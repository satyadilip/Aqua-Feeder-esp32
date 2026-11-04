import json
import base64
import boto3
import struct
import math
from decimal import Decimal
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
telemetry_table = dynamodb.Table('AquaFeeder_Telemetry')
devices_table = dynamodb.Table('AquaFeeder_Devices')
daily_metrics_table = dynamodb.Table('AquaFeeder_DailyMetrics')
settings_table = dynamodb.Table('AquaFeeder_Settings')
tray_checks_table = dynamodb.Table('AquaFeeder_TrayChecks')
commands_table = dynamodb.Table('AquaFeeder_Commands')

iw_client = boto3.client('iotwireless')

DEVEUI_TO_WIRELESS_ID = {
    'e072a1fffef5ba08': '9cd8879c-4265-4ddf-bda1-ab71e80a90a3',
    'e072a1fffef6249c': '503bec00-b0f5-4533-b4e0-9d21fbc28dea',
    'e072a1fffef64134': '144c9bac-2316-4b35-8262-aa297d03805d',
    'e072a1fffef5bac0': 'e27420b7-5d0f-4b60-a033-15fbac63365f',
    'e072a1f6249c0005': '8e499bee-df06-49cb-8ca8-903c0bdf1e3a',
    'e072a1f6249c0001': 'd7feffe3-7eb1-461a-a128-be43271f826f'
}

IST_OFFSET_SEC = 19800  # UTC + 5:30 (Indian Standard Time)

def auto_sync_rtc_if_needed(dev_eui, reported_ts, now_epoch):
    """
    If the device's RTC time is uninitialized (< 1700000000) or drifted by > 300s from IST,
    automatically queue a CMD_SYNC_TIME (0xA3) downlink to synchronize DS3231 RTC to IST.
    """
    try:
        ist_now = now_epoch + IST_OFFSET_SEC
        if reported_ts < 1700000000 or abs(reported_ts - ist_now) > 300:
            w_id = DEVEUI_TO_WIRELESS_ID.get(dev_eui.lower())
            if w_id:
                # 12-byte LoRaDownlinkPayload: 0xA3 + 4B epoch + 7B 0x00
                down_bytes = struct.pack('<BI7s', 0xA3, ist_now, b'\x00' * 7)
                down_b64 = base64.b64encode(down_bytes).decode('ascii')
                iw_client.send_data_to_wireless_device(
                    Id=w_id,
                    TransmitMode=1,
                    PayloadData=down_b64,
                    WirelessMetadata={'LoRaWAN': {'FPort': 1}}
                )
                print(f"[RTC-SYNC] Auto-queued RTC time sync for {dev_eui}: sent IST epoch {ist_now}")
    except Exception as e:
        print(f"[RTC-SYNC] Auto sync error for {dev_eui}: {e}")

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    try:
        payload_b64 = event.get('PayloadData')
        wireless_metadata = event.get('WirelessMetadata', {})
        lorawan_metadata = wireless_metadata.get('LoRaWAN', {})
        dev_eui = lorawan_metadata.get('DevEui', 'UNKNOWN_DEVICE')
        rx_timestamp = lorawan_metadata.get('Timestamp', '')
        
        now_epoch = int(datetime.utcnow().timestamp())
        now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
        
        # Farm operational date in IST (+5:30)
        try:
            dt = datetime.strptime(rx_timestamp, "%Y-%m-%dT%H:%M:%SZ")
            date_str = (dt + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d")
        except:
            date_str = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d")
            
        if not payload_b64:
            print("No payload data found")
            return
            
        payload_bytes = base64.b64decode(payload_b64)
        msg_type = payload_bytes[0] if len(payload_bytes) > 0 else 0
        
        if msg_type == 0x22: # SETTINGS_REPORT (34)
            if len(payload_bytes) >= 13:
                unpacked = struct.unpack('<BIHBBBBH', payload_bytes[:13])
                feed_qty_kg = Decimal(str(round(unpacked[1] / 1000.0, 2)))
                fpe_g = Decimal(str(unpacked[2]))
                shour = Decimal(str(unpacked[3]))
                smin = Decimal(str(unpacked[4]))
                ehour = Decimal(str(unpacked[5]))
                emin = Decimal(str(unpacked[6]))
                rate_gs = Decimal(str(unpacked[7]))

                total_events = int(math.ceil((float(feed_qty_kg) * 1000.0) / float(fpe_g))) if float(fpe_g) > 0 else 250
                motor_time_s = round(float(fpe_g) / float(rate_gs), 2) if float(rate_gs) > 0 else 1.0
                single_event_s = motor_time_s + 6.0  # 3s PRE warmup + motor + 3s POST clearance
                start_mins = int(shour) * 60 + int(smin)
                end_mins = int(ehour) * 60 + int(emin)
                full_window_s = (end_mins - start_mins) * 60
                total_cycle_s = total_events * single_event_s

                # Device RTC is in IST (UTC + 19800)
                ist_epoch = now_epoch + 19800
                sec_since_midnight = ist_epoch % 86400
                cur_mins = sec_since_midnight // 60

                if cur_mins >= end_mins:
                    # After end time: scheduled for tomorrow
                    available_s = full_window_s
                elif cur_mins >= start_mins:
                    # Mid-day active window
                    end_sec_today = end_mins * 60
                    available_s = (end_sec_today - sec_since_midnight) if end_sec_today > sec_since_midnight else full_window_s
                else:
                    # Early morning before start time: scheduled for today
                    available_s = full_window_s

                if total_events > 0 and available_s > total_cycle_s:
                    interval_s = (available_s - total_cycle_s) / float(total_events)
                    interval_min = round(interval_s / 60.0, 1)
                else:
                    interval_min = 2.8
                
                settings_table.put_item(
                    Item={
                        'DeviceId': dev_eui,
                        'DailyTarget_kg': feed_qty_kg,
                        'FeedQuantity_kg': feed_qty_kg,
                        'FeedPerEvent_g': fpe_g,
                        'StartHour': shour,
                        'StartMinute': smin,
                        'EndHour': ehour,
                        'EndMinute': emin,
                        'DischargeRate_gs': rate_gs,
                        'TotalEvents': Decimal(str(total_events)),
                        'IntervalMin': Decimal(str(interval_min)),
                        'MotorTimeSec': Decimal(str(motor_time_s)),
                        'ScheduleValid': True,
                        'LastUpdated': date_str
                    }
                )
                
                # Also synchronize live devices table immediately
                try:
                    devices_table.update_item(
                        Key={'DeviceId': dev_eui},
                        UpdateExpression="SET DailyTarget_kg=:dq, FeedQuantity_kg=:q, FeedPerEvent_g=:f, StartHour=:sh, StartMinute=:sm, EndHour=:eh, EndMinute=:em, DischargeRate_gs=:r, TotalEvents=:te, IntervalMin=:im, ScheduleValid=:sv",
                        ExpressionAttributeValues={
                            ':dq': feed_qty_kg,
                            ':q': feed_qty_kg,
                            ':f': fpe_g,
                            ':sh': shour,
                            ':sm': smin,
                            ':eh': ehour,
                            ':em': emin,
                            ':r': rate_gs,
                            ':te': Decimal(str(total_events)),
                            ':im': Decimal(str(interval_min)),
                            ':sv': True
                        }
                    )
                except Exception as sync_err:
                    print("Devices table sync error:", sync_err)

                print(f"Stored valid Settings from SETTINGS_REPORT for {dev_eui}: {feed_qty_kg}kg, {shour}:{smin} to {ehour}:{emin}, interval {interval_min}m")
            else:
                print(f"Payload too small for SETTINGS_REPORT: {len(payload_bytes)}")
                
        elif len(payload_bytes) >= 15:
            unpacked = struct.unpack('<BIHHHBBBB', payload_bytes[:15])
            timestamp = unpacked[1]
            voltage = unpacked[2]
            current = unpacked[3]
            feed_disp = unpacked[4]
            cur_ev = unpacked[5]
            tot_ev = unpacked[6]
            status_flags = unpacked[7]
            reserved_byte = unpacked[8] if len(unpacked) > 8 else 0
            if reserved_byte > 0:
                fw_maj = reserved_byte >> 4
                fw_min = reserved_byte & 0x0F
                fw_version = f"v{fw_maj}.{fw_min}"
            else:
                fw_version = "v1.0"
            
            cur_ev_int = int(cur_ev)
            tot_ev_int = int(tot_ev)
            
            # 1. Fetch existing device record and user-configured settings FIRST
            existing_dev = {}
            try:
                d_res = devices_table.get_item(Key={'DeviceId': dev_eui})
                existing_dev = d_res.get('Item', {})
            except Exception:
                pass

            prev_status = str(existing_dev.get('Status', 'IDLE')).upper()
            prev_avail = bool(existing_dev.get('FeedAvailable', True))
            prev_flags = int(existing_dev.get('StatusFlags', 0))
            prev_ev = int(existing_dev.get('CurrentEvent', 0))

            saved_qty = existing_dev.get('DailyTarget_kg', existing_dev.get('FeedQuantity_kg', Decimal('15.0')))
            saved_fpe = Decimal('100')
            saved_shour = Decimal('6')
            saved_smin = Decimal('0')
            saved_ehour = Decimal('18')
            saved_emin = Decimal('0')
            saved_rate = Decimal('100')
            saved_interval = Decimal('2.9')
            try:
                s_res = settings_table.get_item(Key={'DeviceId': dev_eui})
                s_item = s_res.get('Item')
                if s_item:
                    saved_qty = s_item.get('DailyTarget_kg', s_item.get('FeedQuantity_kg', saved_qty))
                    saved_fpe = s_item.get('FeedPerEvent_g', saved_fpe)
                    saved_shour = s_item.get('StartHour', saved_shour)
                    saved_smin = s_item.get('StartMinute', saved_smin)
                    saved_ehour = s_item.get('EndHour', saved_ehour)
                    saved_emin = s_item.get('EndMinute', saved_emin)
                    saved_rate = s_item.get('DischargeRate_gs', saved_rate)
                    saved_interval = s_item.get('IntervalMin', saved_interval)
            except Exception:
                pass
            target_kg = Decimal(str(saved_qty))

            # Authoritative FeedPerEvent_g: strictly the active user configuration (NEVER a running average!)
            fpe_g = int(saved_fpe) if int(saved_fpe) > 0 else 100
            total_dispensed_g = int(feed_disp) if int(feed_disp) > 0 else (cur_ev_int * fpe_g)
            dispensed_kg = Decimal(str(round(total_dispensed_g / 1000.0, 2)))

            # 2. Calculate exact physical event grams for this specific pulse
            prev_disp = int(existing_dev.get('LastFeed_g', 0))
            current_disp = int(feed_disp)
            if cur_ev_int > 0:
                if current_disp > prev_disp and 10 <= (current_disp - prev_disp) <= 2000:
                    event_grams = current_disp - prev_disp
                elif current_disp == prev_disp and cur_ev_int == prev_ev and int(existing_dev.get('LastEventGrams', 0)) > 0:
                    event_grams = int(existing_dev.get('LastEventGrams', fpe_g))
                else:
                    event_grams = fpe_g
            else:
                event_grams = 0

            # 3. Store raw telemetry with 15-day TTL and frozen event settings (STORY-007 & STORY-008)
            should_store_telemetry = (cur_ev_int > 0) or (status_flags != prev_flags) or (now_epoch - int(existing_dev.get('LastTelemetryHeartbeat', 0)) >= 3600)
            if should_store_telemetry:
                ttl_epoch = Decimal(str(now_epoch + (15 * 86400))) # 15 days retention
                telemetry_table.put_item(
                    Item={
                        'DeviceId': dev_eui,
                        'Timestamp': Decimal(str(timestamp if timestamp > 1700000000 else now_epoch)),
                        'MsgType': msg_type,
                        'Voltage_mV': Decimal(str(voltage)),
                        'Current_mA': Decimal(str(current)),
                        'FeedDispensed_g': Decimal(str(total_dispensed_g)),
                        'CurrentEvent': cur_ev,
                        'TotalEvents': tot_ev,
                        'StatusFlags': status_flags,
                        'EventGrams': Decimal(str(event_grams)),
                        'FeedPerEvent_g': Decimal(str(fpe_g if cur_ev_int > 0 else saved_fpe)),
                        'Target_kg': target_kg,
                        'TimeToLive': ttl_epoch
                    }
                )
            
            # Auto-check RTC drift & sync
            auto_sync_rtc_if_needed(dev_eui, int(timestamp), now_epoch)
            
            # Handle special message types
            # 1. TRAY_CHECKIN (0x0A = 10)
            if msg_type == 0x0A:
                try:
                    tray_checks_table.put_item(
                        Item={
                            'DeviceId': dev_eui,
                            'Timestamp': Decimal(str(now_epoch)),
                            'CheckEpoch': Decimal(str(now_epoch)),
                            'EventTime': now_iso,
                            'CurrentEvent': cur_ev,
                            'TotalEvents': tot_ev,
                            'DispensedKg': dispensed_kg,
                            'FeedDispensed_g': Decimal(str(total_dispensed_g)),
                            'Voltage_mV': Decimal(str(voltage)),
                            'Battery_V': Decimal(str(round(voltage / 1000.0, 2))),
                            'Status': 'CONFIRMED',
                            'Remarks': 'Manual Tray Check logged from Feeder'
                        }
                    )
                    print(f"Recorded TRAY_CHECKIN event for {dev_eui} at {now_iso}")
                except Exception as t_err:
                    print("Tray check recording error:", t_err)

            # 2. DIAG_CONFIRMATION (0x24 = 36)
            elif msg_type == 0x24:
                motor_num = int(cur_ev) # 1=Loader, 2=Spreader
                motor_name = 'Loader' if motor_num == 1 else 'Spreader'
                duration_sec = int(tot_ev)
                res_str = 'PASSED' if int(status_flags) == 1 else 'FAILED'
                test_info = {
                    'motorNum': motor_num,
                    'motorName': motor_name,
                    'durationSec': duration_sec,
                    'currentMA': int(current),
                    'result': res_str,
                    'confirmedAt': now_iso,
                    'confirmedEpoch': int(now_epoch)
                }
                print(f"Recorded DIAG_CONFIRMATION for {dev_eui}: {test_info}")

            # Schedule time calculation in IST (+5:30)
            now_ist_dt = datetime.utcnow() + timedelta(hours=5, minutes=30)
            now_ist_mins = now_ist_dt.hour * 60 + now_ist_dt.minute
            start_mins = int(saved_shour) * 60 + int(saved_smin)
            end_mins = int(saved_ehour) * 60 + int(saved_emin)
            is_inside_schedule = (now_ist_mins >= start_mins and now_ist_mins < end_mins)

            # Flag decoding
            flag_proximity = (status_flags & 0x01) != 0
            flag_overcurrent = (status_flags & 0x02) != 0
            flag_empty = (status_flags & 0x08) != 0
            flag_paused = (status_flags & 0x10) != 0 or (msg_type in [4, 15])

            # Feed lifecycle identification
            is_feed_advance = (cur_ev_int > prev_ev)
            is_feed_start   = (msg_type == 0x03)
            is_feed_finish  = (msg_type == 0x02)
            is_feed_pause   = (msg_type == 0x04 or flag_paused or flag_proximity)
            is_feed_resume  = (msg_type == 0x05)
            is_feed_stop    = (msg_type == 0x06)
            is_tray_check   = (msg_type == 0x0A)
            
            # Events that update the timeline anchor / event timestamp
            is_event_report = (msg_type in [0x02, 0x03, 0x04, 0x05, 0x06, 0x0A] or is_feed_advance)

            # Check if existing device record has a feed event from today (IST)
            existing_last_ev_str = str(existing_dev.get('LastEventTime', '')).strip()
            existing_is_today = False
            if existing_last_ev_str:
                try:
                    clean_ts = existing_last_ev_str.replace('Z', '').replace('T', ' ')
                    dt_val = datetime.strptime(clean_ts[:19], "%Y-%m-%d %H:%M:%S")
                    dt_ist = dt_val + timedelta(hours=5, minutes=30)
                    if dt_ist.date() == now_ist_dt.date():
                        existing_is_today = True
                except Exception:
                    pass

            # State transition engine:
            if is_feed_finish or (cur_ev_int >= tot_ev_int and tot_ev_int > 0 and is_inside_schedule):
                status_str = 'COMPLETED'
                feed_available = True
                effective_flags = status_flags
            elif is_feed_stop:
                status_str = 'STANDBY'
                feed_available = True
                effective_flags = status_flags
            elif flag_overcurrent:
                status_str = 'MOTOR OVERCURRENT'
                feed_available = False
                effective_flags = status_flags
            elif is_feed_pause:
                status_str = 'PAUSED'
                feed_available = False
                effective_flags = status_flags if status_flags > 0 else 24
            elif flag_empty:
                status_str = 'FEED EMPTY'
                feed_available = False
                effective_flags = status_flags if status_flags > 0 else 8
            elif is_feed_start:
                feed_available = True
                status_str = 'FEEDING'
                effective_flags = status_flags & ~0x10
            elif not is_inside_schedule:
                status_str = 'STANDBY'
                feed_available = True
                effective_flags = status_flags
            elif cur_ev_int > 0 and cur_ev_int < tot_ev_int and is_inside_schedule:
                # Live dispense underway or in wait gap
                status_str = 'FEEDING'
                feed_available = True
                effective_flags = status_flags
            elif msg_type == 0x01: # PERIODIC_HEARTBEAT
                if prev_status == 'FEEDING' and is_inside_schedule:
                    status_str = 'FEEDING'
                elif prev_status in ['COMPLETED', 'FEED EMPTY', 'PAUSED'] and existing_is_today:
                    status_str = prev_status
                else:
                    status_str = 'STANDBY' if (not is_inside_schedule or cur_ev_int >= tot_ev_int) else 'SCHEDULED'
                feed_available = True
                effective_flags = status_flags
            else:
                status_str = existing_dev.get('Status', 'STANDBY')
                if status_str not in ['FEEDING', 'PAUSED', 'FEED EMPTY', 'COMPLETED', 'STANDBY', 'SCHEDULED']:
                    status_str = 'STANDBY'
                feed_available = True
                effective_flags = status_flags

            # Update LastEventTime anchor on genuine feed actions or advances
            if is_event_report or (cur_ev_int > 0 and existing_dev.get('CurrentEvent', 0) == 0):
                last_event_time = now_iso
            else:
                last_event_time = existing_dev.get('LastEventTime', now_iso)

            # Decoupled Today Completed State vs Scheduled State (STORY-009 & STORY-010)
            prev_today_date = str(existing_dev.get('TodayDate', ''))
            prev_today_ev = int(existing_dev.get('TodayEventsCompleted', 0))
            prev_today_kg = Decimal(str(existing_dev.get('TodayFeedDispensed_kg', '0')))
            prev_today_tot = int(existing_dev.get('TodayTotalEvents', tot_ev_int))
            prev_today_status = str(existing_dev.get('TodayStatus', 'STANDBY'))

            is_same_day = (prev_today_date == date_str)

            if cur_ev_int > 0:
                # Live feeding is advancing - use hardware cumulative grams if reported
                live_cur_ev = Decimal(str(cur_ev_int))
                live_disp_kg = Decimal(str(round(int(feed_disp) / 1000.0, 2))) if int(feed_disp) > 0 else Decimal(str(round((cur_ev_int * fpe_g) / 1000.0, 2)))
                today_date = date_str
                today_completed_ev = Decimal(str(cur_ev_int))
                today_dispensed_kg = live_disp_kg
                today_total_ev = Decimal(str(tot_ev_int))
                today_status = status_str
            elif is_same_day and prev_today_ev > 0:
                # After feed completion or mid-day stop on the same calendar day, heartbeats report cur_ev == 0
                # Retain today's completed numbers until midnight!
                today_date = date_str
                today_completed_ev = Decimal(str(prev_today_ev))
                today_dispensed_kg = prev_today_kg
                today_total_ev = Decimal(str(prev_today_tot))
                is_all_done = (prev_today_ev >= prev_today_tot or float(prev_today_kg) >= float(target_kg))
                today_status = 'COMPLETED' if is_all_done else ('SCHEDULE ENDED' if now_ist_mins >= end_mins else prev_today_status)
                
                live_cur_ev = today_completed_ev
                live_disp_kg = today_dispensed_kg
                if is_all_done:
                    status_str = 'COMPLETED'
                elif now_ist_mins >= end_mins:
                    status_str = 'SCHEDULE ENDED'
                elif prev_status in ['STANDBY', 'STOPPED', 'PAUSED']:
                    status_str = prev_status
                else:
                    status_str = 'FEEDING' if is_inside_schedule else 'STANDBY'
            else:
                # New calendar day before feed starts (00:00 to 06:00 IST)
                live_cur_ev = Decimal('0')
                live_disp_kg = Decimal('0')
                today_date = date_str
                today_completed_ev = Decimal('0')
                today_dispensed_kg = Decimal('0')
                today_total_ev = Decimal(str(tot_ev_int))
                today_status = 'STANDBY'

            # Dynamic interval calculation matching firmware FeedEngine::calcSchedule / recalcDynamic
            shour_val = int(saved_shour)
            smin_val = int(saved_smin)
            ehour_val = int(saved_ehour)
            emin_val = int(saved_emin)
            
            sec_since_midnight = now_ist_dt.hour * 3600 + now_ist_dt.minute * 60 + now_ist_dt.second
            end_sec_today = ehour_val * 3600 + emin_val * 60
            start_sec_today = shour_val * 3600 + smin_val * 60
            
            rate_val = float(saved_rate) if float(saved_rate) > 0.1 else 100.0
            motor_time_s = round(float(fpe_g) / rate_val, 2)
            single_event_s = 3.0 + motor_time_s + 3.0
            
            # Authoritative Deductive Schedule Calculation (STORY-017 & Senior Test Audit)
            fpe_val = float(saved_fpe) if float(saved_fpe) > 0 else 100.0
            target_val = float(target_kg) if float(target_kg) > 0 else 15.0
            
            if int(live_cur_ev) > 0 and float(live_disp_kg) > 0:
                rem_kg = max(0.0, target_val - float(live_disp_kg))
                remaining_events = int(math.ceil((rem_kg * 1000.0) / fpe_val)) if rem_kg > 0 else 0
                tot_ev_calc = int(live_cur_ev) + remaining_events
            else:
                tot_ev_calc = int(math.ceil((target_val * 1000.0) / fpe_val))
                remaining_events = tot_ev_calc

            if status_str == 'COMPLETED' or now_ist_mins >= end_mins or float(live_disp_kg) >= target_val or (tot_ev_calc > 0 and int(live_cur_ev) >= tot_ev_calc):
                remaining_events = 0

            tot_ev_int = tot_ev_calc
            tot_ev = tot_ev_calc
            remaining_time_s = max(0, end_sec_today - sec_since_midnight)
            rem_events_calc = max(1, remaining_events)
            rem_duration_s = rem_events_calc * single_event_s
            
            if remaining_time_s > rem_duration_s and remaining_events > 0:
                dynamic_gap_sec = max(5, int((remaining_time_s - rem_duration_s) / rem_events_calc))
            else:
                dynamic_gap_sec = int(float(saved_interval) * 60.0) if float(saved_interval) > 0 else 60
            
            dynamic_interval_min = round(dynamic_gap_sec / 60.0, 1)

            # Synchronous Next Feed calculation
            s_ampm = "PM" if shour_val >= 12 else "AM"
            s_disph = 12 if shour_val % 12 == 0 else shour_val % 12
            s_time_fmt = f"{s_disph:02d}:{smin_val:02d} {s_ampm}"
            
            if status_str == 'FEEDING':
                next_ist_dt = now_ist_dt + timedelta(seconds=dynamic_gap_sec)
                next_feed_str = next_ist_dt.strftime("%I:%M %p")
                next_feed_sub = f"Every {dynamic_gap_sec}s ({dynamic_interval_min}m)"
            elif status_str == 'COMPLETED' or now_ist_mins >= end_mins:
                next_feed_str = s_time_fmt
                next_feed_sub = f"Tomorrow at {s_time_fmt}"
            elif now_ist_mins < start_mins:
                next_feed_str = s_time_fmt
                next_feed_sub = f"Starts today at {s_time_fmt}"
            elif status_str == 'PAUSED':
                next_feed_str = "--"
                next_feed_sub = "Feed Paused"
            elif status_str == 'FEED EMPTY':
                next_feed_str = "--"
                next_feed_sub = "Refill Required"
            else:
                next_feed_str = s_time_fmt
                next_feed_sub = f"Starts at {s_time_fmt}" if now_ist_mins < end_mins else f"Tomorrow at {s_time_fmt}"

            dev_item = {
                'DeviceId': dev_eui,
                'LastSeen': Decimal(str(timestamp)),
                'LastSeenEpoch': Decimal(str(now_epoch)),
                'LastEventTime': last_event_time,
                'CycleStartEpoch': Decimal(str(timestamp if (timestamp > 1700000000 and msg_type == 0x03) else existing_dev.get('CycleStartEpoch', now_epoch))),
                'FeedStartTime': now_iso if msg_type == 0x03 else existing_dev.get('FeedStartTime', now_iso),
                'LastVoltage_mV': Decimal(str(voltage)),
                'LastCurrent_mA': Decimal(str(current)),
                'LastFeed_g': Decimal(str(feed_disp)),
                'CurrentEvent': live_cur_ev,
                'TotalEvents': Decimal(str(tot_ev_int)),
                'TotalEventsRemaining': Decimal(str(remaining_events)),
                'GapIntervalSec': Decimal(str(dynamic_gap_sec)),
                'IntervalMin': Decimal(str(dynamic_interval_min)),
                'NextFeed': next_feed_str,
                'NextFeedSub': next_feed_sub,
                'StatusFlags': effective_flags,
                'DispensedFeed_kg': live_disp_kg,
                'DailyTarget_kg': target_kg,
                'FeedQuantity_kg': target_kg,
                'FeedPerEvent_g': Decimal(str(fpe_g)),
                'DischargeRate_gs': Decimal(str(int(rate_val))),
                'StartHour': Decimal(str(shour_val)),
                'StartMinute': Decimal(str(smin_val)),
                'EndHour': Decimal(str(ehour_val)),
                'EndMinute': Decimal(str(emin_val)),
                'FeedAvailable': feed_available,
                'Status': status_str,
                'LastEventGrams': Decimal(str(event_grams)),
                'FeedActive': False if status_str in ['STANDBY', 'COMPLETED', 'PAUSED'] else existing_dev.get('FeedActive', True),
                'TodayDate': today_date,
                'TodayEventsCompleted': today_completed_ev,
                'TodayFeedDispensed_kg': today_dispensed_kg,
                'TodayTotalEvents': today_total_ev,
                'TodayStatus': today_status,
                'LastTelemetryHeartbeat': Decimal(str(now_epoch if should_store_telemetry else int(existing_dev.get('LastTelemetryHeartbeat', 0)))),
                'FirmwareVersion': fw_version,
                'FirmwareName': 'AquaFeeder Firmware'
            }
            if msg_type == 0x0A:
                dev_item['LastTrayCheck'] = now_iso
                dev_item['LastTrayCheckEpoch'] = Decimal(str(now_epoch))
            elif msg_type == 0x24:
                dev_item['LastTestResult'] = {
                    'motorNum': int(cur_ev),
                    'motorName': 'Loader' if int(cur_ev) == 1 else 'Spreader',
                    'durationSec': int(tot_ev),
                    'currentMA': int(current),
                    'result': 'PASSED' if int(status_flags) == 1 else 'FAILED',
                    'confirmedAt': now_iso
                }
            elif 'LastTrayCheck' in existing_dev:
                dev_item['LastTrayCheck'] = existing_dev['LastTrayCheck']
                dev_item['LastTrayCheckEpoch'] = existing_dev.get('LastTrayCheckEpoch', Decimal(str(now_epoch)))
            if 'LastTestResult' in existing_dev and msg_type != 0x24:
                dev_item['LastTestResult'] = existing_dev['LastTestResult']

            if dev_eui == 'e072a1fffef6249c':
                dev_item['DeviceName'] = 'aquaCON Feeder 01 (Live AF_9C2472E0)'
                dev_item['PondId'] = 'P-01'
            elif dev_eui == 'e072a1fffef5ba08':
                dev_item['DeviceName'] = 'aquaCON Feeder 02'
                dev_item['PondId'] = 'P-01'
            elif dev_eui == 'e072a1fffef64134':
                dev_item['DeviceName'] = 'aquaCON Feeder 03 (Live AF_344172E0)'
                dev_item['PondId'] = 'P-02'
            else:
                dev_item['DeviceName'] = 'aquaCON Feeder ' + dev_eui[-4:]
                dev_item['PondId'] = 'P-01'

            devices_table.put_item(Item=dev_item)
            
            # Routine telemetry uplinks do NOT overwrite user configuration in AquaFeeder_Settings (BUG-C04 FIX)
            # AquaFeeder_Settings is the source of truth set by user POST /api/settings or SETTINGS_REPORT (0x22).
            
            # Record daily metrics whenever feeding has occurred or completed today (STORY-008)
            if int(today_completed_ev) > 0:
                daily_metrics_table.put_item(
                    Item={
                        'DeviceId': dev_eui,
                        'Date': today_date,
                        'DailyFeed_g': Decimal(str(int(float(today_dispensed_kg) * 1000.0))),
                        'DailyFeed_kg': today_dispensed_kg,
                        'TotalCycles': today_completed_ev,
                        'Target_kg': target_kg,
                        'TargetEvents': today_total_ev,
                        'Status': today_status,
                        'LastUpdated': now_iso
                    }
                )
            print(f"Stored telemetry for {dev_eui}: {live_disp_kg}kg ({cur_ev_int}/{tot_ev}) | Status: {status_str} | FeedAvailable: {feed_available}")
        else:
            print(f"Payload too small: {len(payload_bytes)} bytes")
    except Exception as e:
        print(f"Error processing payload: {e}")
        raise e

import json
import base64
import boto3
import struct
from decimal import Decimal
from datetime import datetime

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
        
        try:
            dt = datetime.strptime(rx_timestamp, "%Y-%m-%dT%H:%M:%SZ")
            date_str = dt.strftime("%Y-%m-%d")
        except:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            
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

                total_events = int((float(feed_qty_kg) * 1000.0) / float(fpe_g)) if float(fpe_g) > 0 else 250
                motor_time_s = round(float(fpe_g) / float(rate_gs), 2) if float(rate_gs) > 0 else 1.0
                single_event_s = motor_time_s + 6.0  # 3s PRE warmup + motor + 3s POST clearance
                start_mins = int(shour) * 60 + int(smin)
                end_mins = int(ehour) * 60 + int(emin)
                feed_window_s = (end_mins - start_mins) * 60
                total_cycle_s = total_events * single_event_s
                interval_min = round((feed_window_s - total_cycle_s) / (total_events * 60.0), 1) if (total_events > 0 and feed_window_s > total_cycle_s) else 2.8
                
                settings_table.put_item(
                    Item={
                        'DeviceId': dev_eui,
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
                print(f"Stored valid Settings from SETTINGS_REPORT for {dev_eui}: {feed_qty_kg}kg, {shour}:{smin} to {ehour}:{emin}")
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
            
            cur_ev_int = int(cur_ev)
            tot_ev_int = int(tot_ev)
            fpe_g = 100
            total_dispensed_g = cur_ev_int * fpe_g
            dispensed_kg = Decimal(str(round(total_dispensed_g / 1000.0, 2)))
            target_kg = Decimal(str(round((tot_ev_int * fpe_g) / 1000.0, 1)))
            
            # Store raw telemetry
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
                    'StatusFlags': status_flags
                }
            )
            
            # Auto-check RTC drift & sync
            auto_sync_rtc_if_needed(dev_eui, int(timestamp), now_epoch)
            
            # Fetch existing device record
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

            saved_qty = target_kg
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
                    saved_qty = s_item.get('FeedQuantity_kg', saved_qty)
                    saved_fpe = s_item.get('FeedPerEvent_g', saved_fpe)
                    saved_shour = s_item.get('StartHour', saved_shour)
                    saved_smin = s_item.get('StartMinute', saved_smin)
                    saved_ehour = s_item.get('EndHour', saved_ehour)
                    saved_emin = s_item.get('EndMinute', saved_emin)
                    saved_rate = s_item.get('DischargeRate_gs', saved_rate)
                    saved_interval = s_item.get('IntervalMin', saved_interval)
            except Exception:
                pass
            
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

            # Schedule time calculation
            now_ist_mins = (datetime.utcnow().hour * 60 + datetime.utcnow().minute + 330) % 1440
            start_mins = int(saved_shour) * 60 + int(saved_smin)
            end_mins = int(saved_ehour) * 60 + int(saved_emin)
            is_inside_schedule = (now_ist_mins >= start_mins and now_ist_mins < end_mins)

            # Flag decoding
            flag_proximity = (status_flags & 0x01) != 0
            flag_empty = (status_flags & 0x08) != 0
            flag_paused = (status_flags & 0x10) != 0 or (msg_type in [4, 15])

            # State transition engine:
            if cur_ev_int > prev_ev:
                # Cycle has advanced! Device is actively feeding.
                feed_available = True
                status_str = 'FEEDING'
                effective_flags = status_flags & ~0x10
            elif flag_paused or flag_proximity:
                status_str = 'PAUSED'
                feed_available = False
                effective_flags = status_flags if status_flags > 0 else 24
            elif flag_empty:
                status_str = 'FEED EMPTY'
                feed_available = False
                effective_flags = status_flags if status_flags > 0 else 8
            elif cur_ev_int >= tot_ev_int and tot_ev_int > 0:
                status_str = 'COMPLETED'
                feed_available = True
                effective_flags = status_flags
            elif not is_inside_schedule:
                status_str = 'STANDBY'
                feed_available = True
                effective_flags = status_flags
            elif cur_ev_int > 0:
                status_str = 'FEEDING'
                feed_available = True
                effective_flags = status_flags
            else:
                status_str = 'SCHEDULED'
                feed_available = True
                effective_flags = status_flags

            dev_item = {
                'DeviceId': dev_eui,
                'LastSeen': Decimal(str(timestamp)),
                'LastSeenEpoch': Decimal(str(now_epoch)),
                'LastEventTime': now_iso,
                'LastVoltage_mV': Decimal(str(voltage)),
                'LastCurrent_mA': Decimal(str(current)),
                'LastFeed_g': Decimal(str(feed_disp)),
                'CurrentEvent': cur_ev,
                'TotalEvents': tot_ev,
                'StatusFlags': effective_flags,
                'DispensedFeed_kg': dispensed_kg,
                'FeedQuantity_kg': saved_qty,
                'FeedPerEvent_g': saved_fpe,
                'DischargeRate_gs': saved_rate,
                'StartHour': saved_shour,
                'StartMinute': saved_smin,
                'EndHour': saved_ehour,
                'EndMinute': saved_emin,
                'IntervalMin': saved_interval,
                'FeedAvailable': feed_available,
                'Status': status_str
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
            
            daily_metrics_table.put_item(
                Item={
                    'DeviceId': dev_eui,
                    'Date': date_str,
                    'DailyFeed_g': Decimal(str(total_dispensed_g)),
                    'DailyFeed_kg': dispensed_kg,
                    'TotalCycles': Decimal(str(cur_ev)),
                    'Target_kg': target_kg
                }
            )
            print(f"Stored telemetry for {dev_eui}: {dispensed_kg}kg ({cur_ev}/{tot_ev}) | Status: {status_str} | FeedAvailable: {feed_available}")
        else:
            print(f"Payload too small: {len(payload_bytes)} bytes")
    except Exception as e:
        print(f"Error processing payload: {e}")
        raise e

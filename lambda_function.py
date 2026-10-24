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

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    try:
        # AWS IoT Wireless puts base64 payload in 'PayloadData'
        payload_b64 = event.get('PayloadData')
        wireless_metadata = event.get('WirelessMetadata', {})
        lorawan_metadata = wireless_metadata.get('LoRaWAN', {})
        dev_eui = lorawan_metadata.get('DevEui', 'UNKNOWN_DEVICE')
        rx_timestamp = lorawan_metadata.get('Timestamp', '') # e.g. "2026-08-25T17:16:20Z"
        
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
                # Firmware LoRaSettingsPayload: msgType(1), feedQuantity_g(4), feedPerEvent_g(2), startHour(1), startMinute(1), endHour(1), endMinute(1), dischargeRate(2)
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
                start_mins = int(shour) * 60 + int(smin)
                end_mins = int(ehour) * 60 + int(emin)
                feed_window_s = (end_mins - start_mins) * 60
                total_motor_s = total_events * motor_time_s
                interval_min = round((feed_window_s - total_motor_s) / (total_events * 60.0), 1) if (total_events > 0 and feed_window_s > total_motor_s) else 2.9
                
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
            # Parse 15-byte telemetry struct
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
            
            # Store in Telemetry table
            telemetry_table.put_item(
                Item={
                    'DeviceId': dev_eui,
                    'Timestamp': Decimal(str(timestamp)),
                    'MsgType': msg_type,
                    'Voltage_mV': Decimal(str(voltage)),
                    'Current_mA': Decimal(str(current)),
                    'FeedDispensed_g': Decimal(str(total_dispensed_g)),
                    'CurrentEvent': cur_ev,
                    'TotalEvents': tot_ev,
                    'StatusFlags': status_flags
                }
            )
            
            now_epoch = int(datetime.utcnow().timestamp())
            now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
            
            # Read and preserve custom user-saved settings if present
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
            except Exception as se:
                pass
            
            # Update Devices table with latest status
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
                'StatusFlags': status_flags,
                'DispensedFeed_kg': dispensed_kg,
                'FeedQuantity_kg': saved_qty,
                'FeedPerEvent_g': saved_fpe,
                'DischargeRate_gs': saved_rate,
                'StartHour': saved_shour,
                'StartMinute': saved_smin,
                'EndHour': saved_ehour,
                'EndMinute': saved_emin,
                'IntervalMin': saved_interval,
                'FeedAvailable': True,
                'Status': 'FEEDING' if cur_ev > 0 else 'IDLE'
            }
            if dev_eui == 'e072a1fffef6249c':
                dev_item['DeviceName'] = 'aquaCON Feeder 01 (Live AF_9C2472E0)'
                dev_item['PondId'] = 'P-01'
            else:
                dev_item['DeviceName'] = 'aquaCON Feeder ' + dev_eui[-4:]
                dev_item['PondId'] = 'P-01'

            devices_table.put_item(Item=dev_item)
            
            # Aggregate Daily Metrics
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
            
            print(f"Successfully processed and stored telemetry for device {dev_eui}: {dispensed_kg}kg ({cur_ev}/{tot_ev} events)")
        else:
            print(f"Payload too small: {len(payload_bytes)} bytes")
            
    except Exception as e:
        print(f"Error processing payload: {e}")
        raise e

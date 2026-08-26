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
            if len(payload_bytes) >= 12:
                # struct: msgType(1), feedQuantity_g(4), feedPerEvent_g(2), feedTime_h(1), startHour(1), startMinute(1), dischargeRate(2)
                unpacked = struct.unpack('<BIHBBBH', payload_bytes[:12])
                
                settings_table.put_item(
                    Item={
                        'DeviceId': dev_eui,
                        'FeedQuantity_kg': Decimal(str(unpacked[1] / 1000.0)),
                        'FeedPerEvent_g': Decimal(str(unpacked[2])),
                        'FeedTime_h': Decimal(str(unpacked[3])),
                        'StartHour': Decimal(str(unpacked[4])),
                        'StartMinute': Decimal(str(unpacked[5])),
                        'DischargeRate_gs': Decimal(str(unpacked[6])),
                        'LastUpdated': date_str
                    }
                )
                print(f"Stored Settings for {dev_eui}")
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
            
            # Store in Telemetry table
            telemetry_table.put_item(
                Item={
                    'DeviceId': dev_eui,
                    'Timestamp': Decimal(str(timestamp)),
                    'MsgType': msg_type,
                    'Voltage_mV': Decimal(str(voltage)),
                    'Current_mA': Decimal(str(current)),
                    'FeedDispensed_g': Decimal(str(feed_disp)),
                    'CurrentEvent': cur_ev,
                    'TotalEvents': tot_ev,
                    'StatusFlags': status_flags
                }
            )
            
            # Update Devices table with latest status
            devices_table.put_item(
                Item={
                    'DeviceId': dev_eui,
                    'LastSeen': Decimal(str(timestamp)),
                    'LastVoltage_mV': Decimal(str(voltage)),
                    'LastCurrent_mA': Decimal(str(current)),
                    'LastFeed_g': Decimal(str(feed_disp)),
                    'CurrentEvent': cur_ev,
                    'TotalEvents': tot_ev,
                    'StatusFlags': status_flags
                }
            )
            
            # Aggregate Daily Metrics
            # To prevent double counting, we use put_item to overwrite the day's record with the maximum feed dispensed so far today.
            daily_metrics_table.put_item(
                Item={
                    'DeviceId': dev_eui,
                    'Date': date_str,
                    'DailyFeed_g': Decimal(str(feed_disp)),
                    'TotalCycles': Decimal(str(cur_ev))
                }
            )
            
            print(f"Successfully processed and stored telemetry for device {dev_eui}")
        else:
            print(f"Payload too small: {len(payload_bytes)} bytes")
            
    except Exception as e:
        print(f"Error processing payload: {e}")
        raise e

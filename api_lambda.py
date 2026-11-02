import json
import base64
import struct
import boto3
from decimal import Decimal
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
devices_table = dynamodb.Table('AquaFeeder_Devices')
telemetry_table = dynamodb.Table('AquaFeeder_Telemetry')
settings_table = dynamodb.Table('AquaFeeder_Settings')
metrics_table = dynamodb.Table('AquaFeeder_DailyMetrics')
users_table = dynamodb.Table('AquaCon_Users')
lora_table = dynamodb.Table('LoRaDeviceTelemetry')
tray_checks_table = dynamodb.Table('AquaFeeder_TrayChecks')
commands_table = dynamodb.Table('AquaFeeder_Commands')

iw_client = boto3.client('iotwireless', region_name='us-east-1')

DEVEUI_TO_WIRELESS_ID = {
    'e072a1fffef5ba08': '9cd8879c-4265-4ddf-bda1-ab71e80a90a3',
    'e072a1fffef6249c': '503bec00-b0f5-4533-b4e0-9d21fbc28dea',
    'e072a1fffef64134': '144c9bac-2316-4b35-8262-aa297d03805d',
    'e072a1fffef5bac0': 'e27420b7-5d0f-4b60-a033-15fbac63365f',
    'e072a1f6249c0005': '8e499bee-df06-49cb-8ca8-903c0bdf1e3a',
    'e072a1f6249c0001': 'd7feffe3-7eb1-461a-a128-be43271f826f'
}

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Requested-With',
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }

def send_lora_downlink(dev_eui, downlink_bytes, fport=1):
    w_id = DEVEUI_TO_WIRELESS_ID.get(str(dev_eui).lower().strip())
    if not w_id:
        return False, f"Device {dev_eui} not registered in Wireless Device mapping"
    try:
        down_b64 = base64.b64encode(downlink_bytes).decode('ascii')
        iw_client.send_data_to_wireless_device(
            Id=w_id,
            TransmitMode=0, # 0 = queue for Class A (delivered on next uplink)
            PayloadData=down_b64,
            WirelessMetadata={'LoRaWAN': {'FPort': fport}}
        )
        return True, f"Downlink queued successfully for {dev_eui} ({w_id})"
    except Exception as err:
        return False, str(err)

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    try:
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        
        # 1. Handle CORS Preflight
        if http_method == 'OPTIONS':
            return build_response(200, {'message': 'CORS OK'})
            
        # Parse JSON body if present
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except:
                body = {}

        query_params = event.get('queryStringParameters') or {}

        # 2. User Authentication (Login)
        if path == '/api/auth/login' and http_method == 'POST':
            phone = str(body.get('phone', '')).strip()
            password = str(body.get('password', '')).strip()
            
            if not phone or not password:
                return build_response(400, {'error': 'Phone and password are required'})
                
            # Default Dummy User Override: 9000420999 / admin
            if phone == '9000420999' and password == 'admin':
                return build_response(200, {
                    'status': 'success',
                    'token': 'session_aquacon_admin_9000420999',
                    'user': {
                        'phone': '9000420999',
                        'name': 'aquaCON Supervisor',
                        'farmName': 'aquaCON Pioneer Aqua Farm',
                        'role': 'Admin'
                    }
                })
                
            # Query DynamoDB table AquaCon_Users
            try:
                user_res = users_table.get_item(Key={'Phone': phone})
                user_item = user_res.get('Item')
                if user_item and user_item.get('Password') == password:
                    return build_response(200, {
                        'status': 'success',
                        'token': f'session_aquacon_{phone}',
                        'user': {
                            'phone': phone,
                            'name': user_item.get('Name', 'aquaCON Operator'),
                            'farmName': user_item.get('FarmName', 'My AquaFarm'),
                            'role': user_item.get('Role', 'Operator')
                        }
                    })
                else:
                    return build_response(401, {'error': 'Invalid mobile number or password'})
            except Exception as e:
                print("DynamoDB User lookup error:", str(e))
                return build_response(401, {'error': 'Invalid credentials'})

        # 3. User Registration (Register Farm)
        elif path == '/api/auth/register' and http_method == 'POST':
            phone = str(body.get('phone', '')).strip()
            password = str(body.get('password', 'admin')).strip()
            name = str(body.get('name', 'Farm Operator')).strip()
            farm_name = str(body.get('farmName', 'aquaCON Smart Pond')).strip()
            ponds = str(body.get('ponds', '4')).strip()
            
            if not phone:
                return build_response(400, {'error': 'Phone number is required for registration'})
                
            # Save user in DynamoDB
            now_iso = datetime.utcnow().isoformat()
            users_table.put_item(
                Item={
                    'Phone': phone,
                    'Password': password,
                    'Name': name,
                    'FarmName': farm_name,
                    'Ponds': ponds,
                    'Role': 'Owner',
                    'CreatedAt': now_iso
                }
            )
            return build_response(201, {
                'status': 'success',
                'message': 'User registered successfully',
                'token': f'session_aquacon_{phone}',
                'user': {
                    'phone': phone,
                    'name': name,
                    'farmName': farm_name,
                    'role': 'Owner'
                }
            })

        # 4. Fetch Devices (Real aquaCON Feeder & SenseCAP Telemetry)
        elif path == '/api/devices' and http_method == 'GET':
            devices = []
            try:
                response = devices_table.scan()
                raw_devices = response.get('Items', [])
                for d in raw_devices:
                    dev_id = str(d.get('DeviceId', ''))
                    cur_ev = float(d.get('CurrentEvent', 0))
                    tot_ev = float(d.get('TotalEvents', 250))
                    fpe = float(d.get('FeedPerEvent_g', 100))
                    target_kg = float(d.get('FeedQuantity_kg', round((tot_ev * fpe) / 1000.0, 1)))
                    dispensed_kg = round((cur_ev * fpe) / 1000.0, 2)
                    
                    d['DispensedFeed_kg'] = dispensed_kg
                    d['FeedQuantity_kg'] = target_kg
                    d['CurrentEvent'] = int(cur_ev)
                    d['TotalEvents'] = int(tot_ev)
                    d['FeedPerEvent_g'] = int(fpe)
                    d['LastSeenEpoch'] = int(d.get('LastSeenEpoch', int(datetime.utcnow().timestamp())))
                    d['LastEventTime'] = str(d.get('LastEventTime', datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")))
                    
                    # Base values from device record (authoritative live telemetry)
                    tot_ev = float(d.get('TotalEvents', 200))
                    cur_ev = float(d.get('CurrentEvent', 0))
                    fpe = float(d.get('FeedPerEvent_g', 100))
                    if fpe == 0 and cur_ev > 0 and float(d.get('LastFeed_g', 0)) > 0:
                        fpe = float(round(float(d.get('LastFeed_g')) / cur_ev))
                    
                    target_kg = float(d.get('FeedQuantity_kg', round((tot_ev * fpe) / 1000.0, 1)))
                    dispensed_kg = float(d.get('DispensedFeed_kg', round((cur_ev * fpe) / 1000.0, 2)))
                    
                    # Merge user-configured settings if present (Authoritative Daily Target)
                    try:
                        s_res = settings_table.get_item(Key={'DeviceId': dev_id})
                        s_item = s_res.get('Item')
                        if s_item:
                            target_kg = float(s_item.get('DailyTarget_kg', s_item.get('FeedQuantity_kg', target_kg)))
                            if cur_ev == 0:
                                fpe = float(s_item.get('FeedPerEvent_g', fpe))
                                tot_ev = float(s_item.get('TotalEvents', tot_ev))
                            elif fpe <= 0:
                                fpe = float(s_item.get('FeedPerEvent_g', 100))
                            d['DailyTarget_kg'] = target_kg
                            d['FeedQuantity_kg'] = target_kg
                            d['StartHour'] = int(s_item.get('StartHour', d.get('StartHour', 6)))
                            d['StartMinute'] = int(s_item.get('StartMinute', d.get('StartMinute', 0)))
                            d['EndHour'] = int(s_item.get('EndHour', d.get('EndHour', 18)))
                            d['EndMinute'] = int(s_item.get('EndMinute', d.get('EndMinute', 0)))
                            d['DischargeRate_gs'] = int(s_item.get('DischargeRate_gs', d.get('DischargeRate_gs', 100)))
                            d['MotorTimeSec'] = float(s_item.get('MotorTimeSec', d.get('MotorTimeSec', 1.0)))
                            d['ScheduleValid'] = True
                    except:
                        pass

                    # Real-time operational schedule status
                    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
                    now_min = now_ist.hour * 60 + now_ist.minute
                    s_hour = int(d.get('StartHour', 6))
                    s_min = int(d.get('StartMinute', 0))
                    e_hour = int(d.get('EndHour', 18))
                    e_min = int(d.get('EndMinute', 0))
                    start_min = s_hour * 60 + s_min
                    end_min = e_hour * 60 + e_min

                    if cur_ev >= tot_ev:
                        calc_status = 'COMPLETED'
                    elif now_min >= end_min or now_min < start_min:
                        calc_status = 'STANDBY'
                    else:
                        calc_status = 'SCHEDULED'

                    now_epoch = int(datetime.utcnow().timestamp())
                    if dev_id in ['e072a1fffef6249c', 'e072a1fffef5ba08', 'e072a1fffef64134']:
                        if dev_id == 'e072a1fffef6249c':
                            feeder_name = 'aquaCON Feeder 01'
                            pond_name = 'P-01'
                        elif dev_id == 'e072a1fffef5ba08':
                            feeder_name = 'aquaCON Feeder 02'
                            pond_name = 'P-01'
                        else:
                            feeder_name = 'aquaCON Feeder 03'
                            pond_name = 'P-02'
                        d['DeviceName'] = feeder_name
                        d['PondId'] = pond_name
                        is_online = (now_epoch - int(d.get('LastSeenEpoch', 0))) < 900
                        d['Connected'] = is_online

                        # Verify if last event was actually from TODAY during today's feeding schedule (IST)
                        last_ev_str = str(d.get('LastEventTime', '')).strip()
                        last_seen_epoch = int(d.get('LastSeenEpoch', 0))
                        is_today_feed_event = False
                        if last_ev_str:
                            try:
                                clean_ts = last_ev_str.replace('Z', '').replace('T', ' ')
                                dt_val = datetime.strptime(clean_ts[:19], "%Y-%m-%d %H:%M:%S")
                                dt_ist = dt_val + timedelta(hours=5, minutes=30)
                                if dt_ist.date() == now_ist.date() and (dt_ist.hour * 60 + dt_ist.minute) >= start_min:
                                    is_today_feed_event = True
                            except:
                                pass

                        if not is_today_feed_event and last_seen_epoch > 0:
                            try:
                                seen_ist = datetime.utcfromtimestamp(last_seen_epoch) + timedelta(hours=5, minutes=30)
                                if seen_ist.date() == now_ist.date() and cur_ev > 0:
                                    is_today_feed_event = True
                            except:
                                pass

                        # If feed for today hasn't started yet (before 6:00 AM or no events today), reset today counters
                        if not is_today_feed_event or now_min < start_min:
                            d['CurrentEvent'] = 0
                            d['DispensedFeed_kg'] = 0.0
                            cur_ev = 0
                            dispensed_kg = 0.0
                        
                        raw_feed_avail = d.get('FeedAvailable', True)
                        raw_status = str(d.get('Status', '')).strip().upper()
                        status_flags = int(d.get('StatusFlags', 0))
                        
                        # Alarm bit decoding: Bit 3 (8) = Feed Empty, Bit 4 (16) = Proximity Pause
                        if (status_flags & 0x08) != 0 or raw_feed_avail is False or raw_status == 'FEED EMPTY':
                            actual_feed_avail = False
                        else:
                            actual_feed_avail = True
                            
                        if not is_online:
                            actual_status = 'NOT CONNECTED'
                        elif (status_flags & 0x10) != 0 or raw_status == 'PAUSED':
                            actual_status = 'PAUSED'
                        elif not actual_feed_avail or raw_status == 'FEED EMPTY':
                            actual_status = 'FEED EMPTY'
                        elif now_min < start_min:
                            actual_status = 'STANDBY'
                        elif is_today_feed_event and (cur_ev >= tot_ev or raw_status == 'COMPLETED'):
                            actual_status = 'COMPLETED'
                        elif is_today_feed_event and (raw_status == 'FEEDING' or cur_ev > 0):
                            actual_status = 'FEEDING'
                        else:
                            actual_status = 'STANDBY' if (now_min >= end_min or now_min < start_min) else 'SCHEDULED' 

                        d['FeedAvailable'] = actual_feed_avail if is_online else False
                        d['Status'] = actual_status
                        d['StatusFlags'] = status_flags

                        # Synchronous dynamic interval calculation matching firmware
                        tot_ev_int = int(tot_ev)
                        cur_ev_int = int(cur_ev)
                        rem_events = max(0, tot_ev_int - cur_ev_int)
                        
                        d_rate = float(d.get('DischargeRate_gs', 100))
                        if d_rate <= 0.1: d_rate = 100.0
                        m_time_s = round(float(fpe) / d_rate, 2)
                        single_ev_s = 3.0 + m_time_s + 3.0
                        
                        sec_since_midnight = now_ist.hour * 3600 + now_ist.minute * 60 + now_ist.second
                        end_sec_today = e_hour * 3600 + e_min * 60
                        rem_time_s = max(0, end_sec_today - sec_since_midnight)
                        rem_calc = max(1, rem_events)
                        rem_dur_s = rem_calc * single_ev_s
                        
                        if rem_time_s > rem_dur_s and rem_events > 0:
                            gap_s = max(5, int((rem_time_s - rem_dur_s) / rem_calc))
                        else:
                            gap_s = int(float(d.get('IntervalMin', 2.9)) * 60.0) if float(d.get('IntervalMin', 2.9)) > 0 else 60
                            
                        dyn_interval_m = round(gap_s / 60.0, 1)
                        
                        d['TotalEvents'] = tot_ev_int
                        d['CurrentEvent'] = cur_ev_int
                        d['TotalEventsRemaining'] = rem_events
                        d['FeedPerEvent_g'] = int(fpe)
                        d['FeedQuantity_kg'] = target_kg
                        d['DailyTarget_kg'] = target_kg
                        d['DispensedFeed_kg'] = round((cur_ev_int * fpe) / 1000.0, 2)
                        d['GapIntervalSec'] = gap_s
                        d['IntervalMin'] = dyn_interval_m
                        d['ScheduleValid'] = True

                        s_ampm = "PM" if s_hour >= 12 else "AM"
                        s_disph = 12 if s_hour % 12 == 0 else s_hour % 12
                        s_time_fmt = f"{s_disph:02d}:{s_min:02d} {s_ampm}"

                        if not is_online:
                            d['NextFeed'] = "--"
                            d['NextFeedSub'] = "Feeder Offline"
                        elif actual_status == 'PAUSED':
                            d['NextFeed'] = "--"
                            d['NextFeedSub'] = "Feed Paused"
                        elif actual_status == 'FEED EMPTY':
                            d['NextFeed'] = "--"
                            d['NextFeedSub'] = "Refill Required"
                        elif actual_status == 'COMPLETED' or now_min >= end_min or (is_today_feed_event and cur_ev_int >= tot_ev_int):
                            d['NextFeed'] = s_time_fmt
                            d['NextFeedSub'] = "Tomorrow morning"
                        elif now_min < start_min:
                            d['NextFeed'] = s_time_fmt
                            d['NextFeedSub'] = f"Starts today at {s_time_fmt}"
                        elif actual_status in ['FEEDING', 'ACTIVE']:
                            last_seen_epoch = int(d.get('LastSeenEpoch', 0))
                            if last_seen_epoch > 0 and (now_epoch - last_seen_epoch) < (gap_s + 30):
                                next_feed_epoch = last_seen_epoch + gap_s
                            else:
                                next_feed_epoch = now_epoch + gap_s
                            
                            next_ist = datetime.utcfromtimestamp(next_feed_epoch) + timedelta(hours=5, minutes=30)
                            d['NextFeed'] = next_ist.strftime("%I:%M %p")
                            d['NextFeedSub'] = f"Interval: {dyn_interval_m}m ({gap_s}s)"
                        else:
                            d['NextFeed'] = s_time_fmt
                            d['NextFeedSub'] = f"Starts at {s_time_fmt}" if now_min < end_min else "Tomorrow morning"

                        devices.append(d)

            except Exception as e:
                print("Devices scan error:", e)
            devices.sort(key=lambda x: str(x.get('LastSeen', 0)), reverse=True)
            return build_response(200, {'devices': devices})

        # 4b. Register New Device
        elif path == '/api/devices' and http_method == 'POST':
            dev_id = str(body.get('deviceId', '')).strip()
            dev_name = str(body.get('deviceName', 'aquaCON Feeder')).strip()
            pond_id = str(body.get('pondId', 'P-01')).strip()
            target_kg = float(body.get('feedQuantity_kg', 15.0))
            
            if not dev_id:
                return build_response(400, {'error': 'DeviceId is required'})
                
            now_ts = int(datetime.utcnow().timestamp())
            item = {
                'DeviceId': dev_id,
                'DeviceName': dev_name,
                'PondId': pond_id,
                'Type': 'aquaCON_Feeder',
                'Status': 'IDLE',
                'FeedActive': False,
                'FeedAvailable': True,
                'LastSeen': now_ts,
                'FeedQuantity_kg': Decimal(str(target_kg)),
                'FeedPerEvent_g': 100,
                'DischargeRate_gs': 100,
                'StartHour': 6,
                'StartMinute': 0,
                'EndHour': 18,
                'EndMinute': 0,
                'CurrentEvent': 0,
                'TotalEvents': int((target_kg * 1000) / 100),
                'DispensedFeed_kg': Decimal('0.0'),
                'NextFeed': '06:00',
                'MotorTimeSec': Decimal('1.0'),
                'IntervalMin': Decimal('4.7'),
                'ScheduleValid': True
            }
            devices_table.put_item(Item=item)
            return build_response(201, {'status': 'success', 'message': f'Device {dev_id} added successfully', 'device': item})

        # 5. Device Remote Commands (START, STOP, TEST_LOADER, TEST_DISPENSER, SYNC_RTC)
        elif path.startswith('/api/command/') and http_method == 'POST':
            device_id = path.split('/')[-1]
            cmd = str(body.get('command', '')).upper().strip()
            now_ts = int(datetime.utcnow().timestamp())
            
            print(f"Executing command '{cmd}' for device '{device_id}'")
            
            if cmd in ['START', 'FEED']:
                # Real LoRaWAN Downlink: CMD_START_FEED (0xA4)
                downlink_bytes = struct.pack('<B11s', 0xA4, b'\x00' * 11)
                dl_success, dl_msg = send_lora_downlink(device_id, downlink_bytes, fport=1)
                print(f"[DOWNLINK] Queued CMD_START_FEED for {device_id}: {dl_success} ({dl_msg})")

                # User pressed start feed: counted as ONE EVENT DONE in the entire feed cycle
                cur_ev = int(body.get('currentEvent', 0))
                disp_kg = Decimal(str(body.get('dispensedKg', '0.0')))
                fpe_g = int(body.get('feedGrams', 100))
                
                if cur_ev == 0:
                    item_res = devices_table.get_item(Key={'DeviceId': device_id})
                    existing = item_res.get('Item', {})
                    cur_ev = int(existing.get('CurrentEvent', 0)) + 1
                    tot_ev = int(existing.get('TotalEvents', 235))
                    fpe_g = int(existing.get('FeedPerEvent_g', 100))
                    disp_kg = Decimal(str(existing.get('DispensedFeed_kg', 0))) + Decimal(str(fpe_g / 1000.0))

                devices_table.update_item(
                    Key={'DeviceId': device_id},
                    UpdateExpression='SET #st = :st, CurrentEvent = :ce, DispensedFeed_kg = :df, LastFeed_g = :lf, LastSeen = :ls, LastEventTime = :lt, FeedAvailable = :fa',
                    ExpressionAttributeNames={'#st': 'Status'},
                    ExpressionAttributeValues={
                        ':st': 'FEEDING',
                        ':ce': cur_ev,
                        ':df': disp_kg,
                        ':lf': fpe_g,
                        ':ls': now_ts,
                        ':lt': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ'),
                        ':fa': True
                    }
                )
                return build_response(200, {
                    'status': 'success',
                    'message': f'Feed event #{cur_ev} executed (+{fpe_g}g counted in cycle)',
                    'currentEvent': cur_ev,
                    'dispensedKg': float(disp_kg)
                })

            elif cmd in ['TEST_LOADER', 'TEST_R1']:
                # Real LoRaWAN Downlink: CMD_TEST_MOTOR (0xA2), motorNum=1, durationSec=2
                downlink_bytes = struct.pack('<BBHHBBBB2s', 0xA2, 0, 0, 0, 0, 1, 0, 2, b'\x00\x00')
                success, msg = send_lora_downlink(device_id, downlink_bytes, fport=1)
                
                cmd_id = f"cmd_loader_{now_ts}"
                commands_table.put_item(Item={
                    'DeviceId': device_id,
                    'CommandId': cmd_id,
                    'Command': 'TEST_LOADER',
                    'MotorNum': 1,
                    'DurationSec': 2,
                    'Status': 'QUEUED',
                    'DownlinkQueued': success,
                    'DownlinkMessage': msg,
                    'CreatedAt': now_ts,
                    'Description': 'Augur Loader (Relay 1) 2s Test'
                })
                
                return build_response(200, {
                    'status': 'queued',
                    'commandId': cmd_id,
                    'motor': 'LOADER',
                    'motorNum': 1,
                    'durationSec': 2,
                    'downlinkQueued': success,
                    'message': 'Loader augur (Relay 1) test queued. Feeder will run motor for 2s and measure real current on next transmission.'
                })

            elif cmd in ['TEST_DISPENSER', 'TEST_R2']:
                # Real LoRaWAN Downlink: CMD_TEST_MOTOR (0xA2), motorNum=2, durationSec=2
                downlink_bytes = struct.pack('<BBHHBBBB2s', 0xA2, 0, 0, 0, 0, 2, 0, 2, b'\x00\x00')
                success, msg = send_lora_downlink(device_id, downlink_bytes, fport=1)
                
                cmd_id = f"cmd_dispenser_{now_ts}"
                commands_table.put_item(Item={
                    'DeviceId': device_id,
                    'CommandId': cmd_id,
                    'Command': 'TEST_DISPENSER',
                    'MotorNum': 2,
                    'DurationSec': 2,
                    'Status': 'QUEUED',
                    'DownlinkQueued': success,
                    'DownlinkMessage': msg,
                    'CreatedAt': now_ts,
                    'Description': 'Dispenser Spreader (Relay 2) 2s Test'
                })
                
                return build_response(200, {
                    'status': 'queued',
                    'commandId': cmd_id,
                    'motor': 'DISPENSER',
                    'motorNum': 2,
                    'durationSec': 2,
                    'downlinkQueued': success,
                    'message': 'Dispenser thrower (Relay 2) test queued. Feeder will run motor for 2s and measure real current on next transmission.'
                })

            elif cmd in ['SYNC_RTC', 'SYNC_TIME']:
                # Real LoRaWAN Downlink: CMD_SYNC_TIME (0xA3) with Indian Standard Time (IST = UTC + 5:30) epoch
                ist_epoch = now_ts + 19800
                downlink_bytes = struct.pack('<BI7s', 0xA3, ist_epoch, b'\x00' * 7)
                success, msg = send_lora_downlink(device_id, downlink_bytes, fport=1)
                
                devices_table.update_item(
                    Key={'DeviceId': device_id},
                    UpdateExpression='SET RtcSyncQueued = :sq, RtcSyncEpoch = :se',
                    ExpressionAttributeValues={':sq': True, ':se': ist_epoch}
                )
                
                return build_response(200, {
                    'status': 'queued',
                    'istEpoch': ist_epoch,
                    'downlinkQueued': success,
                    'message': f'RTC synchronization queued with IST timestamp (UTC+5:30: {ist_epoch}). Feeder will sync DS3231 RTC to IST on next transmission.'
                })

            elif cmd == 'STOP':
                # Real LoRaWAN Downlink: CMD_STOP_FEED (0xA5)
                downlink_bytes = struct.pack('<B11s', 0xA5, b'\x00' * 11)
                dl_success, dl_msg = send_lora_downlink(device_id, downlink_bytes, fport=1)
                print(f"[DOWNLINK] Queued CMD_STOP_FEED for {device_id}: {dl_success} ({dl_msg})")

                devices_table.update_item(
                    Key={'DeviceId': device_id},
                    UpdateExpression='SET #st = :st, FeedActive = :fa, LastSeen = :ls',
                    ExpressionAttributeNames={'#st': 'Status'},
                    ExpressionAttributeValues={':st': 'STANDBY', ':fa': False, ':ls': now_ts}
                )
                return build_response(200, {'status': 'success', 'message': f'Feeder stop queued on {device_id}', 'downlinkQueued': dl_success, 'state': 'STANDBY'})

            elif cmd == 'RESUME':
                # Real LoRaWAN Downlink: CMD_RESUME_FEED (0xA6)
                downlink_bytes = struct.pack('<B11s', 0xA6, b'\x00' * 11)
                dl_success, dl_msg = send_lora_downlink(device_id, downlink_bytes, fport=1)
                print(f"[DOWNLINK] Queued CMD_RESUME_FEED for {device_id}: {dl_success} ({dl_msg})")

                devices_table.update_item(
                    Key={'DeviceId': device_id},
                    UpdateExpression='SET #st = :st, FeedActive = :fa, LastSeen = :ls, FeedAvailable = :fa_avail',
                    ExpressionAttributeNames={'#st': 'Status'},
                    ExpressionAttributeValues={':st': 'FEEDING', ':fa': True, ':ls': now_ts, ':fa_avail': True}
                )
                return build_response(200, {'status': 'success', 'message': f'Feeder resume queued on {device_id}', 'downlinkQueued': dl_success, 'state': 'FEEDING'})
            else:
                return build_response(400, {'error': f'Unsupported command {cmd}'})

        # 5b. Query Command Execution Status & Hardware Diagnostic Results
        elif path.startswith('/api/command-status/') and http_method == 'GET':
            device_id = path.split('/')[-1]
            latest_commands = []
            last_test_result = None
            try:
                cmd_res = commands_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('DeviceId').eq(device_id),
                    ScanIndexForward=False,
                    Limit=5
                )
                latest_commands = cmd_res.get('Items', [])
            except Exception as e:
                print("Commands query error:", e)

            try:
                dev_res = devices_table.get_item(Key={'DeviceId': device_id})
                dev_item = dev_res.get('Item', {})
                last_test_result = dev_item.get('LastTestResult')
            except Exception as e:
                print("Device test result lookup error:", e)

            return build_response(200, {
                'deviceId': device_id,
                'commands': latest_commands,
                'lastTestResult': last_test_result
            })

        # 5c. Fetch Check Tray Historic Logs
        elif (path == '/api/tray-checks' or path.startswith('/api/tray-checks/')) and http_method == 'GET':
            dev_id = path.split('/')[-1] if (path.startswith('/api/tray-checks/') and path != '/api/tray-checks') else query_params.get('deviceId', '')
            checks = []
            try:
                if dev_id:
                    res = tray_checks_table.query(
                        KeyConditionExpression=boto3.dynamodb.conditions.Key('DeviceId').eq(dev_id),
                        ScanIndexForward=False,
                        Limit=50
                    )
                    checks = res.get('Items', [])
                else:
                    res = tray_checks_table.scan(Limit=50)
                    checks = res.get('Items', [])
                    checks.sort(key=lambda x: int(x.get('Timestamp', 0)), reverse=True)
            except Exception as e:
                print("Tray checks query error:", e)

            return build_response(200, {
                'deviceId': dev_id or 'all',
                'trayChecks': checks,
                'count': len(checks)
            })

        # 6. Fetch Device Telemetry
        elif path.startswith('/api/telemetry/') and http_method == 'GET':
            device_id = path.split('/')[-1]
            try:
                response = telemetry_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('DeviceId').eq(device_id),
                    ScanIndexForward=False,
                    Limit=100
                )
                items = response.get('Items', [])
                for it in items:
                    raw_ts = int(it.get('Timestamp', 0))
                    if 1700000000 <= raw_ts <= 2000000000:
                        # Device timestamp is DS3231 IST pseudo-epoch (UTC + 19800)
                        dt = datetime.utcfromtimestamp(raw_ts)
                        nh = dt.hour
                        nm = dt.minute
                        ns = dt.second
                        ampm = "PM" if nh >= 12 else "AM"
                        disph = 12 if nh % 12 == 0 else nh % 12
                        it['Time'] = f"{disph:02d}:{nm:02d}:{ns:02d} {ampm}"
                        it['Date'] = dt.strftime("%Y-%m-%d")
                        it['DateLabel'] = dt.strftime("%a %m/%d")
                    else:
                        it['Time'] = ""
                        it['Date'] = ""
            except Exception as e:
                items = []
            return build_response(200, {'deviceId': device_id, 'telemetry': items})

        # 7. Device Settings (GET / POST - Calculate and save feed schedule)
        elif path.startswith('/api/settings/'):
            device_id = path.split('/')[-1]
            if http_method == 'POST':
                feed_qty = Decimal(str(body.get('feedQuantity_kg', 15.0)))
                feed_burst = Decimal(str(body.get('feedPerEvent_g', 100)))
                rate = Decimal(str(body.get('dischargeRate_gs', 100)))
                shour = Decimal(str(body.get('startHour', 6)))
                smin = Decimal(str(body.get('startMinute', 0)))
                ehour = Decimal(str(body.get('endHour', 18)))
                emin = Decimal(str(body.get('endMinute', 0)))
                
                # Calculate feed schedule math
                total_events = int((float(feed_qty) * 1000.0) / float(feed_burst))
                motor_time_s = round(float(feed_burst) / float(rate), 2)
                single_event_s = motor_time_s + 6.0  # 3s PRE warmup + motor + 3s POST clearance
                total_cycle_s = total_events * single_event_s
                
                start_mins = int(shour) * 60 + int(smin)
                end_mins = int(ehour) * 60 + int(emin)
                feed_window_s = (end_mins - start_mins) * 60
                
                interval_min = 0.0
                valid = True
                err = ""
                
                # Check 1: 06:00 to 18:00 operational window limit
                if int(shour) < 6 or int(ehour) > 18 or (int(ehour) == 18 and int(emin) > 0):
                    valid = False
                    err = "Operational daylight window is strictly 06:00 to 18:00 (cannot exceed 18:00)"
                elif end_mins <= start_mins:
                    valid = False
                    err = "End time must be after start time"
                elif total_cycle_s >= feed_window_s:
                    valid = False
                    err = "Feed window too short for requested events and chute clearing duration"
                else:
                    interval_min = round((feed_window_s - total_cycle_s) / (total_events * 60.0), 1)
                
                now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                
                settings_item = {
                    'DeviceId': device_id,
                    'DailyTarget_kg': feed_qty,
                    'FeedQuantity_kg': feed_qty,
                    'FeedPerEvent_g': feed_burst,
                    'DischargeRate_gs': rate,
                    'StartHour': shour,
                    'StartMinute': smin,
                    'EndHour': ehour,
                    'EndMinute': emin,
                    'TotalEvents': Decimal(str(total_events)),
                    'MotorTimeSec': Decimal(str(motor_time_s)),
                    'IntervalMin': Decimal(str(interval_min)),
                    'ScheduleValid': valid,
                    'ScheduleError': err,
                    'LastUpdated': now_str
                }
                
                settings_table.put_item(Item=settings_item)
                
                # Also update device in devices table
                devices_table.update_item(
                    Key={'DeviceId': device_id},
                    UpdateExpression='SET DailyTarget_kg = :dq, FeedQuantity_kg = :fq, FeedPerEvent_g = :fpe, DischargeRate_gs = :dr, StartHour = :sh, StartMinute = :sm, EndHour = :eh, EndMinute = :em, TotalEvents = :te, MotorTimeSec = :mt, IntervalMin = :im, ScheduleValid = :sv',
                    ExpressionAttributeValues={
                        ':dq': feed_qty,
                        ':fq': feed_qty,
                        ':fpe': feed_burst,
                        ':dr': rate,
                        ':sh': shour,
                        ':sm': smin,
                        ':eh': ehour,
                        ':em': emin,
                        ':te': Decimal(str(total_events)),
                        ':mt': Decimal(str(motor_time_s)),
                        ':im': Decimal(str(interval_min)),
                        ':sv': valid
                    }
                )
                
                # Queue LoRaWAN Binary Downlink (CMD_SET_SETTINGS = 0xA0) to Hardware
                downlink_bytes = struct.pack('<BBHHBBBB2s',
                    0xA0,
                    int(emin),
                    int(float(feed_qty) * 10),
                    int(feed_burst),
                    int(ehour),
                    int(shour),
                    int(smin),
                    int(rate),
                    b'\x00\x00'
                )
                downlink_queued, dl_msg = send_lora_downlink(device_id, downlink_bytes, fport=2)
                print(f"Downlink SET_SETTINGS status: {downlink_queued} - {dl_msg}")
                
                return build_response(200, {
                    'status': 'saved',
                    'deviceId': device_id,
                    'downlinkQueued': downlink_queued,
                    'calculated': {
                        'totalEvents': total_events,
                        'motorTimeSec': motor_time_s,
                        'intervalMin': interval_min,
                        'valid': valid,
                        'error': err
                    }
                })
            else:
                response = settings_table.get_item(Key={'DeviceId': device_id})
                return build_response(200, {'settings': response.get('Item', None)})

        # 8. Daily Metrics & Historical Trends
        elif path.startswith('/api/metrics/') and http_method == 'GET':
            device_id = path.split('/')[-1]
            items = []
            try:
                response = metrics_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('DeviceId').eq(device_id),
                    ScanIndexForward=False,
                    Limit=60
                )
                items = response.get('Items', [])
            except Exception as e:
                print("Metrics query error:", e)
                
            base_qty = 50.0 if device_id == 'e072a1fffef6249c' else 15.0
            live_cur_ev = 0
            live_dispensed_kg = 0.0
            try:
                dev_res = devices_table.get_item(Key={'DeviceId': device_id})
                dev_item = dev_res.get('Item', {})
                if dev_item and 'FeedQuantity_kg' in dev_item:
                    base_qty = float(dev_item['FeedQuantity_kg'])
                if dev_item and 'CurrentEvent' in dev_item:
                    live_cur_ev = float(dev_item['CurrentEvent'])
                if dev_item and 'DispensedFeed_kg' in dev_item:
                    live_dispensed_kg = float(dev_item['DispensedFeed_kg'])
            except:
                pass
                
            # Indian Standard Time (+05:30) for farm calendar
            now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
            today_ist = now_ist.date()
            today_str = today_ist.strftime("%Y-%m-%d")
            
            # Map all available database metrics by date string
            db_by_date = {}
            if items:
                for it in items:
                    d_date = str(it.get('Date', '')).strip()
                    if not d_date: continue
                    tot_cycles = int(it.get('TotalCycles', 0))
                    raw_feed_g = float(it.get('DailyFeed_g', 0))
                    raw_feed_kg = float(it.get('DailyFeed_kg', 0))
                    
                    if raw_feed_kg > 0:
                        feed_kg = raw_feed_kg
                    elif raw_feed_g > 0:
                        feed_kg = round(raw_feed_g / 1000.0, 2)
                    elif tot_cycles > 0:
                        feed_kg = round((tot_cycles * 100) / 1000.0, 2)
                    else:
                        feed_kg = 0.0
                        
                    t_kg = float(it.get('Target_kg', base_qty))
                    db_by_date[d_date] = {
                        'DeviceId': it.get('DeviceId', device_id),
                        'Date': d_date,
                        'FeedDispensed_kg': feed_kg,
                        'Target_kg': t_kg,
                        'EventsCompleted': tot_cycles,
                        'TotalEvents': int(t_kg * 10) if t_kg > 0 else 250,
                        'AdherencePct': round(min(100.0, (feed_kg / t_kg) * 100.0) if t_kg > 0 else 100.0, 1)
                    }
                    
            # Determine if today's feeding schedule has actually started in IST
            start_hour = 6
            start_min = 0
            last_ev_str = ''
            if dev_item:
                start_hour = int(dev_item.get('StartHour', 6))
                start_min = int(dev_item.get('StartMinute', 0))
                last_ev_str = str(dev_item.get('LastEventTime', '')).strip()

            now_min = now_ist.hour * 60 + now_ist.minute
            sched_start_min = start_hour * 60 + start_min
            
            is_today_live_event = False
            if last_ev_str:
                try:
                    clean_ts = last_ev_str.replace('Z', '').replace('T', ' ')
                    dt_val = datetime.strptime(clean_ts[:19], "%Y-%m-%d %H:%M:%S")
                    dt_ist = dt_val + timedelta(hours=5, minutes=30)
                    if dt_ist.date() == today_ist and (dt_ist.hour * 60 + dt_ist.minute) >= sched_start_min:
                        is_today_live_event = True
                except:
                    pass

            if not is_today_live_event and live_cur_ev > 0:
                is_today_live_event = True

            # Build rolling 7-day calendar window ending today (IST)
            rolling_7_days = []
            for i in range(6, -1, -1):
                day_date = today_ist - timedelta(days=i)
                d_str = day_date.strftime("%Y-%m-%d")
                weekday_name = day_date.strftime("%a %m/%d")
                
                if d_str in db_by_date:
                    record = dict(db_by_date[d_str])
                    record['dateLabel'] = weekday_name
                    record['isToday'] = (i == 0)
                    rolling_7_days.append(record)
                elif i == 0 and is_today_live_event and live_dispensed_kg > 0:
                    rolling_7_days.append({
                        'DeviceId': device_id,
                        'Date': d_str,
                        'dateLabel': weekday_name,
                        'FeedDispensed_kg': live_dispensed_kg,
                        'Target_kg': base_qty,
                        'EventsCompleted': int(live_cur_ev),
                        'TotalEvents': int(base_qty * 10),
                        'AdherencePct': round(min(100.0, (live_dispensed_kg / base_qty) * 100.0) if base_qty > 0 else 100.0, 1),
                        'isToday': True
                    })
                else:
                    rolling_7_days.append({
                        'DeviceId': device_id,
                        'Date': d_str,
                        'dateLabel': weekday_name,
                        'FeedDispensed_kg': 0.0,
                        'Target_kg': base_qty,
                        'EventsCompleted': 0,
                        'TotalEvents': int(base_qty * 10),
                        'AdherencePct': 0.0,
                        'isToday': (i == 0)
                    })
                    
            return build_response(200, {'deviceId': device_id, 'metrics': rolling_7_days})

        return build_response(404, {'error': f'Route {http_method} {path} not found'})

    except Exception as e:
        print("Exception in lambda_handler:", str(e))
        return build_response(500, {'error': str(e)})

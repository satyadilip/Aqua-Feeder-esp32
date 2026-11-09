import math
import json
import base64
import struct
import boto3
from decimal import Decimal
from datetime import datetime, timedelta, timezone

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
    'e072a1fffef5bac0': '1a4212eb-63ab-4f7a-b0f2-8fe8f78ee59b',
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
    dev_key = str(dev_eui).lower().strip()
    w_id = DEVEUI_TO_WIRELESS_ID.get(dev_key)
    if not w_id:
        try:
            d_res = devices_table.get_item(Key={'DeviceId': dev_eui})
            w_id = d_res.get('Item', {}).get('WirelessDeviceId')
        except Exception:
            pass
    if not w_id:
        return False, f"Device {dev_eui} not registered in Wireless Device mapping"
    try:
        # LoRaWAN Class A queued transmission:
        # AquaFeeder nodes operate in Class A low-power mode with RX1/RX2 receive windows after uplinks.
        # TransmitMode=0 instructs AWS IoT Core Wireless to reliably queue the downlink in the device queue
        # and transmit it immediately in the RX1/RX2 window following the next uplink transmission.
        tx_mode = 0
        down_b64 = base64.b64encode(downlink_bytes).decode('ascii')
        iw_client.send_data_to_wireless_device(
            Id=w_id,
            TransmitMode=tx_mode,
            PayloadData=down_b64,
            WirelessMetadata={'LoRaWAN': {'FPort': fport}}
        )
        return True, f"Downlink queued (Class A RX1/RX2) for {dev_eui} ({w_id})"
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
                    tot_ev = float(d.get('TotalEvents', 200))
                    fpe = float(d.get('FeedPerEvent_g', 100))
                    
                    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
                    today_date_str = now_ist.strftime("%Y-%m-%d")

                    # Authoritative Dispensed Feed Today: strictly the sum of active feed events history
                    actual_dispensed_kg = 0.0
                    try:
                        today_midnight_ist = datetime(now_ist.year, now_ist.month, now_ist.day, 0, 0, 0)
                        today_start_epoch = int(datetime(now_ist.year, now_ist.month, now_ist.day, 0, 0, 0, tzinfo=timezone.utc).timestamp())
                        t_resp = telemetry_table.query(
                            KeyConditionExpression=boto3.dynamodb.conditions.Key('DeviceId').eq(dev_id),
                            ScanIndexForward=False,
                            Limit=50
                        )
                        items = t_resp.get('Items', [])
                        
                        # Find the active event and hardware dispensed grams from latest telemetry of TODAY (IST)
                        active_ev = 0
                        hw_disp_g = 0.0
                        for it in items:
                            ts = int(it.get('Timestamp', 0))
                            if ts < today_start_epoch:
                                continue
                            ev = int(it.get('CurrentEvent', 0))
                            disp_g = float(it.get('FeedDispensed_g', 0))
                            if ev > 0:
                                if active_ev == 0:
                                    active_ev = ev
                                if hw_disp_g == 0.0 and disp_g > 0:
                                    hw_disp_g = disp_g
                                break
                        
                        if hw_disp_g > 0 and active_ev > 0:
                            actual_dispensed_kg = round(hw_disp_g / 1000.0, 2)
                        else:
                            # Monotonic active cycle extraction (strictly today's items)
                            events_today = {}
                            for t_it in items:
                                ts = int(t_it.get('Timestamp', 0))
                                if ts < today_start_epoch:
                                    break
                                ev_num = int(t_it.get('CurrentEvent', 0))
                                if ev_num <= 0:
                                    continue
                                if active_ev > 0 and ev_num > active_ev:
                                    break  # Hit prior run boundary!
                                if ev_num not in events_today:
                                    eg = float(t_it.get('EventGrams', t_it.get('FeedPerEvent_g', fpe)))
                                    events_today[ev_num] = eg
                            if events_today:
                                actual_dispensed_kg = round(sum(events_today.values()) / 1000.0, 2)
                    except Exception as te_err:
                        pass

                    # Fallbacks if telemetry query returned no events:
                    # ONLY use device table fallbacks if TodayDate matches today's date!
                    if str(d.get('TodayDate', '')).strip() == today_date_str:
                        if actual_dispensed_kg == 0.0:
                            if float(d.get('TodayFeedDispensed_kg', 0)) > 0:
                                actual_dispensed_kg = round(float(d.get('TodayFeedDispensed_kg')), 2)
                            elif float(d.get('DispensedFeed_kg', 0)) > 0:
                                actual_dispensed_kg = round(float(d.get('DispensedFeed_kg')), 2)
                            elif cur_ev > 0 and fpe > 0:
                                actual_dispensed_kg = round((cur_ev * fpe) / 1000.0, 2)
                    else:
                        # Day rollover: reset today's active counter if recorded date is from a previous calendar day
                        cur_ev = 0
                        actual_dispensed_kg = 0.0

                    dispensed_kg = actual_dispensed_kg
                    target_kg = float(d.get('FeedQuantity_kg', round((tot_ev * fpe) / 1000.0, 1)))
                    
                    d['DispensedFeed_kg'] = actual_dispensed_kg
                    d['TodayFeedDispensed_kg'] = actual_dispensed_kg
                    d['FeedQuantity_kg'] = target_kg
                    d['CurrentEvent'] = int(cur_ev)
                    d['TotalEvents'] = int(tot_ev)
                    d['FeedPerEvent_g'] = int(fpe)
                    d['LastSeenEpoch'] = int(d.get('LastSeenEpoch', int(datetime.utcnow().timestamp())))
                    d['LastEventTime'] = str(d.get('LastEventTime', datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")))
                    
                    # Merge user-configured settings if present (Authoritative Daily Target)
                    try:
                        s_res = settings_table.get_item(Key={'DeviceId': dev_id})
                        s_item = s_res.get('Item')
                        if s_item:
                            target_kg = float(s_item.get('DailyTarget_kg', s_item.get('FeedQuantity_kg', target_kg)))
                            fpe = float(s_item.get('FeedPerEvent_g', fpe if fpe > 0 else 100))
                            d['DailyTarget_kg'] = target_kg
                            d['FeedQuantity_kg'] = target_kg
                            d['StartHour'] = int(s_item.get('StartHour', d.get('StartHour', 6)))
                            d['StartMinute'] = int(s_item.get('StartMinute', d.get('StartMinute', 0)))
                            d['EndHour'] = int(s_item.get('EndHour', d.get('EndHour', 18)))
                            d['EndMinute'] = int(s_item.get('EndMinute', d.get('EndMinute', 0)))
                            d['DischargeRate_gs'] = int(s_item.get('DischargeRate_gs', d.get('DischargeRate_gs', 100)))
                            d['MotorTimeSec'] = float(s_item.get('MotorTimeSec', d.get('MotorTimeSec', 1.0)))
                            d['ScheduleValid'] = True
                            d['SettingsSyncStatus'] = str(s_item.get('SettingsSyncStatus', d.get('SettingsSyncStatus', 'IN_SYNC')))
                            d['SettingsPushedAt'] = str(s_item.get('SettingsPushedAt', d.get('SettingsPushedAt', '')))
                            d['SettingsConfirmedAt'] = str(s_item.get('SettingsConfirmedAt', d.get('SettingsConfirmedAt', '')))
                            if 'PendingDailyTarget_kg' in s_item and s_item['PendingDailyTarget_kg'] is not None:
                                d['PendingDailyTarget_kg'] = float(s_item['PendingDailyTarget_kg'])
                            if 'ReportedDailyTarget_kg' in s_item and s_item['ReportedDailyTarget_kg'] is not None:
                                d['ReportedDailyTarget_kg'] = float(s_item['ReportedDailyTarget_kg'])
                            d['PendingCommand'] = d.get('PendingCommand', None)
                            d['CommandPushedAt'] = str(d.get('CommandPushedAt', ''))
                            d['CommandConfirmedAt'] = str(d.get('CommandConfirmedAt', ''))

                            # Exact Runtime Deductive Schedule Math matching firmware:
                            # Deductive math ONLY applies during the ACTIVE daylight feeding window for an unfinished cycle.
                            # After hours (>= end_mins), early morning (< start_mins), or when already COMPLETED:
                            # Today's run is finished! target_kg represents the upcoming / next cycle target.
                            start_mins_dev = int(s_item.get('StartHour', 6)) * 60 + int(s_item.get('StartMinute', 0))
                            end_mins_dev = int(s_item.get('EndHour', 18)) * 60 + int(s_item.get('EndMinute', 0))
                            now_ist_mins_dev = now_ist.hour * 60 + now_ist.minute
                            is_active_feeding = (start_mins_dev <= now_ist_mins_dev < end_mins_dev) and str(d.get('Status', '')).upper() not in ['COMPLETED', 'SCHEDULE ENDED']

                            if is_active_feeding and cur_ev > 0 and dispensed_kg > 0:
                                rem_kg = max(0.0, target_kg - dispensed_kg)
                                rem_ev = int(math.ceil((rem_kg * 1000.0) / fpe)) if rem_kg > 0 else 0
                                tot_ev = float(int(cur_ev) + rem_ev)
                            elif str(d.get('Status', '')).upper() == 'COMPLETED' or now_ist_mins_dev >= end_mins_dev:
                                # Today's cycle has ended! Today's completed events is locked to what ran today.
                                tot_ev = float(int(cur_ev)) if cur_ev > 0 else float(int(math.ceil((target_kg * 1000.0) / fpe)))
                            else:
                                tot_ev = float(int(math.ceil((target_kg * 1000.0) / fpe))) if fpe > 0 else 150.0
                        d['FirmwareVersion'] = str(d.get('FirmwareVersion', 'v1.0'))
                        d['FirmwareName'] = str(d.get('FirmwareName', 'AquaFeeder Firmware'))
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
                    # Dynamic device name and pond mapping for all registered feeders
                    existing_name = d.get('DeviceName')
                    existing_pond = d.get('PondId')
                    if existing_name:
                        feeder_name = existing_name
                    elif dev_id == 'e072a1fffef6249c':
                        feeder_name = 'aquaCON Feeder 01'
                    elif dev_id == 'e072a1fffef5ba08':
                        feeder_name = 'aquaCON Feeder 02'
                    elif dev_id == 'e072a1fffef64134':
                        feeder_name = 'aquaCON Feeder 03'
                    elif dev_id == 'e072a1fffef5bac0':
                        feeder_name = 'aquaCON Feeder 04'
                    elif dev_id == 'e072a1f6249c0005':
                        feeder_name = 'aquaCON Feeder 05'
                    else:
                        feeder_name = f"aquaCON Feeder {dev_id[-4:]}"

                    if existing_pond:
                        pond_name = existing_pond
                    elif dev_id in ['e072a1fffef64134', 'e072a1fffef5bac0']:
                        pond_name = 'P-02'
                    else:
                        pond_name = 'P-01'

                    d['DeviceName'] = feeder_name
                    d['PondId'] = pond_name
                    is_online = (now_epoch - int(d.get('LastSeenEpoch', 0))) < 900
                    d['Connected'] = is_online

                    # --- STORY-009 & STORY-010: Decoupled Today Completed State vs Scheduled State ---
                    today_date_str = now_ist.strftime("%Y-%m-%d")
                    
                    today_recorded_date = str(d.get('TodayDate', '')).strip()
                    today_events_done = int(d.get('TodayEventsCompleted', 0))
                    today_kg_done = float(d.get('TodayFeedDispensed_kg', 0.0))
                    today_tot_events = int(d.get('TodayTotalEvents', tot_ev))
                    today_recorded_status = str(d.get('TodayStatus', '')).strip().upper()

                    # Fallback: check AquaFeeder_DailyMetrics for today if TodayEventsCompleted is not yet set in devices_table
                    if today_recorded_date != today_date_str or today_events_done == 0:
                        try:
                            m_res = metrics_table.get_item(Key={'DeviceId': dev_id, 'Date': today_date_str})
                            m_item = m_res.get('Item')
                            if m_item and int(m_item.get('TotalCycles', 0)) > 0:
                                today_recorded_date = today_date_str
                                today_events_done = int(m_item.get('TotalCycles', 0))
                                today_kg_done = float(m_item.get('DailyFeed_kg', 0.0))
                                today_tot_events = int(m_item.get('TargetEvents', today_events_done))
                                today_recorded_status = 'COMPLETED'
                        except Exception:
                            pass

                    is_today_run = (today_recorded_date == today_date_str and today_events_done > 0)
                    
                    # Alarm bit decoding: Bit 3 (8) = Feed Empty, Bit 4 (16) = Proximity Pause
                    raw_feed_avail = d.get('FeedAvailable', True)
                    raw_status = str(d.get('Status', '')).strip().upper()
                    status_flags = int(d.get('StatusFlags', 0))
                    if (status_flags & 0x08) != 0 or raw_feed_avail is False or raw_status == 'FEED EMPTY':
                        actual_feed_avail = False
                    else:
                        actual_feed_avail = True

                    s_ampm = "PM" if s_hour >= 12 else "AM"
                    s_disph = 12 if s_hour % 12 == 0 else s_hour % 12
                    s_time_fmt = f"{s_disph:02d}:{s_min:02d} {s_ampm}"

                    # Dynamic interval calculation
                    d_rate = float(d.get('DischargeRate_gs', 100))
                    if d_rate <= 0.1: d_rate = 100.0
                    m_time_s = round(float(fpe) / d_rate, 2)
                    single_ev_s = 3.0 + m_time_s + 3.0
                    tot_ev_int = int(tot_ev)

                    # Full Window Base Gap Calculation
                    full_window_s = max(60, (end_min - start_min) * 60)
                    tot_dur_s = tot_ev_int * single_ev_s
                    base_gap_s = max(5, int((full_window_s - tot_dur_s) / max(1, tot_ev_int)))
                    base_interval_m = round(base_gap_s / 60.0, 1)

                    # True completion conditions:
                    # 1. All scheduled events physically finished (cur_ev >= tot_ev_int), OR
                    # 2. Target dispensed weight reached (dispensed_kg >= target_kg), OR
                    # 3. Past operational end time (now_min >= end_min) AND feeding actually ran today (cur_ev > 0 or dispensed_kg > 0)
                    is_truly_completed = (tot_ev_int > 0 and cur_ev >= tot_ev_int) or \
                                         (target_kg > 0 and dispensed_kg >= target_kg) or \
                                         (now_min >= end_min and (cur_ev > 0 or dispensed_kg > 0))

                    is_inside_schedule = (start_min <= now_min < end_min)
                    is_feed_stopped = (raw_status in ['STANDBY', 'STOPPED']) or (d.get('FeedActive') is False)
                    # Bit 5 (0x20) is SD Card Fault, NOT Feed Active!
                    # Feeder is ONLY actively feeding if inside operational daylight window and not stopped
                    is_active_feed = (raw_status in ['FEEDING', 'ACTIVE']) and is_inside_schedule and not is_feed_stopped

                    # Phase 1: Date Rollover / Pre-dawn (00:00:00 to start_min IST before window)
                    if now_min < start_min:
                        actual_status = 'STANDBY'
                        live_cur_ev = 0
                        live_tot_ev = tot_ev_int
                        live_rem_ev = tot_ev_int
                        live_disp_kg = 0.0
                        gap_s = base_gap_s
                        dyn_interval_m = base_interval_m
                        next_feed_str = s_time_fmt
                        next_feed_sub = f"Starts today at {s_time_fmt}"

                    # Phase 2: Feed Completed Today (concluded after all pulses or past 18:00 with feeds delivered)
                    elif (is_truly_completed or now_min >= end_min) and not is_active_feed:
                        if now_min >= end_min and not is_today_run and cur_ev == 0:
                            actual_status = 'STANDBY'
                            live_cur_ev = 0
                            live_tot_ev = tot_ev_int
                            live_rem_ev = tot_ev_int
                            live_disp_kg = 0.0
                            next_feed_str = s_time_fmt
                            next_feed_sub = f"Starts tomorrow at {s_time_fmt}"
                        else:
                            actual_status = 'COMPLETED'
                            live_cur_ev = int(cur_ev)
                            live_tot_ev = max(tot_ev_int, int(cur_ev))
                            live_rem_ev = 0
                            live_disp_kg = dispensed_kg
                            next_feed_str = s_time_fmt
                            next_feed_sub = f"Starts tomorrow at {s_time_fmt}"
                        gap_s = base_gap_s
                        dyn_interval_m = base_interval_m

                    # Phase 3: Standby / Stopped (user commanded STOP or device in standby)
                    elif is_feed_stopped or raw_status == 'STANDBY':
                        actual_status = 'STANDBY'
                        live_cur_ev = int(cur_ev)
                        live_tot_ev = tot_ev_int
                        live_rem_ev = max(0, tot_ev_int - live_cur_ev)
                        live_disp_kg = dispensed_kg
                        gap_s = base_gap_s
                        dyn_interval_m = base_interval_m
                        next_feed_str = "--"
                        next_feed_sub = "Feed Paused / Standby"

                    # Phase 4: Active Feeding Window (motor or feed cycle physically active during operational window)
                    elif is_active_feed and is_inside_schedule:
                        actual_status = 'FEEDING'
                        live_cur_ev = int(cur_ev)
                        live_tot_ev = tot_ev_int
                        live_rem_ev = max(0, tot_ev_int - live_cur_ev)
                        live_disp_kg = dispensed_kg
                        
                        sec_since_midnight = now_ist.hour * 3600 + now_ist.minute * 60 + now_ist.second
                        end_sec_today = e_hour * 3600 + e_min * 60
                        rem_time_s = max(0, end_sec_today - sec_since_midnight)
                        rem_calc = max(1, live_rem_ev)
                        rem_dur_s = rem_calc * single_ev_s
                        if rem_time_s > rem_dur_s and live_rem_ev > 0:
                            gap_s = max(5, int((rem_time_s - rem_dur_s) / rem_calc))
                        else:
                            gap_s = base_gap_s
                        dyn_interval_m = round(gap_s / 60.0, 1)

                        next_ev_num = live_cur_ev + 1
                        last_seen_epoch = int(d.get('LastSeenEpoch', 0))
                        # Deterministic scheduled event timeline from morning start:
                        midnight_ist_epoch = now_epoch - sec_since_midnight
                        start_epoch_today = midnight_ist_epoch + (start_min * 60)
                        sched_epoch = start_epoch_today + int(live_cur_ev * (single_ev_s + gap_s))
                        
                        if last_seen_epoch > 0 and 0 < (now_epoch - last_seen_epoch) < (gap_s + 60):
                            next_feed_epoch = last_seen_epoch + gap_s
                        elif sched_epoch > now_epoch:
                            next_feed_epoch = sched_epoch
                        else:
                            next_feed_epoch = now_epoch + gap_s
                            
                        next_ist = datetime.utcfromtimestamp(next_feed_epoch) + timedelta(hours=5, minutes=30)
                        next_feed_str = next_ist.strftime("%I:%M %p")
                        rem_seconds = max(0, next_feed_epoch - now_epoch)
                        rem_m = int(round(rem_seconds / 60.0))
                        if rem_m <= 1:
                            next_feed_sub = f"Event {next_ev_num} of {live_tot_ev} · Due now (Every {dyn_interval_m}m)"
                        else:
                            next_feed_sub = f"Event {next_ev_num} of {live_tot_ev} · in {rem_m}m (Every {dyn_interval_m}m)"

                    # Phase 5: Standby / Scheduled before first pulse during window or after hours with 0 events
                    else:
                        actual_status = 'SCHEDULED' if now_min < end_min else 'STANDBY'
                        live_cur_ev = int(cur_ev)
                        live_tot_ev = tot_ev_int
                        live_rem_ev = max(0, tot_ev_int - live_cur_ev)
                        live_disp_kg = dispensed_kg
                        gap_s = base_gap_s
                        dyn_interval_m = base_interval_m
                        next_feed_str = s_time_fmt
                        next_feed_sub = f"Starts at {s_time_fmt}" if now_min < end_min else f"Starts tomorrow at {s_time_fmt}"

                    # Overrides for offline / alarms
                    if not is_online:
                        actual_status = 'NOT CONNECTED'
                        next_feed_str = "--"
                        next_feed_sub = "Feeder Offline"
                    elif (status_flags & 0x02) != 0 or raw_status in ['MOTOR OVERCURRENT', 'MOTOR JAM / OVERCURRENT']:
                        actual_status = 'MOTOR JAM / OVERCURRENT'
                        next_feed_str = "--"
                        next_feed_sub = "Motor Trip Detected"
                    elif (status_flags & 0x10) != 0 or raw_status == 'PAUSED':
                        actual_status = 'PAUSED'
                        next_feed_str = "--"
                        next_feed_sub = "Feed Paused"
                    elif not actual_feed_avail or raw_status == 'FEED EMPTY':
                        actual_status = 'FEED EMPTY'
                        next_feed_str = "--"
                        next_feed_sub = "Refill Required"

                    d['FeedAvailable'] = actual_feed_avail if is_online else False
                    d['Status'] = actual_status
                    d['StatusFlags'] = status_flags
                    d['TotalEvents'] = live_tot_ev
                    d['CurrentEvent'] = live_cur_ev
                    d['TotalEventsRemaining'] = live_rem_ev
                    d['FeedPerEvent_g'] = int(fpe)
                    d['FeedQuantity_kg'] = target_kg
                    d['DailyTarget_kg'] = target_kg
                    d['DispensedFeed_kg'] = live_disp_kg
                    d['IntervalMin'] = dyn_interval_m
                    d['GapIntervalSec'] = gap_s
                    d['NextFeed'] = next_feed_str
                    d['NextFeedSub'] = next_feed_sub
                    d['ScheduleValid'] = True

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
            
            now_ist_dt = datetime.utcnow() + timedelta(hours=5, minutes=30)
            pushed_ist_str = now_ist_dt.strftime("%Y-%m-%d %I:%M:%S %p IST")

            if cmd in ['START', 'FEED']:
                # STRICT NIGHT GUARD: Prohibit manual/remote start outside operational daylight hours
                try:
                    dev_res = devices_table.get_item(Key={'DeviceId': device_id})
                    dev_item = dev_res.get('Item', {})
                    shour = int(dev_item.get('StartHour', 6))
                    smin = int(dev_item.get('StartMinute', 0))
                    ehour = int(dev_item.get('EndHour', 18))
                    emin = int(dev_item.get('EndMinute', 0))
                    now_ist_mins = now_ist_dt.hour * 60 + now_ist_dt.minute
                    start_mins = shour * 60 + smin
                    end_mins = ehour * 60 + emin
                    if now_ist_mins < start_mins or now_ist_mins >= end_mins:
                        s_ampm = "PM" if shour >= 12 else "AM"
                        s_disph = 12 if shour % 12 == 0 else shour % 12
                        e_ampm = "PM" if ehour >= 12 else "AM"
                        e_disph = 12 if ehour % 12 == 0 else ehour % 12
                        err_msg = f"Strict Night Guard: Feeding is prohibited outside daylight hours ({s_disph:02d}:{smin:02d} {s_ampm} - {e_disph:02d}:{emin:02d} {e_ampm}). Scheduled feeding will start automatically at {s_disph:02d}:{smin:02d} {s_ampm}."
                        print(f"[REJECT_START] {device_id}: {err_msg}")
                        return build_response(400, {'error': err_msg})
                except Exception as guard_err:
                    print("Night guard check error:", guard_err)

                # Real LoRaWAN Downlink: CMD_START_FEED (0xA4)
                downlink_bytes = struct.pack('<B11s', 0xA4, b'\x00' * 11)
                dl_success, dl_msg = send_lora_downlink(device_id, downlink_bytes, fport=1)
                print(f"[DOWNLINK] Queued CMD_START_FEED for {device_id}: {dl_success} ({dl_msg})")

                devices_table.update_item(
                    Key={'DeviceId': device_id},
                    UpdateExpression='SET PendingCommand = :cmd, CommandPushedAt = :pat, DownlinkQueued = :dq',
                    ExpressionAttributeValues={
                        ':cmd': 'START',
                        ':pat': pushed_ist_str,
                        ':dq': dl_success
                    }
                )
                return build_response(200, {
                    'status': 'queued',
                    'pendingCommand': 'START',
                    'pushedAt': pushed_ist_str,
                    'downlinkQueued': dl_success,
                    'message': f'Feed START command queued. Waiting for feeder radio window...'
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
                    UpdateExpression='SET PendingCommand = :cmd, CommandPushedAt = :pat, DownlinkQueued = :dq',
                    ExpressionAttributeValues={
                        ':cmd': 'STOP',
                        ':pat': pushed_ist_str,
                        ':dq': dl_success
                    }
                )
                return build_response(200, {
                    'status': 'queued',
                    'pendingCommand': 'STOP',
                    'pushedAt': pushed_ist_str,
                    'downlinkQueued': dl_success,
                    'message': f'Feed STOP command queued. Waiting for feeder confirmation...'
                })

            elif cmd == 'RESUME':
                # Real LoRaWAN Downlink: CMD_RESUME_FEED (0xA6)
                downlink_bytes = struct.pack('<B11s', 0xA6, b'\x00' * 11)
                dl_success, dl_msg = send_lora_downlink(device_id, downlink_bytes, fport=1)
                print(f"[DOWNLINK] Queued CMD_RESUME_FEED for {device_id}: {dl_success} ({dl_msg})")

                devices_table.update_item(
                    Key={'DeviceId': device_id},
                    UpdateExpression='SET PendingCommand = :cmd, CommandPushedAt = :pat, DownlinkQueued = :dq',
                    ExpressionAttributeValues={
                        ':cmd': 'RESUME',
                        ':pat': pushed_ist_str,
                        ':dq': dl_success
                    }
                )
                return build_response(200, {
                    'status': 'queued',
                    'pendingCommand': 'RESUME',
                    'pushedAt': pushed_ist_str,
                    'downlinkQueued': dl_success,
                    'message': f'Feed RESUME command queued. Waiting for feeder radio window...'
                })
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

        # 6. Fetch Device Telemetry (Supports ?date=YYYY-MM-DD, 15-day lookup & hourly distribution)
        elif path.startswith('/api/telemetry/') and http_method == 'GET':
            device_id = path.split('/')[-1]
            req_date = (query_params.get('date') or '').strip()
            try:
                now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
                today_date_str = now_ist.strftime("%Y-%m-%d")

                raw_items = []
                lek = None
                pages = 0
                target_date = req_date if req_date else None
                is_fallback = False

                # Paged DynamoDB query scanning backwards from newest entries
                while len(raw_items) < 600 and pages < 15:
                    pages += 1
                    q_args = {
                        'KeyConditionExpression': boto3.dynamodb.conditions.Key('DeviceId').eq(device_id),
                        'ScanIndexForward': False,
                        'Limit': 200
                    }
                    if lek:
                        q_args['ExclusiveStartKey'] = lek
                    response = telemetry_table.query(**q_args)
                    cur_items = response.get('Items', [])
                    if not cur_items:
                        break

                    # If no target date requested, determine if today has active events;
                    # if today has 0 events (e.g. pre-dawn before 06:00), automatically anchor
                    # to the most recent calendar day that contains completed pulses!
                    if not target_date:
                        has_today = any(datetime.utcfromtimestamp(int(x.get('Timestamp', 0))).strftime("%Y-%m-%d") == today_date_str and int(x.get('CurrentEvent', 0)) > 0 for x in cur_items)
                        if has_today:
                            target_date = today_date_str
                        else:
                            for it in cur_items:
                                ev_num = int(it.get('CurrentEvent', 0))
                                if ev_num > 0:
                                    cand_date = datetime.utcfromtimestamp(int(it.get('Timestamp', 0))).strftime("%Y-%m-%d")
                                    target_date = cand_date
                                    if target_date != today_date_str:
                                        is_fallback = True
                                    break
                            if not target_date:
                                target_date = today_date_str

                    reached_past = False
                    for it in cur_items:
                        ts = int(it.get('Timestamp', 0))
                        dt = datetime.utcfromtimestamp(ts)
                        d_str = dt.strftime("%Y-%m-%d")
                        if d_str == target_date:
                            raw_items.append(it)
                        elif d_str < target_date:
                            reached_past = True
                            break

                    lek = response.get('LastEvaluatedKey')
                    if reached_past or not lek:
                        break

                # Deduplicate by CurrentEvent:
                # Standby heartbeats in the evening repeat the last CurrentEvent (e.g. Event 100).
                # To ensure the event record reflects when feed was ACTUALLY dispensed (during daylight feeding hours)
                # and NOT an evening standby heartbeat, we pick the true daytime dispensing record for each event.
                distinct_by_ev = {}
                for it in raw_items:
                    ev = int(it.get('CurrentEvent', 0))
                    if ev > 0:
                        raw_ts = int(it.get('Timestamp', 0))
                        dt = datetime.utcfromtimestamp(raw_ts)
                        is_daytime = (dt.hour * 60 + dt.minute <= 18 * 60 + 5)
                        if ev not in distinct_by_ev:
                            distinct_by_ev[ev] = it
                        else:
                            prev_ts = int(distinct_by_ev[ev].get('Timestamp', 0))
                            prev_dt = datetime.utcfromtimestamp(prev_ts)
                            prev_is_daytime = (prev_dt.hour * 60 + prev_dt.minute <= 18 * 60 + 5)
                            if is_daytime and not prev_is_daytime:
                                distinct_by_ev[ev] = it
                            elif is_daytime and prev_is_daytime and raw_ts < prev_ts:
                                # Retain the earliest daytime packet (the exact moment event was dispensed)
                                distinct_by_ev[ev] = it

                sorted_ev_nums = sorted(distinct_by_ev.keys())

                # Recover physical pulse deltas from cumulative hardware counter FeedDispensed_g
                prev_fg = None
                calculated_pulse_grams = {}
                for ev in sorted_ev_nums:
                    it_ev = distinct_by_ev[ev]
                    fg = int(it_ev.get('FeedDispensed_g', 0))
                    if prev_fg is not None and fg > prev_fg and 10 <= (fg - prev_fg) <= 2000:
                        calculated_pulse_grams[ev] = fg - prev_fg
                    prev_fg = fg

                hourly_grams = [0] * 24
                for ev in sorted_ev_nums:
                    it = distinct_by_ev[ev]
                    ev_num = int(it.get('CurrentEvent', 0))
                    if ev_num in calculated_pulse_grams:
                        it['EventGrams'] = calculated_pulse_grams[ev_num]
                    elif 'EventGrams' not in it or it['EventGrams'] is None or int(it.get('EventGrams', 0)) == 0:
                        it['EventGrams'] = int(it.get('FeedPerEvent_g', 100))
                    raw_ts = int(it.get('Timestamp', 0))
                    if 1700000000 <= raw_ts <= 2000000000:
                        dt = datetime.utcfromtimestamp(raw_ts)
                        nh = dt.hour
                        nm = dt.minute
                        ns = dt.second
                        ampm = "PM" if nh >= 12 else "AM"
                        disph = 12 if nh % 12 == 0 else nh % 12
                        it['Time'] = f"{disph:02d}:{nm:02d}:{ns:02d} {ampm}"
                        it['Date'] = dt.strftime("%Y-%m-%d")
                        it['DateLabel'] = dt.strftime("%a %m/%d")
                        if 0 <= nh < 24:
                            hourly_grams[nh] += int(it['EventGrams'])
                    else:
                        it['Time'] = ""
                        it['Date'] = ""

                items = [distinct_by_ev[ev] for ev in reversed(sorted_ev_nums)]
                total_dispensed_g = sum(int(distinct_by_ev[ev].get('EventGrams', 0)) for ev in sorted_ev_nums)
                hourly_kg = [round(g / 1000.0, 3) for g in hourly_grams]
            except Exception as e:
                print(f"Telemetry history fetch error: {e}")
                items = []
                target_date = today_date_str
                is_fallback = False
                total_dispensed_g = 0
                hourly_kg = [0.0] * 24

            return build_response(200, {
                'deviceId': device_id,
                'date': target_date or today_date_str,
                'isToday': (target_date == today_date_str),
                'isHistoricalFallback': is_fallback,
                'totalEvents': len(sorted_ev_nums) if 'sorted_ev_nums' in locals() else len(items),
                'totalDispensedKg': round(total_dispensed_g / 1000.0, 2),
                'hourlyKg': hourly_kg,
                'telemetry': items
            })

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
                
                feed_qty_float = float(feed_qty)
                feed_burst_float = float(feed_burst)
                rate_float = float(rate) if float(rate) > 0.1 else 100.0

                # Fetch existing device state to account for already dispensed feed today
                existing_dev = {}
                try:
                    dev_res = devices_table.get_item(Key={'DeviceId': device_id})
                    existing_dev = dev_res.get('Item', {})
                except Exception as e:
                    print(f"Error fetching existing device: {e}")

                now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
                today_date_str = now_ist.strftime("%Y-%m-%d")

                cur_ev = int(existing_dev.get('CurrentEvent', 0))
                dispensed_kg = float(existing_dev.get('DispensedFeed_kg', 0.0))
                today_ev = int(existing_dev.get('TodayEventsCompleted', 0))
                today_kg = float(existing_dev.get('TodayFeedDispensed_kg', 0.0))
                today_date = str(existing_dev.get('TodayDate', '')).strip()

                already_ran_events = 0
                already_dispensed_kg = 0.0
                if cur_ev > 0 and dispensed_kg > 0:
                    already_ran_events = cur_ev
                    already_dispensed_kg = dispensed_kg
                elif today_date == today_date_str and today_ev > 0:
                    already_ran_events = today_ev
                    already_dispensed_kg = today_kg if today_kg > 0 else dispensed_kg

                if 'alreadyDispensed_kg' in body and float(body['alreadyDispensed_kg']) > 0:
                    cand_kg = float(body['alreadyDispensed_kg'])
                    # Sanity-check: never allow alreadyDispensed_kg to drastically exceed what already_ran_events could physically dispense
                    if already_ran_events > 0:
                        max_allowed = (already_ran_events * feed_burst_float / 1000.0) * 1.5
                        if cand_kg <= max_allowed:
                            already_dispensed_kg = cand_kg
                        else:
                            already_dispensed_kg = round((already_ran_events * feed_burst_float) / 1000.0, 2)
                    else:
                        already_dispensed_kg = 0.0
                if 'alreadyRanEvents' in body and int(body['alreadyRanEvents']) > 0:
                    already_ran_events = max(already_ran_events, int(body['alreadyRanEvents']))

                motor_time_s = round(feed_burst_float / rate_float, 2)
                single_event_s = 3.0 + motor_time_s + 3.0  # 3s PRE warmup + motor + 3s POST clearance

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

                # Runtime Deductive Schedule Calculation:
                # Deductive math applies strictly DURING the active daylight window (start_mins <= now < end_mins).
                # After hours (>= end_mins) or early morning (< start_mins), settings configure the full upcoming daytime window.
                now_ist_mins = now_ist.hour * 60 + now_ist.minute
                is_active_daytime_window = (start_mins <= now_ist_mins < end_mins)

                if is_active_daytime_window and already_ran_events > 0 and already_dispensed_kg > 0:
                    remaining_kg = max(0.0, feed_qty_float - already_dispensed_kg)
                    remaining_events = int(math.ceil((remaining_kg * 1000.0) / feed_burst_float)) if remaining_kg > 0 else 0
                    total_events = already_ran_events + remaining_events

                    sec_since_midnight = now_ist.hour * 3600 + now_ist.minute * 60 + now_ist.second
                    end_sec_today = int(ehour) * 3600 + int(emin) * 60
                    rem_window_s = max(0, end_sec_today - sec_since_midnight)
                    rem_cycles_s = remaining_events * single_event_s

                    if remaining_events > 0:
                        if rem_cycles_s >= rem_window_s:
                            valid = False
                            err = f"Remaining time ({rem_window_s}s) too short for {remaining_events} remaining events ({rem_cycles_s}s)"
                            interval_min = 0.0
                        else:
                            gap_s = max(5, int((rem_window_s - rem_cycles_s) / remaining_events))
                            interval_min = round(gap_s / 60.0, 1)
                    else:
                        interval_min = 0.0
                else:
                    total_events = int(math.ceil((feed_qty_float * 1000.0) / feed_burst_float))
                    remaining_events = total_events
                    total_cycle_s = total_events * single_event_s
                    if total_cycle_s >= feed_window_s:
                        valid = False
                        err = "Feed window too short for requested events and chute clearing duration"
                    else:
                        gap_s = max(5, int((feed_window_s - total_cycle_s) / total_events))
                        interval_min = round(gap_s / 60.0, 1)
                
                now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                pushed_ist_str = now_ist.strftime("%Y-%m-%d %I:%M:%S %p IST")

                # Fetch existing settings to preserve last confirmed reported values
                existing_settings = {}
                try:
                    s_cur = settings_table.get_item(Key={'DeviceId': device_id})
                    existing_settings = s_cur.get('Item', {})
                except Exception:
                    pass

                reported_qty = existing_settings.get('ReportedDailyTarget_kg', existing_dev.get('ReportedDailyTarget_kg', existing_dev.get('DailyTarget_kg', feed_qty)))
                reported_fpe = existing_settings.get('ReportedFeedPerEvent_g', existing_dev.get('ReportedFeedPerEvent_g', existing_dev.get('FeedPerEvent_g', feed_burst)))
                last_confirmed_at = existing_settings.get('SettingsConfirmedAt', existing_dev.get('SettingsConfirmedAt', ''))

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
                    'SettingsSyncStatus': 'PENDING',
                    'SettingsPushedAt': pushed_ist_str,
                    'SettingsConfirmedAt': last_confirmed_at,
                    'PendingDailyTarget_kg': feed_qty,
                    'PendingFeedPerEvent_g': feed_burst,
                    'ReportedDailyTarget_kg': reported_qty,
                    'ReportedFeedPerEvent_g': reported_fpe,
                    'LastUpdated': now_str
                }
                
                settings_table.put_item(Item=settings_item)
                
                # Also update device in devices table - preserving immutable dispensed feed history
                update_expr = 'SET DailyTarget_kg = :dq, FeedQuantity_kg = :fq, FeedPerEvent_g = :fpe, DischargeRate_gs = :dr, StartHour = :sh, StartMinute = :sm, EndHour = :eh, EndMinute = :em, TotalEvents = :te, TotalEventsRemaining = :ter, MotorTimeSec = :mt, IntervalMin = :im, ScheduleValid = :sv, SettingsSyncStatus = :sync, SettingsPushedAt = :spat, PendingDailyTarget_kg = :pdq, PendingFeedPerEvent_g = :pfpe, ReportedDailyTarget_kg = :rdq, ReportedFeedPerEvent_g = :rfpe'
                expr_vals = {
                    ':dq': feed_qty,
                    ':fq': feed_qty,
                    ':fpe': feed_burst,
                    ':dr': rate,
                    ':sh': shour,
                    ':sm': smin,
                    ':eh': ehour,
                    ':em': emin,
                    ':te': Decimal(str(total_events)),
                    ':ter': Decimal(str(remaining_events)),
                    ':mt': Decimal(str(motor_time_s)),
                    ':im': Decimal(str(interval_min)),
                    ':sv': valid,
                    ':sync': 'PENDING',
                    ':spat': pushed_ist_str,
                    ':pdq': feed_qty,
                    ':pfpe': feed_burst,
                    ':rdq': reported_qty,
                    ':rfpe': reported_fpe
                }
                if already_dispensed_kg > 0:
                    update_expr += ', DispensedFeed_kg = :dfk, TodayFeedDispensed_kg = :tfd'
                    expr_vals[':dfk'] = Decimal(str(round(already_dispensed_kg, 2)))
                    expr_vals[':tfd'] = Decimal(str(round(already_dispensed_kg, 2)))

                devices_table.update_item(
                    Key={'DeviceId': device_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeValues=expr_vals
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
                    'syncStatus': 'PENDING',
                    'settingsPushedAt': pushed_ist_str,
                    'settingsConfirmedAt': last_confirmed_at,
                    'pendingSettings': {
                        'dailyTarget_kg': float(feed_qty),
                        'feedPerEvent_g': int(feed_burst),
                        'startHour': int(shour),
                        'startMinute': int(smin),
                        'endHour': int(ehour),
                        'endMinute': int(emin)
                    },
                    'reportedSettings': {
                        'dailyTarget_kg': float(reported_qty),
                        'feedPerEvent_g': int(reported_fpe)
                    },
                    'calculated': {
                        'totalEvents': total_events,
                        'remainingEvents': remaining_events,
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
                    stored_target_ev = int(it.get('TargetEvents', 0))
                    fpe_val = float(dev_item.get('FeedPerEvent_g', 100)) if dev_item else 100.0
                    if fpe_val <= 0: fpe_val = 100.0
                    calc_tot_events = stored_target_ev if stored_target_ev > 0 else (math.ceil((t_kg * 1000.0) / fpe_val) if t_kg > 0 else 250)

                    db_by_date[d_date] = {
                        'DeviceId': it.get('DeviceId', device_id),
                        'Date': d_date,
                        'FeedDispensed_kg': feed_kg,
                        'Target_kg': t_kg,
                        'EventsCompleted': tot_cycles,
                        'TotalEvents': calc_tot_events,
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

            # Dynamic Available-Day History (CR-028 / REQ-219)
            # If the device has fewer than 15 days of history, show ONLY available days (don't force 15 days)
            try:
                max_window_days = int(query_params.get('days', 15))
            except:
                max_window_days = 15
            max_window_days = max(1, min(15, max_window_days))

            # Find earliest recorded feeding/metric date within the 15-day window
            cutoff_date_str = (today_ist - timedelta(days=max_window_days - 1)).strftime("%Y-%m-%d")
            active_dates_in_window = [
                d for d in db_by_date.keys()
                if d >= cutoff_date_str and (float(db_by_date[d].get('FeedDispensed_kg', 0)) > 0 or float(db_by_date[d].get('EventsCompleted', 0)) > 0)
            ]

            if active_dates_in_window:
                earliest_recorded_str = min(active_dates_in_window)
                try:
                    earliest_dt = datetime.strptime(earliest_recorded_str, "%Y-%m-%d").date()
                    available_days_count = (today_ist - earliest_dt).days + 1
                    num_days = min(max_window_days, max(1, available_days_count))
                except:
                    num_days = len(active_dates_in_window)
            elif is_today_live_event and live_dispensed_kg > 0:
                num_days = 1
            else:
                # No historical feed data in window: only show today
                num_days = 1

            rolling_days = []
            for i in range(num_days - 1, -1, -1):
                day_date = today_ist - timedelta(days=i)
                d_str = day_date.strftime("%Y-%m-%d")
                weekday_name = day_date.strftime("%a %m/%d")
                
                if d_str in db_by_date:
                    record = dict(db_by_date[d_str])
                    record['dateLabel'] = weekday_name
                    record['isToday'] = (i == 0)
                    rolling_days.append(record)
                elif i == 0 and is_today_live_event and live_dispensed_kg > 0:
                    rolling_days.append({
                        'DeviceId': device_id,
                        'Date': d_str,
                        'dateLabel': weekday_name,
                        'FeedDispensed_kg': live_dispensed_kg,
                        'Target_kg': base_qty,
                        'EventsCompleted': int(live_cur_ev),
                        'TotalEvents': math.ceil((base_qty * 1000.0) / fpe_val) if base_qty > 0 else 250,
                        'AdherencePct': round(min(100.0, (live_dispensed_kg / base_qty) * 100.0) if base_qty > 0 else 100.0, 1),
                        'isToday': True
                    })
                else:
                    rolling_days.append({
                        'DeviceId': device_id,
                        'Date': d_str,
                        'dateLabel': weekday_name,
                        'FeedDispensed_kg': 0.0,
                        'Target_kg': base_qty,
                        'EventsCompleted': 0,
                        'TotalEvents': math.ceil((base_qty * 1000.0) / fpe_val) if base_qty > 0 else 250,
                        'AdherencePct': 0.0,
                        'isToday': (i == 0)
                    })
                    
            return build_response(200, {
                'deviceId': device_id,
                'availableDays': len(rolling_days),
                'metrics': rolling_days
            })

        return build_response(404, {'error': f'Route {http_method} {path} not found'})

    except Exception as e:
        print("Exception in lambda_handler:", str(e))
        return build_response(500, {'error': str(e)})

import boto3

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
client = session.client('iotwireless')

gw_eui = '2cf7f11080100354'

# 1. Delete existing gateway if needed
gws = client.list_wireless_gateways()['WirelessGatewayList']
for g in gws:
    if g.get('LoRaWAN', {}).get('GatewayEui') == gw_eui:
        gw_id = g['Id']
        print(f"[INFO] Found existing gateway {gw_id} ({gw_eui}), deleting to re-create with IN865...")
        client.delete_wireless_gateway(Id=gw_id)
        print("[OK] Deleted existing gateway.")

# 2. Create Wireless Gateway with IN865
res_gw = client.create_wireless_gateway(
    Name='SenseCAP-M2-IN865',
    Description='SenseCAP M2 IN865 LoRaWAN Gateway',
    LoRaWAN={
        'GatewayEui': gw_eui,
        'RfRegion': 'IN865'
    }
)
new_gw_id = res_gw['Id']
gw_arn = res_gw['Arn']
print(f"[SUCCESS] Created IN865 Wireless Gateway! ID: {new_gw_id}")
print(f"  ARN: {gw_arn}")

# 3. Create or find Device Profile for IN865
dp_id = None
dps = client.list_device_profiles()['DeviceProfileList']
for dp in dps:
    if dp['Name'] == 'IN865-OTAA-DeviceProfile':
        dp_id = dp['Id']

if not dp_id:
    res_dp = client.create_device_profile(
        Name='IN865-OTAA-DeviceProfile',
        LoRaWAN={
            'SupportsClassB': False,
            'ClassBTimeout': 0,
            'SupportsClassC': False,
            'ClassCTimeout': 0,
            'MacVersion': '1.0.3',
            'RegParamsRevision': 'RP002-1.0.1',
            'RxDelay1': 1,
            'RxDrOffset1': 0,
            'RxDataRate2': 2,
            'RxFreq2': 866550000,
            'FactoryPresetFreqsList': [865062500, 865402500, 865985000]
        }
    )
    dp_id = res_dp['Id']
print(f"[OK] Device Profile ID: {dp_id}")

# 4. Create or find Service Profile
sp_id = None
sps = client.list_service_profiles()['ServiceProfileList']
for sp in sps:
    if sp['Name'] == 'IN865-ServiceProfile':
        sp_id = sp['Id']

if not sp_id:
    res_sp = client.create_service_profile(
        Name='IN865-ServiceProfile',
        LoRaWAN={'AddGwMetadata': True}
    )
    sp_id = res_sp['Id']
print(f"[OK] Service Profile ID: {sp_id}")

# 5. Check/Create Destination
dest_name = 'AquaFeederTelemetry'
dests = client.list_destinations()['DestinationList']
dest_found = any(d['Name'] == dest_name for d in dests)
if not dest_found:
    try:
        client.create_destination(
            Name=dest_name,
            ExpressionType='RuleName',
            Expression='AquaFeederTelemetryRule',
            Description='Destination for AquaFeeder telemetry payloads',
            RoleArn='arn:aws:iam::056580203662:role/service-role/IoTWirelessRuleRole'
        )
        print(f"[OK] Created Destination: {dest_name}")
    except Exception as e:
        dest_name = dests[0]['Name'] if dests else 'AquaFeederDestination'
        print(f"[NOTE] Using destination: {dest_name}")

# 6. Register Wireless Device AGV1-IN-2026-0001
dev_eui = 'E072A1F6249C0001'
app_eui = '0000000000000000'
app_key = '2B7E151628AED2A6ABF7158809CF4F3C'

devs = client.list_wireless_devices()['WirelessDeviceList']
for d in devs:
    d_info = client.get_wireless_device(Identifier=d['Id'], IdentifierType='WirelessDeviceId')
    if d_info.get('LoRaWAN', {}).get('DevEui', '').upper() == dev_eui:
        print(f"[INFO] Found existing device {d['Id']} ({d_info.get('Name')}), deleting to claim DevEUI...")
        client.delete_wireless_device(Id=d['Id'])

res_dev = client.create_wireless_device(
    Type='LoRaWAN',
    Name='AGV1-IN-2026-0001',
    Description='AquaFeeder AG_V1 Node IN865',
    DestinationName=dest_name,
    LoRaWAN={
        'DevEui': dev_eui,
        'DeviceProfileId': dp_id,
        'ServiceProfileId': sp_id,
        'OtaaV1_0_x': {
            'AppEui': app_eui,
            'AppKey': app_key
        }
    }
)
print(f"[SUCCESS] Registered Wireless Device AGV1-IN-2026-0001! ID: {res_dev['Id']}")

# Fetch CUPS & LNS Endpoints for Gateway configuration
cups_endpoint = client.get_service_endpoint(ServiceType='CUPS')['ServiceEndpoint']
lns_endpoint = client.get_service_endpoint(ServiceType='LNS')['ServiceEndpoint']

print("\n=======================================================")
print("=== AWS IOT WIRELESS IN865 SETUP COMPLETE ===")
print("=======================================================")
print(f"  Gateway EUI:         {gw_eui}")
print(f"  Gateway Region:      IN865")
print(f"  Device Name:         AGV1-IN-2026-0001")
print(f"  Device DevEUI:       {dev_eui}")
print(f"  Device AppKey:       {app_key}")
print(f"  CUPS Endpoint:       {cups_endpoint}")
print(f"  LNS Endpoint:        {lns_endpoint}")
print("=======================================================\n")

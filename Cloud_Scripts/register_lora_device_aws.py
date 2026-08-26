import boto3
import json

dev_eui = 'E072A1F6249C0001'
app_key = '2B7E151628AED2A6ABF7158809CF4F3C'
app_eui = '0000000000000000'
device_name = 'AGV1-IN-2026-0001'

print(f"[INFO] Checking / Registering Wireless Device {device_name} in AWS IoT Wireless...")

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iotwireless = session.client('iotwireless')

# 1. Device Profile for IN865
dp_id = None
dps = iotwireless.list_device_profiles()['DeviceProfileList']
for dp in dps:
    dp_info = iotwireless.get_device_profile(Id=dp['Id'])
    if dp_info.get('LoRaWAN', {}).get('RfRegion') == 'IN865':
        dp_id = dp['Id']
        print(f"[FOUND] Existing IN865 Device Profile: {dp_id}")
        break

if not dp_id:
    res_dp = iotwireless.create_device_profile(
        Name='IN865-Device-Profile',
        LoRaWAN={
            'RfRegion': 'IN865',
            'SupportsClassB': False,
            'SupportsClassC': False,
            'MacVersion': '1.0.3',
            'RegParamsRevision': 'RP001-1.0.3'
        }
    )
    dp_id = res_dp['Id']
    print(f"[CREATED] IN865 Device Profile: {dp_id}")

# 2. Service Profile
sp_id = None
sps = iotwireless.list_service_profiles()['ServiceProfileList']
if sps:
    sp_id = sps[0]['Id']
    print(f"[FOUND] Existing Service Profile: {sp_id}")
else:
    res_sp = iotwireless.create_service_profile(
        Name='AquaFeeder-Service-Profile',
        LoRaWAN={'AddGwMetadata': True}
    )
    sp_id = res_sp['Id']
    print(f"[CREATED] Service Profile: {sp_id}")

# 3. Clean up existing Wireless Device with same DevEUI or Name
devs = iotwireless.list_wireless_devices()['WirelessDeviceList']
for d in devs:
    if d.get('LoRaWAN', {}).get('DevEui') == dev_eui.lower() or d.get('Name') == device_name:
        print(f"[INFO] Removing old Wireless Device {d['Id']}...")
        iotwireless.delete_wireless_device(Id=d['Id'])

# 4. Create Wireless Device
res_dev = iotwireless.create_wireless_device(
    Type='LoRaWAN',
    Name=device_name,
    Description='AquaFeeder Smart Feeder Node 0001',
    DestinationName='AquaFeederDestination',
    LoRaWAN={
        'DevEui': dev_eui,
        'DeviceProfileId': dp_id,
        'ServiceProfileId': sp_id,
        'OtaaV1_0_x': {
            'AppKey': app_key,
            'AppEui': app_eui
        }
    }
)
dev_id = res_dev['Id']
dev_arn = res_dev['Arn']

print("\n=======================================================")
print("=== AWS IOT WIRELESS DEVICE REGISTRATION COMPLETE ===")
print("=======================================================")
print(f"  Device Name:      {device_name}")
print(f"  Device ID:        {dev_id}")
print(f"  DevEUI:           {dev_eui}")
print(f"  AppEUI (JoinEUI): {app_eui}")
print(f"  AppKey:           {app_key}")
print(f"  Region:           IN865")
print("=======================================================\n")

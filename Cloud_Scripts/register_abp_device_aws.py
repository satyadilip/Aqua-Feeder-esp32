import boto3
import json

dev_eui = 'E072A1F6249C0001'
device_name = 'AGV1-IN-2026-0001'
dev_addr = '0072A1F6'  # Derived from DevEUI
nwk_s_key = '2B7E151628AED2A6ABF7158809CF4F3C'
app_s_key = '2B7E151628AED2A6ABF7158809CF4F3C'

print(f"[INFO] Registering ABP Wireless Device {device_name} in AWS IoT Wireless...")

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iotwireless = session.client('iotwireless')

# 1. Create Device Profile for 1.0.3
res_dp = iotwireless.create_device_profile(
    Name='AquaFeeder-IN865-ABP-1.0.3',
    LoRaWAN={
        'MacVersion': '1.0.3',
        'RegParamsRevision': 'RP002-1.0.1',
        'MaxEirp': 14,
        'MaxDutyCycle': 100,
        'SupportsJoin': False,
        'RfRegion': 'IN865',
        'Supports32BitFCnt': True
    }
)
dp_id = res_dp['Id']
print(f"[USING] NEW IN865 ABP 1.0.3 Device Profile: {dp_id}")

# 2. Service Profile
sp_id = None
sps = iotwireless.list_service_profiles()['ServiceProfileList']
if sps:
    sp_id = sps[0]['Id']

# 3. Clean up existing Wireless Device with same DevEUI or Name
devs = iotwireless.list_wireless_devices()['WirelessDeviceList']
for d in devs:
    if d.get('LoRaWAN', {}).get('DevEui') == dev_eui.lower() or d.get('Name') == device_name:
        print(f"[INFO] Removing old Wireless Device {d['Id']}...")
        iotwireless.delete_wireless_device(Id=d['Id'])

# 4. Create ABP Wireless Device
res_dev = iotwireless.create_wireless_device(
    Type='LoRaWAN',
    Name=device_name,
    Description='AquaFeeder Smart Feeder ABP Node',
    DestinationName='AquaFeederDestination',
    LoRaWAN={
        'DevEui': dev_eui,
        'DeviceProfileId': dp_id,
        'ServiceProfileId': sp_id,
        'AbpV1_0_x': {
            'DevAddr': dev_addr,
            'SessionKeys': {
                'NwkSKey': nwk_s_key,
                'AppSKey': app_s_key
            }
        }
    }
)
dev_id = res_dev['Id']

print("\n=======================================================")
print("=== AWS IOT WIRELESS ABP DEVICE REGISTRATION COMPLETE ===")
print("=======================================================")
print(f"  Device Name:  {device_name}")
print(f"  Device ID:    {dev_id}")
print(f"  DevEUI:       {dev_eui}")
print(f"  DevAddr:      {dev_addr}")
print(f"  NwkSKey:      {nwk_s_key}")
print(f"  AppSKey:      {app_s_key}")
print("=======================================================\n")

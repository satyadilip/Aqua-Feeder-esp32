import boto3
import json

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)

iotwireless = session.client('iotwireless')

gw_id = '680a7b22-89d0-4744-8f01-6d4131d3bbe0'
dev_id = 'da30e35b-8dbf-4983-8b9c-a9d9c2a575bd'

print("=== AWS CLOUD STATUS CHECK ===")
try:
    gw_stat = iotwireless.get_wireless_gateway_statistics(WirelessGatewayId=gw_id)
    print("  Gateway Conn Status: ", gw_stat.get('ConnectionStatus'))
    print("  Gateway Last Uplink: ", gw_stat.get('LastUplinkReceivedAt'))
except Exception as e:
    print("  Gateway error:", e)

# Find wireless device ID dynamically
devs = iotwireless.list_wireless_devices()['WirelessDeviceList']
dev_id = None
for d in devs:
    if d.get('Name') == 'AGV1-IN-2026-0001':
        dev_id = d['Id']
        print(f"  Found Active Wireless Device ID: {dev_id} (Type: {d.get('LoRaWAN', {}).get('DevEui') or 'ABP'})")
        break

if dev_id:
    try:
        dev_stat = iotwireless.get_wireless_device_statistics(WirelessDeviceId=dev_id)
        print("  Node Last Uplink:    ", dev_stat.get('LastUplinkReceivedAt'))
        print("  LoRaWAN Frame Counter:", dev_stat.get('LoRaWAN', {}).get('FCnt'))
    except Exception as e:
        print("  Dev error:", e)
else:
    print("  No matching device found!")

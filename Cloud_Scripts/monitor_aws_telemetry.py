import boto3
import time

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iotwireless = session.client('iotwireless')

gw_id = '361c4980-a356-4145-9ae5-a5e23212b628'
dev_id = '6e59f52a-c68f-4111-8680-97a34e9dde1e'

print("=== AWS IOT WIRELESS TELEMETRY MONITOR ===")
print(f"  Gateway ID: {gw_id}")
print(f"  Device ID:  {dev_id}")
print("==========================================\n")

for i in range(10):
    try:
        gw_stat = iotwireless.get_wireless_gateway_statistics(WirelessGatewayId=gw_id)
        dev_stat = iotwireless.get_wireless_device_statistics(WirelessDeviceId=dev_id)
        
        conn = gw_stat.get('ConnectionStatus', 'UNKNOWN')
        last_gw_up = gw_stat.get('LastUplinkReceivedAt', 'None')
        last_dev_up = dev_stat.get('LastUplinkReceivedAt', 'None')
        
        print(f"[{i+1}/10] Gateway Conn: {conn} | GW Last Uplink: {last_gw_up} | Node Last Uplink: {last_dev_up}")
    except Exception as e:
        print(f"[{i+1}/10] Error: {e}")
    time.sleep(3)

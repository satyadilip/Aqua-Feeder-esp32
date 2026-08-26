import boto3
import time

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iotwireless = session.client('iotwireless')

dev_id = '2255b5ae-4e11-49af-8227-0da6b3c97fcf'
gw_id = '680a7b22-89d0-4744-8f01-6d4131d3bbe0'

print("=== MONITORING LIVE LORAWAN CLOUD TELEMETRY ROUTING ===")
for i in range(10):
    gw_stat = iotwireless.get_wireless_gateway_statistics(WirelessGatewayId=gw_id)
    dev_stat = iotwireless.get_wireless_device_statistics(WirelessDeviceId=dev_id)
    
    gw_up = gw_stat.get('LastUplinkReceivedAt', 'None')
    dev_up = dev_stat.get('LastUplinkReceivedAt', 'None')
    
    print(f"[{i+1}/10] Gateway Last Uplink: {gw_up} | Device Last Uplink: {dev_up}")
    time.sleep(2)

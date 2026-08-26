import boto3
import time

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iotwireless = session.client('iotwireless')

dev_id = 'da30e35b-8dbf-4983-8b9c-a9d9c2a575bd'
gw_id = '680a7b22-89d0-4744-8f01-6d4131d3bbe0'

print("=== MONITORING LIVE AWS LORAWAN CLOUD UPLINKS ===")
for i in range(12):
    gw_stat = iotwireless.get_wireless_gateway_statistics(WirelessGatewayId=gw_id)
    dev_stat = iotwireless.get_wireless_device_statistics(WirelessDeviceId=dev_id)
    
    gw_up = gw_stat.get('LastUplinkReceivedAt', 'None')
    dev_up = dev_stat.get('LastUplinkReceivedAt', 'None')
    
    print(f"[{i+1}/12] Gateway Last Uplink: {gw_up} | Node Last Uplink: {dev_up}")
    time.sleep(2)

import boto3

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iotwireless = session.client('iotwireless')

dev_id = '2255b5ae-4e11-49af-8227-0da6b3c97fcf'

print("=== CHECKING WIRELESS DEVICE DESTINATION ===")
dev_info = iotwireless.get_wireless_device(Identifier=dev_id, IdentifierType='WirelessDeviceId')
print("Destination Name:", dev_info.get('DestinationName'))

print("\n=== LISTING ALL DESTINATIONS ===")
dests = iotwireless.list_destinations()['DestinationList']
for d in dests:
    print(f"  Name: {d.get('Name')} | ExpressionType: {d.get('ExpressionType')} | Expression: {d.get('Expression')}")

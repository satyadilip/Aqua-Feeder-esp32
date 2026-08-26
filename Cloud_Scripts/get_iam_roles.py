import boto3

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iam = session.client('iam')
iotwireless = session.client('iotwireless')

print("=== CHECKING EXISTING DESTINATIONS WITH ROLEARN ===")
dests = iotwireless.list_destinations()['DestinationList']
for d in dests:
    info = iotwireless.get_destination(Name=d['Name'])
    print(f"  Name: {d['Name']} | RoleArn: {info.get('RoleArn')} | Expression: {info.get('Expression')}")

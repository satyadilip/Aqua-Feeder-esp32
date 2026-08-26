import boto3

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
ddb = session.resource('dynamodb')

devices = ddb.Table('AquaFeeder_Devices').scan().get('Items', [])
telemetry = ddb.Table('AquaFeeder_Telemetry').scan().get('Items', [])
daily = ddb.Table('AquaFeeder_DailyMetrics').scan().get('Items', [])
settings = ddb.Table('AquaFeeder_Settings').scan().get('Items', [])

print("=== DEVICES ===")
for d in devices:
    print(d)

print("\n=== TELEMETRY ===")
for t in telemetry:
    print(t)

print("\n=== DAILY METRICS ===")
for d in daily:
    print(d)
    
print("\n=== SETTINGS ===")
for s in settings:
    print(s)

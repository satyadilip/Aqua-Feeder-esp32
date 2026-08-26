import boto3
import time

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
client = session.client('logs')

log_group = '/aws/lambda/AquaFeederTelemetryProcessor'

try:
    logs = client.filter_log_events(
        logGroupName=log_group, 
        startTime=int((time.time() - 3600) * 1000)
    )
    events = logs.get('events', [])
    if not events:
        print("No logs found for AquaFeederTelemetryProcessor in the last hour.")
    else:
        for e in events:
            print(e['message'].strip())
except Exception as e:
    print(f"Error reading logs: {e}")

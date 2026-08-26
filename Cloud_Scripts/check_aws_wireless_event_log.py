import boto3
import json

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)

iotwireless = session.client('iotwireless')

dev_id = 'f3c812c5-ea79-4c04-bd3f-964f6945be3e'

print("=== CHECKING DEVICE EVENT LOG CONFIG ===")
try:
    log_cfg = iotwireless.get_event_configuration_by_resource_types()
    print("Event Configuration:", json.dumps(log_cfg, indent=2, default=str))
except Exception as e:
    print("Error:", e)

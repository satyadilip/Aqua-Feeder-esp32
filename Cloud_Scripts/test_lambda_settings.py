import boto3
import json
import base64
import struct

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
lambda_client = session.client('lambda')

# Payload: msgType(1), feedQuantity_g(4), feedPerEvent_g(2), feedTime_h(1), startHour(1), startMinute(1), dischargeRate(2)
# SETTINGS_REPORT = 0x22
# feedQuantity_g = 10000 (10kg)
# feedPerEvent_g = 100 (100g)
# feedTime_h = 2 (2 hours)
# startHour = 8
# startMinute = 30
# dischargeRate = 50 (50g/s)
payload_bytes = struct.pack('<BIHBBBH', 0x22, 10000, 100, 2, 8, 30, 50)
payload_b64 = base64.b64encode(payload_bytes).decode('utf-8')

test_event = {
    "MessageId": "test-msg-id",
    "WirelessDeviceId": "f678a4f1-6d71-4dd0-8de0-ada0e7c1d655",
    "PayloadData": payload_b64,
    "WirelessMetadata": {
        "LoRaWAN": {
            "DevEui": "e072a1f6249c0001",
            "Timestamp": "2026-08-25T18:00:00Z"
        }
    }
}

response = lambda_client.invoke(
    FunctionName='AquaFeederTelemetryProcessor',
    InvocationType='RequestResponse',
    Payload=json.dumps(test_event)
)

print(response['Payload'].read().decode('utf-8'))

import boto3

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iotwireless = session.client('iotwireless')

dev_id = '2255b5ae-4e11-49af-8227-0da6b3c97fcf'

role_arn = 'arn:aws:iam::056580203662:role/AWSLoRaWirelessDestinationRole'

print("[INFO] Updating AWS IoT Wireless Destination AquaFeederDestination...")
try:
    iotwireless.update_destination(
        Name='AquaFeederDestination',
        ExpressionType='MqttTopic',
        Expression='aqua/feeder/telemetry',
        RoleArn=role_arn,
        Description='AquaFeeder live LoRaWAN telemetry destination'
    )
    print("[SUCCESS] Destination AquaFeederDestination set to MqttTopic: 'aqua/feeder/telemetry'")
except Exception as e:
    print("[ERROR] Update destination failed:", e)

try:
    iotwireless.update_wireless_device(
        Id=dev_id,
        DestinationName='AquaFeederDestination'
    )
    print("[SUCCESS] Wireless Device AGV1-IN-2026-0001 bound to AquaFeederDestination!")
except Exception as e:
    print("[ERROR] Update wireless device failed:", e)

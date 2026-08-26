import boto3
import json
import time
import zipfile
import os

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)

dynamodb = session.client('dynamodb')
iam = session.client('iam')
lambda_client = session.client('lambda')
iot = session.client('iot')

print("=== AquaFeeder AWS Backend Provisioning ===")

# 1. Create DynamoDB Tables
def create_table(table_name, key_schema, attribute_definitions):
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"Creating table {table_name}...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        print(f"Table {table_name} created successfully.")
    except dynamodb.exceptions.ResourceInUseException:
        print(f"Table {table_name} already exists.")

create_table(
    'AquaFeeder_Devices',
    [{'AttributeName': 'DeviceId', 'KeyType': 'HASH'}],
    [{'AttributeName': 'DeviceId', 'AttributeType': 'S'}]
)

create_table(
    'AquaFeeder_Telemetry',
    [{'AttributeName': 'DeviceId', 'KeyType': 'HASH'}, {'AttributeName': 'Timestamp', 'KeyType': 'RANGE'}],
    [{'AttributeName': 'DeviceId', 'AttributeType': 'S'}, {'AttributeName': 'Timestamp', 'AttributeType': 'N'}]
)

# 2. Create IAM Role for Lambda
role_name = 'AquaFeederLambdaRole'
assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [{"Action": "sts:AssumeRole", "Principal": {"Service": "lambda.amazonaws.com"}, "Effect": "Allow"}]
}

try:
    role_response = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(assume_role_policy)
    )
    print(f"Created IAM Role: {role_name}")
    time.sleep(10) # Wait for role to propagate
except iam.exceptions.EntityAlreadyExistsException:
    print(f"IAM Role {role_name} already exists.")
    role_response = iam.get_role(RoleName=role_name)

role_arn = role_response['Role']['Arn']

# Attach DynamoDB and CloudWatch policies
iam.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess')
iam.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole')
print("Attached policies to IAM Role.")

# 3. Create Lambda Function code
lambda_code = """
import json
import base64
import boto3
import struct
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
telemetry_table = dynamodb.Table('AquaFeeder_Telemetry')
devices_table = dynamodb.Table('AquaFeeder_Devices')

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    try:
        # AWS IoT Wireless puts base64 payload in 'PayloadData'
        payload_b64 = event.get('PayloadData')
        wireless_metadata = event.get('WirelessMetadata', {})
        lorawan_metadata = wireless_metadata.get('LoRaWAN', {})
        dev_eui = lorawan_metadata.get('DevEui', 'UNKNOWN_DEVICE')
        
        if not payload_b64:
            print("No payload data found")
            return
            
        payload_bytes = base64.b64decode(payload_b64)
        
        # Parse 15-byte struct: msgType(1), timestamp(4), voltage(2), current(2), feed(2), curEv(1), totEv(1), status(1), rsvd(1)
        if len(payload_bytes) >= 15:
            unpacked = struct.unpack('<BIHHHHBBB', payload_bytes[:15])
            msg_type = unpacked[0]
            timestamp = unpacked[1]
            voltage = unpacked[2]
            current = unpacked[3]
            feed_disp = unpacked[4]
            cur_ev = unpacked[5]
            tot_ev = unpacked[6]
            status_flags = unpacked[7]
            
            # Store in Telemetry table
            telemetry_table.put_item(
                Item={
                    'DeviceId': dev_eui,
                    'Timestamp': Decimal(str(timestamp)),
                    'MsgType': msg_type,
                    'Voltage_mV': Decimal(str(voltage)),
                    'Current_mA': Decimal(str(current)),
                    'FeedDispensed_g': Decimal(str(feed_disp)),
                    'CurrentEvent': cur_ev,
                    'TotalEvents': tot_ev,
                    'StatusFlags': status_flags
                }
            )
            
            # Update Devices table with latest status
            devices_table.put_item(
                Item={
                    'DeviceId': dev_eui,
                    'LastSeen': Decimal(str(timestamp)),
                    'LastVoltage_mV': Decimal(str(voltage)),
                    'LastCurrent_mA': Decimal(str(current)),
                    'LastFeed_g': Decimal(str(feed_disp)),
                    'CurrentEvent': cur_ev,
                    'TotalEvents': tot_ev,
                    'StatusFlags': status_flags
                }
            )
            print(f"Successfully processed and stored telemetry for device {dev_eui}")
        else:
            print(f"Payload too small: {len(payload_bytes)} bytes")
            
    except Exception as e:
        print(f"Error processing payload: {e}")
        raise e
"""

with open('lambda_function.py', 'w') as f:
    f.write(lambda_code)

with zipfile.ZipFile('lambda_function.zip', 'w') as z:
    z.write('lambda_function.py')

func_name = 'AquaFeederTelemetryProcessor'
try:
    print(f"Creating Lambda Function {func_name}...")
    time.sleep(5) # Wait for role propagation
    lambda_response = lambda_client.create_function(
        FunctionName=func_name,
        Runtime='python3.11',
        Role=role_arn,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': open('lambda_function.zip', 'rb').read()},
        Timeout=15
    )
    func_arn = lambda_response['FunctionArn']
    print(f"Created Lambda function: {func_arn}")
except lambda_client.exceptions.ResourceConflictException:
    print(f"Lambda function {func_name} already exists. Updating code...")
    lambda_client.update_function_code(
        FunctionName=func_name,
        ZipFile=open('lambda_function.zip', 'rb').read()
    )
    func_arn = lambda_client.get_function(FunctionName=func_name)['Configuration']['FunctionArn']
    print(f"Updated Lambda function: {func_arn}")

# 4. Create IoT Rule
rule_name = 'AquaFeederTelemetryRule'
topic = 'aqua/feeder/telemetry'

try:
    # Need to give IoT Core permission to invoke the Lambda
    lambda_client.add_permission(
        FunctionName=func_name,
        StatementId='IoTRuleInvokeAccess',
        Action='lambda:InvokeFunction',
        Principal='iot.amazonaws.com'
    )
    print("Granted IoT permission to invoke Lambda")
except lambda_client.exceptions.ResourceConflictException:
    print("IoT permission to invoke Lambda already exists")

rule_payload = {
    'sql': f"SELECT * FROM '{topic}'",
    'actions': [{'lambda': {'functionArn': func_arn}}],
    'ruleDisabled': False
}

try:
    iot.create_topic_rule(
        ruleName=rule_name,
        topicRulePayload=rule_payload
    )
    print(f"Created IoT Core Rule: {rule_name}")
except iot.exceptions.ResourceAlreadyExistsException:
    iot.replace_topic_rule(
        ruleName=rule_name,
        topicRulePayload=rule_payload
    )
    print(f"Updated IoT Core Rule: {rule_name}")

print("=== Backend Provisioning Complete! ===")

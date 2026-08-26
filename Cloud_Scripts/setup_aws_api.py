import boto3
import json
import time
import zipfile

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)

iam = session.client('iam')
lambda_client = session.client('lambda')

print("=== AquaFeeder AWS API Provisioning ===")

role_name = 'AquaFeederLambdaRole'
role_arn = iam.get_role(RoleName=role_name)['Role']['Arn']

# Create Lambda Function code for API
lambda_code = """
import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
devices_table = dynamodb.Table('AquaFeeder_Devices')
telemetry_table = dynamodb.Table('AquaFeeder_Telemetry')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,GET',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    path = event.get('path', '')
    
    if path == '/api/devices':
        response = devices_table.scan()
        return build_response(200, {'devices': response.get('Items', [])})
        
    elif path.startswith('/api/telemetry/'):
        # /api/telemetry/{deviceId}
        device_id = path.split('/')[-1]
        
        # We can add query params for time range, for now just query last 100 items
        response = telemetry_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('DeviceId').eq(device_id),
            ScanIndexForward=False, # Descending order by Timestamp
            Limit=100
        )
        return build_response(200, {'telemetry': response.get('Items', [])})
        
    return build_response(404, {'error': 'Not Found'})
"""

with open('api_lambda.py', 'w') as f:
    f.write(lambda_code)

with zipfile.ZipFile('api_lambda.zip', 'w') as z:
    z.write('api_lambda.py')

func_name = 'AquaFeederApiHandler'
try:
    print(f"Creating Lambda Function {func_name}...")
    lambda_response = lambda_client.create_function(
        FunctionName=func_name,
        Runtime='python3.11',
        Role=role_arn,
        Handler='api_lambda.lambda_handler',
        Code={'ZipFile': open('api_lambda.zip', 'rb').read()},
        Timeout=15
    )
    func_arn = lambda_response['FunctionArn']
    print(f"Created API Lambda function: {func_arn}")
except lambda_client.exceptions.ResourceConflictException:
    print(f"Lambda function {func_name} already exists. Updating code...")
    lambda_client.update_function_code(
        FunctionName=func_name,
        ZipFile=open('api_lambda.zip', 'rb').read()
    )
    func_arn = lambda_client.get_function(FunctionName=func_name)['Configuration']['FunctionArn']
    print(f"Updated API Lambda function: {func_arn}")

# API Gateway provision using boto3 can be complex (creating REST API, resources, methods, integrations, deployments, etc.)
# A simpler approach is to create a Function URL!
print("Creating Function URL for API...")
try:
    url_response = lambda_client.create_function_url_config(
        FunctionName=func_name,
        AuthType='NONE',
        Cors={
            'AllowOrigins': ['*'],
            'AllowMethods': ['*'],
            'AllowHeaders': ['*']
        }
    )
    api_url = url_response['FunctionUrl']
    
    # Add permission for public access
    lambda_client.add_permission(
        FunctionName=func_name,
        StatementId='FunctionURLAllowPublicAccess',
        Action='lambda:InvokeFunctionUrl',
        Principal='*',
        FunctionUrlAuthType='NONE'
    )
except lambda_client.exceptions.ResourceConflictException:
    # URL already exists
    url_response = lambda_client.get_function_url_config(FunctionName=func_name)
    api_url = url_response['FunctionUrl']

print(f"=== Backend API Provisioning Complete! ===")
print(f"API URL: {api_url}")

import boto3
import zipfile
import os

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
lambda_client = session.client('lambda')

zip_file = "lambda_function.zip"
with zipfile.ZipFile(zip_file, 'w') as z:
    z.write('lambda_function.py')

with open(zip_file, 'rb') as f:
    zipped_code = f.read()

print("Updating Lambda function code...")
response = lambda_client.update_function_code(
    FunctionName='AquaFeederTelemetryProcessor',
    ZipFile=zipped_code
)
print("Updated! RevisionId:", response['RevisionId'])

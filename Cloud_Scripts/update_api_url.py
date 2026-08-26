import boto3

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
lambda_client = session.client('lambda')

func_name = 'AquaFeederApiHandler'

print("Updating Function URL Config...")
res = lambda_client.update_function_url_config(
    FunctionName=func_name,
    AuthType='NONE',
    Cors={
        'AllowOrigins': ['*'],
        'AllowMethods': ['*'],
        'AllowHeaders': ['*']
    }
)
print("Updated config:", res['FunctionUrl'])

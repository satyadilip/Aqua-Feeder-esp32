import boto3

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
lambda_client = session.client('lambda')

func_name = 'AquaFeederApiHandler'

try:
    lambda_client.add_permission(
        FunctionName=func_name,
        StatementId='FunctionURLAllowPublicAccess2',
        Action='lambda:InvokeFunctionUrl',
        Principal='*',
        FunctionUrlAuthType='NONE'
    )
    print("Successfully added public permission!")
except lambda_client.exceptions.ResourceConflictException:
    print("Permission already exists.")
except Exception as e:
    print(f"Error: {e}")

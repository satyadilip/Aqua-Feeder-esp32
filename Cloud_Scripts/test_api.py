import boto3
import urllib.request
import urllib.error

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
lambda_client = session.client('lambda')

print(lambda_client.get_policy(FunctionName='AquaFeederApiHandler')['Policy'])

try:
    print(urllib.request.urlopen('https://vl6lwnkimuef3bsry5sb7bxc7i0lzokn.lambda-url.us-east-1.on.aws/api/devices').read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.read().decode('utf-8'))


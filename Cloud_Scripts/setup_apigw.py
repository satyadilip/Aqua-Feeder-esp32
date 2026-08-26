import boto3

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
apigw = session.client('apigateway')
lambda_client = session.client('lambda')

func_name = 'AquaFeederApiHandler'
func_arn = lambda_client.get_function(FunctionName=func_name)['Configuration']['FunctionArn']

# 1. Create REST API
api = apigw.create_rest_api(Name='AquaFeederAPI', EndpointConfiguration={'types': ['REGIONAL']})
api_id = api['id']
root_id = apigw.get_resources(restApiId=api_id)['items'][0]['id']

# 2. Create proxy resource
proxy = apigw.create_resource(restApiId=api_id, parentId=root_id, pathPart='{proxy+}')
proxy_id = proxy['id']

# 3. Create ANY method
apigw.put_method(restApiId=api_id, resourceId=proxy_id, httpMethod='ANY', authorizationType='NONE')

# 4. Create Integration
apigw.put_integration(
    restApiId=api_id,
    resourceId=proxy_id,
    httpMethod='ANY',
    type='AWS_PROXY',
    integrationHttpMethod='POST',
    uri=f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{func_arn}/invocations"
)

# 5. Add permission to Lambda
try:
    lambda_client.add_permission(
        FunctionName=func_name,
        StatementId='ApiGatewayInvoke',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f"arn:aws:execute-api:us-east-1:{func_arn.split(':')[4]}:{api_id}/*/*/*"
    )
except:
    pass

# 6. Deploy API
apigw.create_deployment(restApiId=api_id, stageName='prod')

api_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod"
print(f"API Gateway URL: {api_url}")

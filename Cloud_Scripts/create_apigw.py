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

api = apigw.create_rest_api(name='AquaFeederAPI', endpointConfiguration={'types': ['REGIONAL']})
api_id = api['id']
root_id = apigw.get_resources(restApiId=api_id)['items'][0]['id']

proxy = apigw.create_resource(restApiId=api_id, parentId=root_id, pathPart='{proxy+}')
proxy_id = proxy['id']

apigw.put_method(restApiId=api_id, resourceId=proxy_id, httpMethod='ANY', authorizationType='NONE')
apigw.put_integration(
    restApiId=api_id,
    resourceId=proxy_id,
    httpMethod='ANY',
    type='AWS_PROXY',
    integrationHttpMethod='POST',
    uri=f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{func_arn}/invocations"
)

# Also create ANY on root /
apigw.put_method(restApiId=api_id, resourceId=root_id, httpMethod='ANY', authorizationType='NONE')
apigw.put_integration(
    restApiId=api_id,
    resourceId=root_id,
    httpMethod='ANY',
    type='AWS_PROXY',
    integrationHttpMethod='POST',
    uri=f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{func_arn}/invocations"
)

try:
    lambda_client.add_permission(
        FunctionName=func_name,
        StatementId='ApiGatewayInvoke2',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f"arn:aws:execute-api:us-east-1:056580203662:{api_id}/*/*"
    )
except Exception as e:
    print(e)

apigw.create_deployment(restApiId=api_id, stageName='prod')

print(f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod")

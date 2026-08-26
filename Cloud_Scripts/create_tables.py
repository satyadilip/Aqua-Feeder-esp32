import boto3
import time

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
dynamodb = session.client('dynamodb')

def create_table_if_not_exists(table_name, key_schema, attribute_definitions):
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
        print(f"Table {table_name} created successfully!")
    except dynamodb.exceptions.ResourceInUseException:
        print(f"Table {table_name} already exists.")

create_table_if_not_exists(
    'AquaFeeder_DailyMetrics',
    [{'AttributeName': 'DeviceId', 'KeyType': 'HASH'}, {'AttributeName': 'Date', 'KeyType': 'RANGE'}],
    [{'AttributeName': 'DeviceId', 'AttributeType': 'S'}, {'AttributeName': 'Date', 'AttributeType': 'S'}]
)

create_table_if_not_exists(
    'AquaFeeder_Settings',
    [{'AttributeName': 'DeviceId', 'KeyType': 'HASH'}],
    [{'AttributeName': 'DeviceId', 'AttributeType': 'S'}]
)


import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
devices_table = dynamodb.Table('AquaFeeder_Devices')
telemetry_table = dynamodb.Table('AquaFeeder_Telemetry')
settings_table = dynamodb.Table('AquaFeeder_Settings')
metrics_table = dynamodb.Table('AquaFeeder_DailyMetrics')

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
    try:
        path = event.get('path', '')
        
        if path == '/api/devices':
            response = devices_table.scan()
            # Sort devices by LastSeen desc
            devices = response.get('Items', [])
            devices.sort(key=lambda x: x.get('LastSeen', 0), reverse=True)
            return build_response(200, {'devices': devices})
            
        elif path.startswith('/api/telemetry/'):
            device_id = path.split('/')[-1]
            response = telemetry_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('DeviceId').eq(device_id),
                ScanIndexForward=False,
                Limit=100
            )
            return build_response(200, {'telemetry': response.get('Items', [])})
            
        elif path.startswith('/api/settings/'):
            device_id = path.split('/')[-1]
            response = settings_table.get_item(Key={'DeviceId': device_id})
            return build_response(200, {'settings': response.get('Item', None)})
            
        elif path.startswith('/api/metrics/'):
            device_id = path.split('/')[-1]
            response = metrics_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('DeviceId').eq(device_id),
                ScanIndexForward=False,
                Limit=30 # Last 30 days
            )
            return build_response(200, {'metrics': response.get('Items', [])})
            
        return build_response(404, {'error': 'Not Found'})
    except Exception as e:
        print(e)
        return build_response(500, {'error': str(e)})

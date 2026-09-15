import boto3
import zipfile

session = boto3.Session(region_name='us-east-1')
lambda_client = session.client('lambda')

lambda_code = """
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
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
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
            # Handle Function URL payload format 2.0
            method = event.get('requestContext', {}).get('http', {}).get('method', '')
            
            if method == 'POST':
                try:
                    body = json.loads(event.get('body', '{}'))
                    feed_qty = int(float(body.get('feedQuantity', 0)) * 10)
                    feed_per = int(body.get('feedPerEvent', 0))
                    feed_time = int(body.get('feedTime', 0))
                    start_hr = int(body.get('startHour', 0))
                    start_min = int(body.get('startMinute', 0))
                    discharge = int(body.get('dischargeRate', 0))
                    
                    import struct
                    import base64
                    # Pack 12 bytes: msgType(0xA0), pad(1), feedQty(2), feedPer(2), feedTime(1), startHr(1), startMin(1), discharge(1), rsvd(2)
                    payload_bytes = struct.pack('<BBHHBBBBH', 0xA0, 0, feed_qty, feed_per, feed_time, start_hr, start_min, discharge, 0)
                    b64_payload = base64.b64encode(payload_bytes).decode('utf-8')
                    
                    try:
                        iotwireless = boto3.client('iotwireless')
                        dev_res = iotwireless.get_wireless_device(Identifier=device_id, IdentifierType='DevEui')
                        wireless_id = dev_res['Id']
                        
                        iotwireless.send_data_to_wireless_device(
                            Id=wireless_id,
                            TransmitMode=0,
                            PayloadData=b64_payload,
                            WirelessMetadata={'LoRaWAN': {'FPort': 2}}
                        )
                    except Exception as e:
                        print(f"LoRa Downlink skipped/failed: {str(e)}")
                    
                    try:
                        iot_data = boto3.client('iot-data')
                        iot_data.publish(
                            topic=f'aquafeeder/{device_id}/downlink',
                            qos=1,
                            payload=json.dumps({'action': 'set_settings', 'settings': body})
                        )
                    except Exception as e:
                        print(f"MQTT Downlink skipped/failed: {str(e)}")
                        
                    return build_response(200, {'message': 'Downlink queued successfully'})
                except Exception as e:
                    return build_response(500, {'error': f'Failed to queue downlink: {str(e)}'})
            else:
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
"""

with open('api_lambda.py', 'w') as f:
    f.write(lambda_code)

with zipfile.ZipFile('api_lambda.zip', 'w') as z:
    z.write('api_lambda.py')

func_name = 'AquaFeederApiHandler'
print("Updating Lambda function code...")
response = lambda_client.update_function_code(
    FunctionName=func_name,
    ZipFile=open('api_lambda.zip', 'rb').read()
)
print("Updated! RevisionId:", response['RevisionId'])

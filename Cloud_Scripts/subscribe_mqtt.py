import boto3
import time
import json
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iot = session.client('iot')
endpoint = iot.describe_endpoint(endpointType='iot:Data-ATS')['endpointAddress']

def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print(f"Received message from topic '{topic}':")
    print(payload.decode('utf-8'))

event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
credentials_provider = auth.AwsCredentialsProvider.new_static(
    access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY'
)

mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
    endpoint=endpoint,
    client_bootstrap=client_bootstrap,
    region='us-east-1',
    credentials_provider=credentials_provider,
    clean_session=True,
    keep_alive_secs=30,
    client_id='test-sub-' + str(int(time.time()))
)

print(f"Connecting to {endpoint}...")
connect_future = mqtt_connection.connect()
connect_future.result()
print("Connected!")

mqtt_connection.subscribe(
    topic="$aws/iotwireless/#",
    qos=mqtt.QoS.AT_LEAST_ONCE,
    callback=on_message_received
)
mqtt_connection.subscribe(
    topic="aqua/feeder/telemetry",
    qos=mqtt.QoS.AT_LEAST_ONCE,
    callback=on_message_received
)

print("Subscribed to all IoT topics. Waiting for 30 seconds...")
time.sleep(30)
mqtt_connection.disconnect().result()
print("Disconnected.")

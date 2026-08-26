import boto3
import json

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iot = session.client('iot')
iotwireless = session.client('iotwireless')

gw_id = 'ff38400a-d797-4fdf-8fd5-0f0f6ef0ec4b'
thing_name = 'SenseCAP_M2_IN865_Gateway'

print(f"[INFO] Configuring AWS IoT Certificate for Gateway {gw_id}...")

# 1. Create IoT Thing if it doesn't exist
try:
    thing = iot.describe_thing(thingName=thing_name)
    thing_arn = thing['thingArn']
    print(f"[OK] Found existing IoT Thing: {thing_name}")
except iot.exceptions.ResourceNotFoundException:
    thing = iot.create_thing(thingName=thing_name)
    thing_arn = thing['thingArn']
    print(f"[SUCCESS] Created IoT Thing: {thing_name}")

# 2. Create Keys and Certificate
cert_res = iot.create_keys_and_certificate(setAsActive=True)
cert_arn = cert_res['certificateArn']
cert_id = cert_res['certificateId']
cert_pem = cert_res['certificatePem']
priv_key = cert_res['keyPair']['PrivateKey']

print(f"[SUCCESS] Created Certificate ID: {cert_id}")

# 3. Create IoT Policy for Wireless Gateway if not exists
policy_name = 'WirelessGatewayPolicy'
policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iot:Connect",
                "iot:Subscribe",
                "iot:Publish",
                "iot:Receive",
                "iotwireless:*"
            ],
            "Resource": "*"
        }
    ]
}

try:
    iot.get_policy(policyName=policy_name)
    print(f"[OK] Found existing IoT Policy: {policy_name}")
except iot.exceptions.ResourceNotFoundException:
    iot.create_policy(
        policyName=policy_name,
        policyDocument=json.dumps(policy_document)
    )
    print(f"[SUCCESS] Created IoT Policy: {policy_name}")

# Attach policy to certificate & attach certificate to thing
iot.attach_policy(policyName=policy_name, target=cert_arn)
iot.attach_thing_principal(thingName=thing_name, principal=cert_arn)
print("[OK] Attached Policy and Thing to Certificate.")

# 4. Associate Wireless Gateway with Thing
iotwireless.associate_wireless_gateway_with_thing(
    Id=gw_id,
    ThingArn=thing_arn
)
print(f"[SUCCESS] Associated Wireless Gateway {gw_id} with Thing {thing_name}!")

# 5. Fetch Amazon Root CA 1
import urllib.request
root_ca_url = 'https://www.amazontrust.com/repository/AmazonRootCA1.pem'
root_ca = urllib.request.urlopen(root_ca_url).read().decode('utf-8')

# Save certificate files for SenseCAP M2
with open('c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/cups.crt', 'w') as f:
    f.write(cert_pem)
with open('c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/cups.key', 'w') as f:
    f.write(priv_key)
with open('c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/cups.trust', 'w') as f:
    f.write(root_ca)

with open('c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/tc.crt', 'w') as f:
    f.write(cert_pem)
with open('c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/tc.key', 'w') as f:
    f.write(priv_key)
with open('c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/tc.trust', 'w') as f:
    f.write(root_ca)

print("\n=======================================================")
print("=== GATEWAY CERTIFICATES GENERATED SUCCESSFULLY ===")
print("=======================================================")
print("  Client Certificate File: cups.crt / tc.crt")
print("  Private Key File:        cups.key / tc.key")
print("  Trust CA File:           cups.trust / tc.trust")
print("=======================================================\n")

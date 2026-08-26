import boto3
import json
import os
import urllib.request

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iot = session.client('iot')
iotwireless = session.client('iotwireless')

gw_eui = '2cf7f11080100354'
thing_name = 'SenseCAP_M2_IN865_Gateway'
policy_name = 'WirelessGatewayPolicy'
certs_dir = 'c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/certs'

os.makedirs(certs_dir, exist_ok=True)
print(f"[INFO] Cleaning up and re-registering Gateway {gw_eui}...")

# 1. Delete existing Wireless Gateways with this EUI
gws = iotwireless.list_wireless_gateways()['WirelessGatewayList']
for g in gws:
    if g.get('LoRaWAN', {}).get('GatewayEui', '').lower() == gw_eui.lower():
        gw_id = g['Id']
        print(f"[INFO] Deleting existing Wireless Gateway {gw_id}...")
        try:
            iotwireless.disassociate_wireless_gateway_from_thing(Id=gw_id)
        except Exception:
            pass
        iotwireless.delete_wireless_gateway(Id=gw_id)
        print(f"[OK] Deleted Wireless Gateway {gw_id}")

# 2. Delete existing IoT Thing and attached certificates
try:
    principals = iot.list_thing_principals(thingName=thing_name)['principals']
    for p in principals:
        cert_id = p.split('/')[-1]
        print(f"[INFO] Detaching and updating cert {cert_id}...")
        iot.detach_thing_principal(thingName=thing_name, principal=p)
        policies = iot.list_attached_policies(target=p)['policies']
        for pol in policies:
            iot.detach_policy(policyName=pol['policyName'], target=p)
        iot.update_certificate(certificateId=cert_id, newStatus='INACTIVE')
        iot.delete_certificate(certificateId=cert_id)
        print(f"[OK] Deleted Certificate {cert_id}")
    iot.delete_thing(thingName=thing_name)
    print(f"[OK] Deleted IoT Thing {thing_name}")
except iot.exceptions.ResourceNotFoundException:
    pass

# 3. Create fresh Wireless Gateway with IN865
res_gw = iotwireless.create_wireless_gateway(
    Name='SenseCAP-M2-IN865',
    Description='SenseCAP M2 IN865 Gateway Fresh Registration',
    LoRaWAN={
        'GatewayEui': gw_eui,
        'RfRegion': 'IN865'
    }
)
new_gw_id = res_gw['Id']
gw_arn = res_gw['Arn']
print(f"[SUCCESS] Created fresh IN865 Wireless Gateway! ID: {new_gw_id}")

# 4. Create fresh IoT Thing
thing = iot.create_thing(thingName=thing_name)
thing_arn = thing['thingArn']
print(f"[SUCCESS] Created fresh IoT Thing: {thing_name}")

# 5. Create fresh Keys and Certificate
cert_res = iot.create_keys_and_certificate(setAsActive=True)
cert_arn = cert_res['certificateArn']
cert_id = cert_res['certificateId']
cert_pem = cert_res['certificatePem']
priv_key = cert_res['keyPair']['PrivateKey']
pub_key = cert_res['keyPair']['PublicKey']

print(f"[SUCCESS] Created fresh Certificate ID: {cert_id}")

# 6. Ensure Policy exists and attach
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
except iot.exceptions.ResourceNotFoundException:
    iot.create_policy(
        policyName=policy_name,
        policyDocument=json.dumps(policy_document)
    )

iot.attach_policy(policyName=policy_name, target=cert_arn)
iot.attach_thing_principal(thingName=thing_name, principal=cert_arn)
print("[OK] Attached Policy and Thing to Certificate.")

# 7. Associate Gateway with Thing
iotwireless.associate_wireless_gateway_with_thing(
    Id=new_gw_id,
    ThingArn=thing_arn
)
print(f"[SUCCESS] Associated Wireless Gateway {new_gw_id} with Thing {thing_name}!")

# 8. Download Amazon Root CA 1
root_ca_url = 'https://www.amazontrust.com/repository/AmazonRootCA1.pem'
root_ca = urllib.request.urlopen(root_ca_url).read().decode('utf-8')

# Fetch Endpoints
cups_endpoint = iotwireless.get_service_endpoint(ServiceType='CUPS')['ServiceEndpoint']
lns_endpoint = iotwireless.get_service_endpoint(ServiceType='LNS')['ServiceEndpoint']

# Save files to certs folder
def save_file(filename, content):
    path = os.path.join(certs_dir, filename)
    with open(path, 'w') as f:
        f.write(content)
    print(f"  Saved: {path}")

print("\n[INFO] Saving certificate files to certs folder...")
save_file('cups.crt', cert_pem)
save_file('cups.key', priv_key)
save_file('cups.trust', root_ca)
save_file('cups_full.pem', cert_pem + '\n' + root_ca)
save_file('cups_combo.pem', cert_pem + '\n' + priv_key)

save_file('tc.crt', cert_pem)
save_file('tc.key', priv_key)
save_file('tc.trust', root_ca)

readme_text = f"""=======================================================
AQUA FEEDER SENSECAP M2 GATEWAY CONFIGURATION
=======================================================
Gateway EUI:        {gw_eui}
Gateway Region:     IN865
AWS Gateway ID:     {new_gw_id}
AWS Thing Name:     {thing_name}
Certificate ID:     {cert_id}

CUPS Server URL:    {cups_endpoint}
CUPS Hostname Only: A3AIZAWV83NXIH.cups.lorawan.us-east-1.amazonaws.com

LNS Server URL:     {lns_endpoint}
LNS Hostname Only:  A3AIZAWV83NXIH.lns.lorawan.us-east-1.amazonaws.com

CERTIFICATE FILES IN THIS FOLDER:
  1. Client Certificate: cups.crt (or tc.crt)
  2. Private Key:        cups.key (or tc.key)
  3. Trust CA Cert:      cups.trust (or tc.trust)
  4. Combined Cert+CA:   cups_full.pem
  5. Combined Cert+Key:  cups_combo.pem
=======================================================
"""
save_file('readme_config.txt', readme_text)

print("\n=======================================================")
print("=== FRESH AWS GATEWAY & CERTS REGISTRATION COMPLETE ===")
print("=======================================================")
print(f"  New Wireless Gateway ID: {new_gw_id}")
print(f"  Certificates Folder:     {certs_dir}")
print(f"  CUPS Endpoint:           {cups_endpoint}")
print(f"  LNS Endpoint:            {lns_endpoint}")
print("=======================================================\n")

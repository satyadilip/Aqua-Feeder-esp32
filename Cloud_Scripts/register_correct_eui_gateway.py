import boto3
import json
import os
import urllib.request
import requests
import urllib3

urllib3.disable_warnings()

# 1. Correct Gateway EUI from user screenshot: 2CF7F11090100354
gw_eui = '2CF7F11090100354'
thing_name = 'SenseCAP_M2_IN865_Gateway_Correct'
policy_name = 'WirelessGatewayPolicy'
certs_dir = 'c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/certs'

os.makedirs(certs_dir, exist_ok=True)
print(f"[INFO] Registering Gateway with EXACT EUI: {gw_eui} in AWS...")

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iot = session.client('iot')
iotwireless = session.client('iotwireless')

# Delete old gateways
gws = iotwireless.list_wireless_gateways()['WirelessGatewayList']
for g in gws:
    gw_id = g['Id']
    print(f"[INFO] Cleaning up old Wireless Gateway {gw_id}...")
    try:
        iotwireless.disassociate_wireless_gateway_from_thing(Id=gw_id)
    except Exception:
        pass
    iotwireless.delete_wireless_gateway(Id=gw_id)

# Create Wireless Gateway with exact EUI 2CF7F11090100354
res_gw = iotwireless.create_wireless_gateway(
    Name='SenseCAP-M2-IN865-Correct',
    Description='SenseCAP M2 IN865 Gateway Correct EUI',
    LoRaWAN={
        'GatewayEui': gw_eui,
        'RfRegion': 'IN865'
    }
)
new_gw_id = res_gw['Id']
gw_arn = res_gw['Arn']
print(f"[SUCCESS] Created IN865 Wireless Gateway! ID: {new_gw_id}, EUI: {gw_eui}")

# Create IoT Thing & Certificate
try:
    thing = iot.create_thing(thingName=thing_name)
    thing_arn = thing['thingArn']
except iot.exceptions.ResourceAlreadyExistsException:
    thing_arn = iot.describe_thing(thingName=thing_name)['thingArn']

cert_res = iot.create_keys_and_certificate(setAsActive=True)
cert_arn = cert_res['certificateArn']
cert_id = cert_res['certificateId']
cert_pem = cert_res['certificatePem']
priv_key = cert_res['keyPair']['PrivateKey']

iot.attach_policy(policyName=policy_name, target=cert_arn)
iot.attach_thing_principal(thingName=thing_name, principal=cert_arn)
iotwireless.associate_wireless_gateway_with_thing(Id=new_gw_id, ThingArn=thing_arn)
print(f"[SUCCESS] Associated Gateway {new_gw_id} with Certificate {cert_id}!")

# Download Amazon Root CA 1
root_ca_url = 'https://www.amazontrust.com/repository/AmazonRootCA1.pem'
root_ca = urllib.request.urlopen(root_ca_url).read().decode('utf-8')

# Save files locally
with open(f'{certs_dir}/cups.trust', 'w') as f: f.write(root_ca)
with open(f'{certs_dir}/cups.crt', 'w') as f: f.write(cert_pem)
with open(f'{certs_dir}/cups.key', 'w') as f: f.write(priv_key)

# 2. Automatically Upload Certificates & URI to Gateway Hardware via ubus API
host = '192.168.88.7'
login_url = f'https://{host}/cgi-bin/luci'
password = '5F7bukM4'

s = requests.Session()
s.verify = False
s.post(login_url, data={'luci_username': 'admin', 'luci_password': password}, headers={'Referer': login_url})
sysauth = s.cookies.get('sysauth')

ubus_url = f'https://{host}/ubus/'
def ubus_call(sid, module, method, params):
    req_body = {"jsonrpc": "2.0", "id": 1, "method": "call", "params": [sid, module, method, params]}
    return s.post(ubus_url, json=req_body).json()

res_auth = ubus_call("00000000000000000000000000000000", "session", "login", {"username": "admin", "password": password})
ubus_sid = res_auth.get('result', [0, {}])[1].get('ubus_rpc_session', sysauth)

lns_uri = "wss://A3AIZAWV83NXIH.lns.lorawan.us-east-1.amazonaws.com:443"

print("[INFO] Uploading fresh certificates to SenseCAP Gateway filesystem...")
ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/server.trust", "data": root_ca.strip() + '\n'})
ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/client.crt", "data": cert_pem.strip() + '\n'})
ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/client.key", "data": priv_key.strip() + '\n'})

print(f"[INFO] Setting UCI gateway_ID: '{gw_eui}', uri: '{lns_uri}'...")
ubus_call(ubus_sid, "uci", "set", {
    "config": "lora_network",
    "section": "network",
    "values": {"mode": "basic_station"}
})
ubus_call(ubus_sid, "uci", "set", {
    "config": "lora_network",
    "section": "station",
    "values": {
        "gateway_ID": gw_eui,
        "server": "lns",
        "uri": lns_uri,
        "auth_mode": "tls-server-client"
    }
})

print("\n=======================================================")
print("=== GATEWAY EUI 2CF7F11090100354 REGISTRATION COMPLETE ===")
print("=======================================================")
print(f"  Correct EUI:  {gw_eui}")
print(f"  Gateway ID:   {new_gw_id}")
print(f"  LNS URI:      {lns_uri}")
print("=======================================================\n")

import requests
import urllib3
import sys
import json

urllib3.disable_warnings()

if len(sys.argv) < 2:
    print("Usage: python fix_uri.py <GATEWAY_IP>")
    sys.exit(1)

host = sys.argv[1]
password = '5F7bukM4'

s = requests.Session()
s.verify = False

login = s.post(f'https://{host}/cgi-bin/luci', data={'luci_username': 'admin', 'luci_password': password}, verify=False)
sysauth = s.cookies.get('sysauth')

auth_req = {"jsonrpc":"2.0","id":1,"method":"call","params":["00000000000000000000000000000000","session","login",{"username":"admin","password":password}]}
ubus_sid = s.post(f'https://{host}/ubus/', json=auth_req, verify=False).json()['result'][1]['ubus_rpc_session']

# Force the URI and server settings
print("[INFO] Fixing the Server Type and URI directly in the database...")
s.post(f'https://{host}/ubus/', json={"jsonrpc":"2.0","id":1,"method":"call","params":[ubus_sid,"uci","set",{"config":"lora_network","section":"station","values":{"server":"cups_boot","uri":"https://A3AIZAWV83NXIH.cups.lorawan.us-east-1.amazonaws.com:443"}}]}, verify=False)

s.post(f'https://{host}/ubus/', json={"jsonrpc":"2.0","id":1,"method":"call","params":[ubus_sid,"uci","commit",{"config":"lora_network"}]}, verify=False)

# Restart the station service
print("[INFO] Restarting the gateway service...")
s.post(f'https://{host}/ubus/', json={"jsonrpc":"2.0","id":1,"method":"call","params":[ubus_sid,"file","exec",{"command":"/etc/init.d/station","params":["restart"]}]}, verify=False)

print("[SUCCESS] All fixed!")

import requests
import urllib3
import sys
import json

urllib3.disable_warnings()

if len(sys.argv) < 2:
    print("Usage: python debug_eui.py <GATEWAY_IP>")
    sys.exit(1)

host = sys.argv[1]
password = '5F7bukM4'

s = requests.Session()
s.verify = False

print(f"Connecting to Gateway {host}...")
login = s.post(f'https://{host}/cgi-bin/luci', data={'luci_username': 'admin', 'luci_password': password}, verify=False)
sysauth = s.cookies.get('sysauth')
if not sysauth:
    print("Login failed! Check password or IP.")
    sys.exit(1)

auth_req = {"jsonrpc":"2.0","id":1,"method":"call","params":["00000000000000000000000000000000","session","login",{"username":"admin","password":password}]}
ubus_sid = s.post(f'https://{host}/ubus/', json=auth_req, verify=False).json()['result'][1]['ubus_rpc_session']

# Read UCI lora_network
req = {"jsonrpc":"2.0","id":1,"method":"call","params":[ubus_sid,"uci","get",{"config":"lora_network"}]}
res = s.post(f'https://{host}/ubus/', json=req, verify=False).json()
print("\n--- LORA NETWORK CONFIG ---")
print(json.dumps(res, indent=2))
print("---------------------------\n")

# Check /var/etc/station/station.conf just in case
req2 = {"jsonrpc":"2.0","id":1,"method":"call","params":[ubus_sid,"file","read",{"path":"/var/etc/station/station.conf"}]}
res2 = s.post(f'https://{host}/ubus/', json=req2, verify=False).json()
if 'result' in res2 and len(res2['result']) >= 2 and 'data' in res2['result'][1]:
    print("\n--- STATION.CONF ---")
    print(res2['result'][1]['data'])
    print("--------------------\n")

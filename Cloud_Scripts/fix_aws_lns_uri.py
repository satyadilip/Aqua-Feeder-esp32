import requests
import json
import urllib3

urllib3.disable_warnings()

s = requests.Session()
s.verify = False

host = '192.168.88.7'
login_url = f'https://{host}/cgi-bin/luci'
password = '5F7bukM4'

s.post(login_url, data={'luci_username': 'admin', 'luci_password': password}, headers={'Referer': login_url})
sysauth = s.cookies.get('sysauth')

ubus_url = f'https://{host}/ubus/'

def ubus_call(sid, module, method, params):
    req_body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "call",
        "params": [sid, module, method, params]
    }
    r = s.post(ubus_url, json=req_body)
    return r.json()

res_auth = ubus_call("00000000000000000000000000000000", "session", "login", {"username": "admin", "password": password})
ubus_sid = res_auth.get('result', [0, {}])[1].get('ubus_rpc_session', sysauth)

# Correct AWS LNS URI with .lns. subdomain
correct_lns_uri = "wss://A3AIZAWV83NXIH.lns.lorawan.us-east-1.amazonaws.com:443"

print(f"[INFO] Setting CORRECT AWS LNS URI: {correct_lns_uri}...")

res_set = ubus_call(ubus_sid, "uci", "set", {
    "config": "lora_network",
    "section": "station",
    "values": {
        "server": "lns",
        "uri": correct_lns_uri,
        "auth_mode": "tls-server-client"
    }
})
print("Set uci result:", res_set)

# Update cert files in /etc/station/
cert_dir = 'c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/certs'
with open(f'{cert_dir}/cups.trust') as f:
    root_ca = f.read().strip() + '\n'
with open(f'{cert_dir}/cups.crt') as f:
    client_crt = f.read().strip() + '\n'
with open(f'{cert_dir}/cups.key') as f:
    client_key = f.read().strip() + '\n'

ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/server.trust", "data": root_ca})
ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/client.crt", "data": client_crt})
ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/client.key", "data": client_key})
print("[OK] Certificate files written to /etc/station/")

# Verify updated config
res_check = ubus_call(ubus_sid, "uci", "get", {"config": "lora_network"})
print("\n=== VERIFIED UCI CONFIG ===")
print(json.dumps(res_check, indent=2))

import requests
import json
import urllib3

urllib3.disable_warnings()

s = requests.Session()
s.verify = False

host = '192.168.88.7'
login_url = f'https://{host}/cgi-bin/luci'
password = '5F7bukM4'

# Login
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

# Read fresh certificates
cert_dir = 'c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/certs'
with open(f'{cert_dir}/cups.trust') as f:
    root_ca = f.read().strip() + '\n'
with open(f'{cert_dir}/cups.crt') as f:
    client_crt = f.read().strip() + '\n'
with open(f'{cert_dir}/cups.key') as f:
    client_key = f.read().strip() + '\n'

cups_url = "https://A3AIZAWV83NXIH.cups.lorawan.us-east-1.amazonaws.com:443"

print("[INFO] Writing certificate files directly to /etc/station/...")
ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/server.trust", "data": root_ca})
ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/client.crt", "data": client_crt})
ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/client.key", "data": client_key})
ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/cups.trust", "data": root_ca})
ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/cups.crt", "data": client_crt})
ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/cups.key", "data": client_key})
ubus_call(ubus_sid, "file", "write", {"path": "/etc/station/cups.uri", "data": cups_url + '\n'})

print(f"[INFO] Setting UCI station server='cups_boot', uri='{cups_url}'...")
ubus_call(ubus_sid, "uci", "set", {
    "config": "lora_network",
    "section": "network",
    "values": {"mode": "basic_station"}
})
ubus_call(ubus_sid, "uci", "set", {
    "config": "lora_network",
    "section": "station",
    "values": {
        "server": "cups_boot",
        "uri": cups_url,
        "auth_mode": "tls-server-client"
    }
})

ubus_call(ubus_sid, "uci", "commit", {"config": "lora_network"})
print("[SUCCESS] UCI lora_network committed for CUPS Boot Server!")

# Read back check
res_check = ubus_call(ubus_sid, "uci", "get", {"config": "lora_network"})
print(json.dumps(res_check, indent=2))

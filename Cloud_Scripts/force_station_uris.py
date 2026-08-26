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

# Read fresh certs
cert_dir = 'c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/certs'
with open(f'{cert_dir}/cups.trust') as f:
    root_ca = f.read().strip() + '\n'
with open(f'{cert_dir}/cups.crt') as f:
    client_crt = f.read().strip() + '\n'
with open(f'{cert_dir}/cups.key') as f:
    client_key = f.read().strip() + '\n'

lns_uri = "wss://A3AIZAWV83NXIH.lns.lorawan.us-east-1.amazonaws.com:443\n"
cups_uri = "https://A3AIZAWV83NXIH.cups.lorawan.us-east-1.amazonaws.com:443\n"

def write_file(path, content):
    res = ubus_call(ubus_sid, "file", "write", {"path": path, "data": content})
    print(f"  Writing {path}: {res}")

print("[INFO] Writing BasicStation LNS & CUPS URI and Certificate files directly to /etc/station/...")

# Write LNS files
write_file('/etc/station/tc.uri', lns_uri)
write_file('/etc/station/tc.trust', root_ca)
write_file('/etc/station/tc.crt', client_crt)
write_file('/etc/station/tc.key', client_key)

# Write CUPS files
write_file('/etc/station/cups.uri', cups_uri)
write_file('/etc/station/cups.trust', root_ca)
write_file('/etc/station/cups.crt', client_crt)
write_file('/etc/station/cups.key', client_key)

# Write Generic files
write_file('/etc/station/server.trust', root_ca)
write_file('/etc/station/client.crt', client_crt)
write_file('/etc/station/client.key', client_key)

# Update UCI
print("[INFO] Updating UCI lora_network config...")
ubus_call(ubus_sid, "uci", "set", {
    "config": "lora_network",
    "section": "network",
    "values": {"mode": "basic_station"}
})
ubus_call(ubus_sid, "uci", "set", {
    "config": "lora_network",
    "section": "station",
    "values": {
        "server": "lns",
        "uri": lns_uri.strip(),
        "auth_mode": "tls-server-client"
    }
})
ubus_call(ubus_sid, "uci", "commit", {"config": "lora_network"})

# Restart station daemon
print("[INFO] Restarting SenseCAP BasicStation service...")
ubus_call(ubus_sid, "file", "exec", {"command": "/etc/init.d/station", "params": ["restart"]})

print("\n[SUCCESS] BasicStation configuration & URIs written to /etc/station/!")

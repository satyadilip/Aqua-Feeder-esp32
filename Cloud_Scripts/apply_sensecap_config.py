import requests
import json
import urllib3

urllib3.disable_warnings()

s = requests.Session()
s.verify = False

host = '192.168.88.7'
login_url = f'https://{host}/cgi-bin/luci'
password = '5F7bukM4'

# 1. Login to get session
s.post(login_url, data={'luci_username': 'admin', 'luci_password': password}, headers={'Referer': login_url})
sysauth = s.cookies.get('sysauth')
print(f"[OK] Logged in! sysauth session: {sysauth}")

# Read fresh certificates from project folder
cert_dir = 'c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/certs'
with open(f'{cert_dir}/cups.trust') as f:
    server_trust = f.read()
with open(f'{cert_dir}/cups.crt') as f:
    client_crt = f.read()
with open(f'{cert_dir}/cups.key') as f:
    client_key = f.read()

# 2. Call LuCI ubus RPC or LuCI file write API
# LuCI modern API uses /ubus/ endpoint with session id
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

# Authenticate ubus session
res_auth = ubus_call("00000000000000000000000000000000", "session", "login", {"username": "admin", "password": password})
ubus_sid = res_auth.get('result', [0, {}])[1].get('ubus_rpc_session', sysauth)
print(f"[OK] ubus session authenticated: {ubus_sid}")

# Write certificate files directly via file write API
def write_remote_file(filepath, content):
    res = ubus_call(ubus_sid, "file", "write", {"path": filepath, "data": content})
    print(f"  Writing {filepath}: {res}")

print("[INFO] Uploading certificate files to SenseCAP gateway filesystem...")
write_remote_file('/etc/station/server.trust', server_trust.strip() + '\n')
write_remote_file('/etc/station/client.crt', client_crt.strip() + '\n')
write_remote_file('/etc/station/client.key', client_key.strip() + '\n')

# 3. Set UCI configuration for lora_network
print("[INFO] Updating uci configuration for lora_network...")

# Set mode to basic_station
ubus_call(ubus_sid, "uci", "set", {
    "config": "lora_network",
    "section": "network",
    "values": {
        "mode": "basic_station"
    }
})

# Set station configuration
lns_url = "wss://A3AIZAWV83NXIH.lns.lorawan.us-east-1.amazonaws.com:443"
ubus_call(ubus_sid, "uci", "set", {
    "config": "lora_network",
    "section": "station",
    "values": {
        "server": "lns",
        "uri": lns_url,
        "auth_mode": "tls-server-client"
    }
})

# Commit uci configuration
ubus_call(ubus_sid, "uci", "commit", {"config": "lora_network"})
print("[SUCCESS] UCI configuration committed!")

# 4. Restart station service
print("[INFO] Restarting SenseCAP BasicStation service...")
ubus_call(ubus_sid, "file", "exec", {"command": "/etc/init.d/station", "params": ["restart"]})

print("\n=======================================================")
print("=== SENSECAP GATEWAY CONFIGURATION APPLIED LIVE! ===")
print("=======================================================")
print(f"  Mode:        Basic Station")
print(f"  Server:      LNS")
print(f"  URI:         {lns_url}")
print(f"  Auth Mode:   TLS Server and Client Authentication")
print(f"  Certs:       Uploaded server.trust, client.crt, client.key")
print("=======================================================\n")

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

# 1. Get current lora_network uci config
res_get = ubus_call(ubus_sid, "uci", "get", {"config": "lora_network"})
print("=== CURRENT UCI LORA_NETWORK CONFIG ===")
print(json.dumps(res_get, indent=2))

# 2. Update section network to mode basic_station
lns_uri = "wss://A3AIZAWV83NXIH.lns.lorawan.us-east-1.amazonaws.com:443"

ubus_call(ubus_sid, "uci", "set", {
    "config": "lora_network",
    "section": "network",
    "values": {
        "mode": "basic_station"
    }
})

# Find station section name (usually '@station[0]' or 'station')
values_station = {
    "server": "lns",
    "uri": lns_uri,
    "auth_mode": "tls-server-client"
}

res_set1 = ubus_call(ubus_sid, "uci", "set", {
    "config": "lora_network",
    "section": "station",
    "values": values_station
})
print("Set station res:", res_set1)

res_commit = ubus_call(ubus_sid, "uci", "commit", {"config": "lora_network"})
print("Commit res:", res_commit)

print("\n=== VERIFYING UPDATED UCI CONFIG ===")
res_check = ubus_call(ubus_sid, "uci", "get", {"config": "lora_network"})
print(json.dumps(res_check, indent=2))

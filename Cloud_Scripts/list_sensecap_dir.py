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

# List files in /etc/station/
res_list = ubus_call(ubus_sid, "file", "list", {"path": "/etc/station"})
print("=== /etc/station FILES ===")
print(res_list)

files_to_read = ['tc.uri', 'cups.uri', 'station.conf', 'tc.trust', 'server.trust', 'tc.crt', 'client.crt']

for fn in files_to_read:
    p = f'/etc/station/{fn}'
    res = ubus_call(ubus_sid, "file", "read", {"path": p, "length": 500, "offset": 0})
    result = res.get('result', [])
    if len(result) > 1 and isinstance(result[1], dict):
        data = result[1].get('data', '')
        print(f"=== {p} ===")
        print(data.strip())

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

# Check log files
log_paths = ['/var/log/messages', '/tmp/station.log', '/var/log/station.log', '/tmp/syslog.log']

for p in log_paths:
    res = ubus_call(ubus_sid, "file", "read", {"path": p, "length": 4000, "offset": 0})
    result = res.get('result', [])
    if len(result) > 1 and isinstance(result[1], dict):
        data = result[1].get('data', '')
        if data:
            print(f"=== LOG FILE {p} ===")
            lines = [l for l in data.splitlines() if 'station' in l.lower() or 'lora' in l.lower() or 'error' in l.lower() or 'fail' in l.lower()]
            for l in lines[-30:]:
                print("  ", l.encode('ascii', errors='replace').decode('ascii'))

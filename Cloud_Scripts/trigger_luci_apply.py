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

# Trigger LuCI apply
apply_url = f'https://{host}/cgi-bin/luci/admin/uci/apply'
r = s.post(apply_url, data={'tok': 'a18ad985f6f931473c263d4bc4e78f4e'}, headers={'Referer': login_url})
print("LuCI Apply Response:", r.status_code)

# Trigger LuCI service restart via RPC
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
ubus_sid = res_auth.get('result', [0, {}])[1].get('ubus_rpc_session')

res_serv = ubus_call(ubus_sid, "service", "list", {"name": "station"})
print("=== SERVICE STATION LIST ===")
print(res_serv)

res_restart = ubus_call(ubus_sid, "service", "event", {"type": "service.restart", "data": {"name": "station"}})
print("=== SERVICE RESTART EVENT ===", res_restart)

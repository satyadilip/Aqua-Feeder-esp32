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

# Write files using LuCI cbi/fs write handler or station conf
# SenseCAP station init script /etc/init.d/station builds /var/etc/station/ from /etc/station/
# Let's inspect /etc/init.d/station script!

res_init = ubus_call(ubus_sid, "file", "read", {"path": "/etc/init.d/station", "length": 4000, "offset": 0})
init_script = res_init.get('result', [])
if len(init_script) > 1 and isinstance(init_script[1], dict):
    print("=== /etc/init.d/station SCRIPT ===")
    script_text = init_script[1].get('data', '')
    print(script_text.encode('ascii', errors='replace').decode('ascii'))

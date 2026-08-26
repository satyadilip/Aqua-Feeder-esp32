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

lns_uri = "wss://A3AIZAWV83NXIH.lns.lorawan.us-east-1.amazonaws.com:443"
cups_uri = "https://A3AIZAWV83NXIH.cups.lorawan.us-east-1.amazonaws.com:443"

# Read fresh certs
cert_dir = 'c:/Users/nsaty/Documents/Dilip Work/Aqua_feeder/certs'
with open(f'{cert_dir}/cups.trust') as f:
    root_ca = f.read().strip()
with open(f'{cert_dir}/cups.crt') as f:
    client_crt = f.read().strip()
with open(f'{cert_dir}/cups.key') as f:
    client_key = f.read().strip()

# Run shell command via file exec
def run_cmd(cmd_str):
    res = ubus_call(ubus_sid, "file", "exec", {"command": "/bin/sh", "params": ["-c", cmd_str]})
    print(f"  CMD [{cmd_str[:40]}...]: {res}")
    return res

print("[INFO] Writing URI files and certificates via shell execution...")
run_cmd(f"echo '{lns_uri}' > /etc/station/tc.uri")
run_cmd(f"echo '{cups_uri}' > /etc/station/cups.uri")
run_cmd(f"echo '{root_ca}' > /etc/station/tc.trust")
run_cmd(f"echo '{client_crt}' > /etc/station/tc.crt")
run_cmd(f"echo '{client_key}' > /etc/station/tc.key")
run_cmd(f"echo '{root_ca}' > /etc/station/cups.trust")
run_cmd(f"echo '{client_crt}' > /etc/station/cups.crt")
run_cmd(f"echo '{client_key}' > /etc/station/cups.key")
run_cmd(f"echo '{root_ca}' > /etc/station/server.trust")
run_cmd(f"echo '{client_crt}' > /etc/station/client.crt")
run_cmd(f"echo '{client_key}' > /etc/station/client.key")

# Restart station daemon
print("[INFO] Restarting SenseCAP BasicStation service...")
run_cmd("/etc/init.d/station restart")

print("\n[SUCCESS] Shell execution completed!")

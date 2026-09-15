import requests
import urllib3
import sys

urllib3.disable_warnings()

if len(sys.argv) < 2:
    print("Usage: python fix_eui.py <GATEWAY_IP>")
    sys.exit(1)

host = sys.argv[1]
password = '5F7bukM4'

s = requests.Session()
s.verify = False

# 1. Login
login = s.post(f'https://{host}/cgi-bin/luci', data={'luci_username': 'admin', 'luci_password': password}, verify=False)
sysauth = s.cookies.get('sysauth')
if not sysauth:
    print("Login failed! Check password.")
    sys.exit(1)

# 2. Get UBUS session
auth_req = {"jsonrpc":"2.0","id":1,"method":"call","params":["00000000000000000000000000000000","session","login",{"username":"admin","password":password}]}
ubus_sid = s.post(f'https://{host}/ubus/', json=auth_req, verify=False).json()['result'][1]['ubus_rpc_session']

# 3. Read the buggy station.conf
read_req = {"jsonrpc":"2.0","id":1,"method":"call","params":[ubus_sid,"file","read",{"path":"/etc/station/station.conf"}]}
res = s.post(f'https://{host}/ubus/', json=read_req, verify=False).json()
if 'result' not in res or len(res['result']) < 2 or 'data' not in res['result'][1]:
    print("Could not read station.conf. Is Basic Station running?")
    sys.exit(1)

conf = res['result'][1]['data']

# 4. Fix the dropped zero bug
if "2cf7:f110:8010:354" in conf or "2cf7f1108010354" in conf:
    print("[INFO] Found the bugged EUI! Fixing...")
    conf = conf.replace("2cf7:f110:8010:354", "2CF7F11080100354")
    conf = conf.replace("2cf7f1108010354", "2CF7F11080100354")
    
    # Write it back
    write_req = {"jsonrpc":"2.0","id":1,"method":"call","params":[ubus_sid,"file","write",{"path":"/etc/station/station.conf","data":conf}]}
    s.post(f'https://{host}/ubus/', json=write_req, verify=False)
    
    # Restart the station service
    restart_req = {"jsonrpc":"2.0","id":1,"method":"call","params":[ubus_sid,"file","exec",{"command":"/etc/init.d/station","params":["restart"]}]}
    s.post(f'https://{host}/ubus/', json=restart_req, verify=False)
    
    print("[SUCCESS] Fixed! The gateway is restarting with the correct 16-character EUI.")
else:
    print("[INFO] The bugged EUI was not found in station.conf. No changes made.")

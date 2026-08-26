import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req1 = urllib.request.Request("http://192.168.88.7/ubus", data=json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "call",
    "params": ["00000000000000000000000000000000", "session", "login", {"username": "admin", "password": "5F7bukM4"}]
}).encode('utf-8'), headers={'Content-Type': 'application/json'})

res1 = json.loads(urllib.request.urlopen(req1, context=ctx).read())
sid = res1['result'][1]['ubus_rpc_session']

req2 = urllib.request.Request("http://192.168.88.7/ubus", data=json.dumps({
    "jsonrpc": "2.0", "id": 2, "method": "call",
    "params": [sid, "file", "exec", {"command": "logread", "args": ["-e", "station"]}]
}).encode('utf-8'), headers={'Content-Type': 'application/json'})

res2 = json.loads(urllib.request.urlopen(req2, context=ctx).read())
print("=== SENSECAP BASICSTATION LOGS ===")
try:
    stdout = res2['result'][1]['stdout']
    lines = stdout.splitlines()
    print('\n'.join(lines[-40:]))
except Exception as e:
    print("Log format error:", e, res2)

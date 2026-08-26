import requests
import urllib3

urllib3.disable_warnings()

s = requests.Session()
s.verify = False

url = 'https://192.168.88.7/luci-static/resources/view/lora/lora_network.js'
r = s.get(url)

lines = r.text.splitlines()
print("=== lora_network.js LINES 1 to 180 ===")
for i, line in enumerate(lines[:180]):
    print(f"{i+1:3d}: {line.encode('ascii', errors='replace').decode('ascii')}")

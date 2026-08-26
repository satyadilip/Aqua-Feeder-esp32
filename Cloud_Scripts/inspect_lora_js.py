import requests
import urllib3

urllib3.disable_warnings()

s = requests.Session()
s.verify = False

url = 'https://192.168.88.7/luci-static/resources/view/lora/lora_network.js'
r = s.get(url)

print("=== lora_network.js CONTENT ===")
print(r.text.encode('ascii', errors='replace').decode('ascii'))

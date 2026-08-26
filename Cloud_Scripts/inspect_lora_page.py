import requests
import re
import urllib3

urllib3.disable_warnings()

s = requests.Session()
s.verify = False

login_url = 'https://192.168.88.7/cgi-bin/luci'
s.post(login_url, data={'luci_username': 'admin', 'luci_password': '5F7bukM4'}, headers={'Referer': login_url})

url = 'https://192.168.88.7/cgi-bin/luci/admin/lora'
r = s.get(url)

print("=== /cgi-bin/luci/admin/lora CONTENT ===")
print(r.text.encode('ascii', errors='replace').decode('ascii'))

# Find all links on this page
links = re.findall(r'href="([^"]+)"', r.text)
print("\n=== LINKS ON LORA PAGE ===")
for l in sorted(list(set(links))):
    print("  Link:", l)

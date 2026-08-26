import requests
import re
import urllib3

urllib3.disable_warnings()

s = requests.Session()
s.verify = False

login_url = 'https://192.168.88.7/cgi-bin/luci'
res_login = s.post(login_url, data={'luci_username': 'admin', 'luci_password': '5F7bukM4'}, headers={'Referer': login_url})

print("Login Status:", res_login.status_code)
print("Session Cookies:", s.cookies.get_dict())

res_home = s.get('https://192.168.88.7/cgi-bin/luci/admin/status/overview')
print("\n=== SENSECAP MENU DISCOVERY ===")

links = re.findall(r'href="(/cgi-bin/luci/[^"]+)"', res_home.text)
for l in sorted(list(set(links))):
    print("  Link:", l)

# Also check common SenseCAP endpoints
endpoints = [
    '/cgi-bin/luci/admin/lora',
    '/cgi-bin/luci/admin/lora/basicstation',
    '/cgi-bin/luci/admin/lora/packet_forwarder',
    '/cgi-bin/luci/admin/services/lora',
    '/cgi-bin/luci/admin/services/basicstation',
    '/cgi-bin/luci/admin/admin_status/index'
]

print("\n=== PROBING LORA ENDPOINTS ===")
for ep in endpoints:
    url = f"https://192.168.88.7{ep}"
    r = s.get(url)
    if r.status_code == 200 and 'Authorization Required' not in r.text:
        print(f"[FOUND 200] {ep} (Length: {len(r.text)})")
        # Find forms
        forms = re.findall(r'<form[^>]+action="([^"]+)"', r.text)
        print(f"   Action URLs: {forms}")
    else:
        print(f"[{r.status_code}] {ep}")

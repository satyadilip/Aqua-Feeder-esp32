import threading
import subprocess

def ping(ip):
    subprocess.call(['ping', '-n', '1', '-w', '100', ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Detecting local subnets...")
try:
    arp_out = subprocess.check_output('arp -a', shell=True).decode(errors='ignore')
except Exception as e:
    arp_out = ""

subnets = set()
for line in arp_out.split('\n'):
    line = line.strip()
    if line.startswith('Interface:'):
        ip = line.split()[1]
        parts = ip.split('.')
        # Only sweep typical local networks to save time
        if len(parts) == 4 and parts[0] in ['192', '10', '172']:
            subnets.add(f"{parts[0]}.{parts[1]}.{parts[2]}")

if not subnets:
    subnets.add("192.168.29")

print(f"Sweeping subnets: {', '.join(subnets)}.x (this will take 2 seconds)...")
threads = []
for subnet in subnets:
    for i in range(1, 255):
        t = threading.Thread(target=ping, args=(f"{subnet}.{i}",))
        t.start()
        threads.append(t)

for t in threads:
    t.join()

print("Scanning ARP table for SenseCAP Gateway (MAC: 2C-F7-F1)...")
result = subprocess.check_output('arp -a', shell=True).decode(errors='ignore')
found = False
for line in result.split('\n'):
    if '2c-f7' in line.lower() or '2c:f7' in line.lower():
        parts = line.split()
        if len(parts) >= 2:
            print(f"\n[SUCCESS] Gateway Found! IP Address: {parts[0]}")
            print(f"--> Open in browser: http://{parts[0]}")
            found = True

if not found:
    print("\n[FAILED] Gateway not found in the ARP cache.")
    print("Are you sure the gateway is powered on and connected to this exact network?")
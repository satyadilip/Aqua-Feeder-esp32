import serial
import serial.tools.list_ports
import time
import sys
import re

print("=" * 65)
print("   AQUA FEEDER / LORAWAN NODE - AUTO-RESET & KEY EXTRACTOR")
print("=" * 65)

def find_target_port():
    """Auto-detect active USB Serial COM port."""
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return None
    
    print("\n[+] Available COM Ports detected:")
    for p in ports:
        print(f"    - {p.device}: {p.description} (VID:PID={p.vid}:{p.pid})")
    
    # Priority matching
    for p in ports:
        desc = (p.description or "").lower()
        mfg = (p.manufacturer or "").lower()
        if any(k in desc or k in mfg for k in ["esp32", "cp210", "ch340", "ftdi", "usb serial", "jtag"]):
            if "COM3" not in p.device and "COM4" not in p.device:
                return p.device
                
    # Fallback: first non-standard COM
    for p in ports:
        if p.device not in ["COM1", "COM3", "COM4"]:
            return p.device
            
    return ports[0].device

port = find_target_port()
if not port:
    print("\n[!] ERROR: No active COM ports found. Please check USB cable connection.")
    sys.exit(1)

print(f"\n[+] Selected Port: {port} at 115200 baud")

try:
    ser = serial.Serial(port, 115200, timeout=0.2)
except Exception as e:
    print(f"\n[!] ERROR opening port {port}: {e}")
    sys.exit(1)

print("[+] Triggering software reset pulse via DTR/RTS...")
# DTR/RTS toggle resets ESP32 without touching physical button
ser.dtr = False
ser.rts = True
time.sleep(0.15)
ser.dtr = False
ser.rts = False
time.sleep(0.3)

# Send CLI unlock and EUI queries in case it is already booted
ser.write(b"\r\n")
time.sleep(0.1)
ser.write(b"AUTH 123456\r\n")
ser.write(b"AUTH 8888\r\n")
ser.write(b"EUI\r\n")
ser.write(b"S\r\n")

print("[+] Capturing serial output for 8 seconds...\n")
output_lines = []
start_time = time.time()
while time.time() - start_time < 8.0:
    if ser.in_waiting:
        try:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line:
                output_lines.append(line)
                print(f"  {line}")
        except Exception:
            pass
    time.sleep(0.02)

ser.close()

full_text = "\n".join(output_lines)

# Search for EUI and Keys
print("\n" + "=" * 65)
print("           EXTRACTED LORAWAN CREDENTIALS SUMMARY")
print("=" * 65)

deveui_match = re.search(r'DevEUI\s*[:=]\s*([0-9a-fA-F]{16})', full_text, re.IGNORECASE)
appeui_match = re.search(r'AppEUI\s*[:=]\s*([0-9a-fA-F]{16})', full_text, re.IGNORECASE)
appkey_match = re.search(r'AppKey\s*[:=]\s*([0-9a-fA-F]{32})', full_text, re.IGNORECASE)

if deveui_match:
    print(f"  DevEUI : {deveui_match.group(1).upper()}")
else:
    print("  DevEUI : (Not explicitly parsed - check raw lines above)")

if appeui_match:
    print(f"  AppEUI : {appeui_match.group(1).upper()}")
else:
    print("  AppEUI : 0000000000000000 (Default)")

if appkey_match:
    print(f"  AppKey : {appkey_match.group(1).upper()}")
else:
    print("  AppKey : (Not explicitly parsed - check raw lines above)")

lora_status = [l for l in output_lines if any(k in l.upper() for k in ["LORA", "SX1262", "JOIN", "CONNECTED"])]
if lora_status:
    print("\n  LoRa Hardware Status:")
    for l in lora_status:
        print(f"    -> {l}")

print("=" * 65)

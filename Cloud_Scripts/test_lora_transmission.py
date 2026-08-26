import serial
import time

print("=== CONNECTING TO ESP32-S3 CLI ON COM9 ===")
try:
    ser = serial.Serial('COM9', 115200, timeout=1)
    time.sleep(1)
    
    ser.write(b"AUTH 8888\r\n")
    time.sleep(0.5)
    ser.write(b"DIAG\r\n")
    time.sleep(0.5)
    
    print("=== LIVE SERIAL MONITORING ===")
    start_time = time.time()
    while time.time() - start_time < 12:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print("  [NODE]:", line)
    ser.close()
except Exception as e:
    print("Serial error:", e)

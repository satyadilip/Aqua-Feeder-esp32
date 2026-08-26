import serial
import time

print("=== READING LIVE SERIAL FROM COM9 ===")
try:
    ser = serial.Serial('COM9', 115200, timeout=1)
    
    start_time = time.time()
    while time.time() - start_time < 8:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print("  [NODE]:", line)
    ser.close()
except Exception as e:
    print("Serial error:", e)

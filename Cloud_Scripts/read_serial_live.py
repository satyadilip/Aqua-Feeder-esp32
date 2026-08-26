import serial
import time

try:
    ser = serial.Serial('COM9', 115200, timeout=1)
    print("=== LISTENING TO COM9 SERIAL STREAM (20 SECONDS) ===")
    start = time.time()
    while time.time() - start < 20:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line:
                print("  [NODE]:", line)
        time.sleep(0.05)
    ser.close()
except Exception as e:
    print("Serial error:", e)

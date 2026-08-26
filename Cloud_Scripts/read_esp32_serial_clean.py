import serial
import time
import sys

try:
    ser = serial.Serial('COM9', 115200, timeout=1)
    
    # Trigger reset
    ser.dtr = False
    ser.rts = True
    time.sleep(0.1)
    ser.rts = False
    time.sleep(0.5)
    
    print("=== LIVE ESP32-S3 SERIAL BOOT & DIAGNOSTIC LOGS ===")
    start = time.time()
    while time.time() - start < 15:
        if ser.in_waiting:
            line_bytes = ser.readline()
            line = line_bytes.decode('utf-8', errors='replace').strip()
            if line:
                # Encode safely for console
                safe_line = line.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
                print("  [NODE]:", safe_line)
        time.sleep(0.02)
    ser.close()
except Exception as e:
    print("Error:", e)

import serial
import time

print("=== READING LIVE SERIAL FROM ESP32-S3 ON COM9 ===")
try:
    ser = serial.Serial('COM9', 115200, timeout=1)
    # Toggle DTR/RTS to reset ESP32
    ser.setDTR(False)
    ser.setRTS(False)
    time.sleep(0.1)
    ser.setDTR(True)
    ser.setRTS(True)
    time.sleep(0.1)
    ser.setDTR(False)
    ser.setRTS(False)
    
    start_time = time.time()
    while time.time() - start_time < 10:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            print("  [NODE SERIAL]:", line)
    ser.close()
except Exception as e:
    print("Serial read error:", e)

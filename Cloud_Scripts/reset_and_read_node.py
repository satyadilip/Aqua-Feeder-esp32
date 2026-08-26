import serial
import time

print("=== TRIGGERING HARDWARE RESET VIA RTS ON COM9 ===")
try:
    ser = serial.Serial('COM9', 115200, timeout=1)
    
    # Pulse RTS low/high to reset ESP32 hardware EN pin
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.1)
    ser.setRTS(False)
    time.sleep(0.2)
    
    print("=== LISTENING TO ESP32-S3 SERIAL OUTPUT ===")
    start_time = time.time()
    while time.time() - start_time < 12:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print("  [NODE SERIAL]:", line)
    ser.close()
except Exception as e:
    print("Serial error:", e)

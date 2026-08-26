import serial
import time

print("=== RESETTING ESP32-S3 TO NORMAL RUN MODE ===")
try:
    ser = serial.Serial('COM9', 115200, timeout=1)
    
    # Pulse RTS to trigger EN pin hardware reset without entering bootloader mode
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.1)
    ser.setRTS(False)
    time.sleep(0.5)
    
    print("Listening to Node Serial logs...")
    start_time = time.time()
    while time.time() - start_time < 12:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print("  [NODE]:", line)
    ser.close()
except Exception as e:
    print("Serial error:", e)

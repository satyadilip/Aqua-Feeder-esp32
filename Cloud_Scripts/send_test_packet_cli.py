import serial
import time

print("=== SENDING CLI COMMANDS TO ESP32-S3 ===")
try:
    ser = serial.Serial('COM9', 115200, timeout=0.5)
    
    # Reset DTR/RTS to wake CDC
    ser.dtr = False
    ser.rts = False
    time.sleep(0.1)
    
    ser.write(b"\r\n")
    time.sleep(0.2)
    ser.write(b"AUTH 8888\r\n")
    time.sleep(0.3)
    ser.write(b"DIAG\r\n")
    time.sleep(0.5)
    
    buf = ser.read(2048)
    print("Received bytes:", len(buf))
    if buf:
        print(buf.decode('utf-8', errors='ignore'))
        
    ser.close()
except Exception as e:
    print("Error:", e)

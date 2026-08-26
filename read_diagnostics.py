import serial
import serial.tools.list_ports
import time
import sys

def find_esp32_port():
    """Auto-detect active ESP32 USB CDC or Serial COM port."""
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        desc = (p.description or "").lower()
        mfg = (p.manufacturer or "").lower()
        # Look for ESP32 CDC / USB Serial ports
        if "esp32" in desc or "usb" in desc or "serial" in desc or "esp32" in mfg or "expressif" in mfg:
            if "COM3" not in p.device and "COM4" not in p.device: # Skip Bluetooth standard serial ports
                return p.device
    
    # Fallback to last non-standard COM port
    for p in reversed(ports):
        if "COM3" not in p.device and "COM4" not in p.device:
            return p.device
            
    return None

def main():
    port = find_esp32_port()
    if not port:
        print("[ERROR] No active ESP32 COM port detected. Please verify USB cable connection.")
        sys.exit(1)
        
    print(f"[INFO] Auto-detected ESP32 COM Port: {port}")
    print("[INFO] Resetting controller and capturing hardware diagnostics...")
    
    try:
        ser = serial.Serial(port, 115200, timeout=0.1)
        
        # Hardware Reset Pulse via DTR/RTS
        ser.dtr = False
        ser.rts = True
        time.sleep(0.1)
        ser.dtr = False
        ser.rts = False
        time.sleep(0.2)
        
        # Read serial output for 6 seconds
        start_time = time.time()
        output_buffer = ""
        while time.time() - start_time < 6.0:
            if ser.in_waiting:
                data = ser.read_all().decode('utf-8', errors='replace')
                output_buffer += data
            time.sleep(0.05)
            
        ser.close()
        
        print("\n==================== LIVE BOARD DIAGNOSTIC OUTPUT ====================")
        clean_text = output_buffer.encode('ascii', errors='replace').decode('ascii')
        print(clean_text)
        print("====================================================================\n")
        
    except Exception as e:
        print(f"[ERROR] Failed to communicate with port {port}: {e}")

if __name__ == "__main__":
    main()

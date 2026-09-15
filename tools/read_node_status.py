import serial
import serial.tools.list_ports
import time
import sys

def main():
    print("==================================================")
    print("   AquaFeeder Serial Status & EUI Reader")
    print("==================================================")
    
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("[ERROR] No COM ports found!")
        sys.exit(1)
        
    print("\nAvailable COM Ports:")
    for i, port in enumerate(ports):
        print(f"  [{i+1}] {port.device} - {port.description}")
        
    try:
        selection = int(input(f"\nSelect port (1-{len(ports)}): ")) - 1
        if selection < 0 or selection >= len(ports):
            print("[ERROR] Invalid selection.")
            sys.exit(1)
    except ValueError:
        print("[ERROR] Please enter a valid number.")
        sys.exit(1)
        
    selected_port = ports[selection].device
    print(f"\n[OK] Connecting to {selected_port} at 115200 baud...\n")
    
    try:
        ser = serial.Serial(selected_port, 115200, timeout=1)
        
        print("=== TRIGGERING HARDWARE RESET ===")
        # ESP32 Reset sequence (DTR/RTS)
        ser.setDTR(False)
        ser.setRTS(True)
        time.sleep(0.1)
        ser.setRTS(False)
        time.sleep(1)
        
        # Clear buffer
        ser.read_all()
        
        print("=== AUTHENTICATING ===")
        ser.write(b"AUTH 1234\n")
        time.sleep(0.5)
        
        print("=== LISTENING TO LIVE LOGS (Press Ctrl+C to exit) ===")
        while True:
            if ser.in_waiting:
                line_bytes = ser.readline()
                line = line_bytes.decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"  [NODE]: {line}")
            else:
                time.sleep(0.01)
                
    except KeyboardInterrupt:
        print("\n[OK] Exiting reader...")
    except serial.SerialException as e:
        print(f"\n[ERROR] Failed to open port: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()

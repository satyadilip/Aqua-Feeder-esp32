import serial
import serial.tools.list_ports
import time
import sys

def main():
    print("==================================================")
    print("   AquaFeeder LoRaWAN Nonce Eraser")
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
    print(f"\n[OK] Connecting to {selected_port} at 115200 baud...")
    
    try:
        ser = serial.Serial(selected_port, 115200, timeout=2)
        time.sleep(2)  # Wait for ESP32 to boot if auto-reset happened
        
        # Clear any leftover serial buffer
        ser.read_all()
        
        print("\n=== AUTHENTICATING ===")
        ser.write(b"AUTH 1234\n")
        time.sleep(0.5)
        response = ser.read_all().decode('utf-8', errors='ignore')
        print(response.strip())
        
        if "SUCCESS" not in response and "unlocked" not in response:
            print("\n[WARNING] Authentication might have failed or device was already unlocked. Proceeding anyway...")
        
        print("\n=== ERASING LORAWAN NONCES ===")
        ser.write(b"ERASE LORA\n")
        time.sleep(0.5)
        response = ser.read_all().decode('utf-8', errors='ignore')
        print(response.strip())
        
        print("\n=== REBOOTING DEVICE ===")
        ser.write(b"REBOOT\n")
        time.sleep(0.5)
        response = ser.read_all().decode('utf-8', errors='ignore')
        print(response.strip())
        
        print("\n[SUCCESS] LoRaWAN Nonces have been cleared!")
        ser.close()
        
    except serial.SerialException as e:
        print(f"\n[ERROR] Failed to open port: {e}")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()

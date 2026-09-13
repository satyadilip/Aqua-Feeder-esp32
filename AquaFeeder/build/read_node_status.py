import serial
import serial.tools.list_ports
import time
import sys

def get_esp32_ports():
    ports = serial.tools.list_ports.comports()
    esp_ports = []
    
    # Common USB-to-UART bridge keywords for ESP32
    keywords = ["cp210", "ch340", "ftdi", "usb serial", "usb jtag"]
    
    for port in ports:
        desc = port.description.lower()
        if any(kw in desc for kw in keywords):
            esp_ports.append(port)
            
    return esp_ports, ports

def main():
    print("="*50)
    print("   AquaFeeder Serial Status & EUI Reader")
    print("="*50)
    
    esp_ports, all_ports = get_esp32_ports()
    selected_port = None
    
    if len(esp_ports) == 1:
        selected_port = esp_ports[0].device
        print(f"Found ESP32 device on {selected_port} ({esp_ports[0].description})")
        ans = input("Use this port? (Y/n): ")
        if ans.lower() == 'n':
            selected_port = None
            
    if not selected_port:
        if not all_ports:
            print("[ERROR] No COM ports found!")
            sys.exit(1)
            
        print("\nAvailable COM Ports:")
        for i, port in enumerate(all_ports):
            print(f"  [{i+1}] {port.device} - {port.description}")
        
        while True:
            try:
                choice = int(input(f"\nSelect port (1-{len(all_ports)}): "))
                if 1 <= choice <= len(all_ports):
                    selected_port = all_ports[choice-1].device
                    break
                print("Invalid choice.")
            except ValueError:
                print("Please enter a valid number.")

    print(f"\n[OK] Connecting to {selected_port} at 115200 baud...")
    
    try:
        ser = serial.Serial(selected_port, 115200, timeout=0.1)
        
        print("\n=== TRIGGERING HARDWARE RESET ===")
        # Toggle DTR/RTS to reset the ESP32
        ser.setDTR(False)
        ser.setRTS(True)
        time.sleep(0.1)
        ser.setRTS(False)
        
        print("Waiting for boot...")
        time.sleep(1.5) # Wait for ESP32 to fully boot
        
        # Flush the initial boot logs to clear the buffer
        boot_logs = ser.read_all().decode('utf-8', errors='ignore')
        
        print("\n=== AUTHENTICATING ===")
        ser.write(b"AUTH 8888\n")
        time.sleep(0.5)
        print(ser.read_all().decode('utf-8', errors='ignore').strip())
        
        print("\n=== FETCHING STATUS ===")
        ser.write(b"STATUS\n")
        time.sleep(0.5)
        print(ser.read_all().decode('utf-8', errors='ignore').strip())
        
        print("\n=== FETCHING LORA EUI ===")
        ser.write(b"EUI\n")
        time.sleep(0.5)
        print(ser.read_all().decode('utf-8', errors='ignore').strip())
        
        print("\n=== LISTENING TO LIVE LOGS (Press Ctrl+C to exit) ===")
        ser.timeout = 1 # Relax timeout for live reading
        while True:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print("  [NODE]:", line)
                    
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\n[ERROR] {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()

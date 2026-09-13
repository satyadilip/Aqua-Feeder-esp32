import os
import sys
import subprocess
import time

try:
    import serial.tools.list_ports
except ImportError:
    print("Error: 'pyserial' is not installed. Please run: pip install pyserial")
    sys.exit(1)

def get_esp32_ports():
    ports = serial.tools.list_ports.comports()
    esp_ports = []
    
    # Common USB-to-UART bridge keywords for ESP32/ESP8266
    keywords = ["cp210", "ch340", "ftdi", "usb serial", "usb jtag"]
    
    for port in ports:
        desc = port.description.lower()
        if any(kw in desc for kw in keywords):
            esp_ports.append(port)
            
    return esp_ports, ports

def main():
    print("="*50)
    print("   AquaFeeder Field Flasher Utility")
    print("="*50)
    
    bin_file = "AquaFeeder.bin" # Now acts as the universal firmware file
    if not os.path.exists(bin_file):
        print(f"\n[ERROR] Could not find {bin_file} in the current directory!")
        print("Please ensure this script is placed in the 'build' folder alongside the .bin files.")
        sys.exit(1)
        
    if not os.path.exists("AquaFeeder.ino.bootloader.bin") or not os.path.exists("AquaFeeder.ino.partitions.bin"):
        print("\n[ERROR] Missing bootloader or partitions binary!")
        sys.exit(1)

    print(f"\n[OK] Selected binary: {bin_file}")

    # 2. Scan COM Ports
    print("\nScanning for connected devices...")
    esp_ports, all_ports = get_esp32_ports()
    
    selected_port = None
    
    if len(esp_ports) == 1:
        port = esp_ports[0]
        print(f"Found ESP32 device on {port.device} ({port.description})")
        confirm = input("Use this port? (Y/n): ").strip().lower()
        if confirm == '' or confirm == 'y':
            selected_port = port.device
            
    if not selected_port:
        if len(all_ports) == 0:
            print("[ERROR] No COM ports found! Is the device plugged in?")
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
            except ValueError:
                pass
            print("Invalid choice.")
            
    print(f"\n[OK] Proceeding with {selected_port}")
    
    # 3. Flash using esptool
    print("\n" + "="*50)
    print(f"   FLASHING UNIVERSAL FIRMWARE TO {selected_port}   ")
    print("="*50)
    
    cmd = [
        sys.executable, "-m", "esptool",
        "--chip", "esp32s3",
        "--port", selected_port,
        "--baud", "921600",
        "--before", "default_reset",
        "--after", "hard_reset",
        "write_flash", "-z",
        "--flash_mode", "dio",
        "--flash_freq", "80m",
        "--flash_size", "16MB",
        "0x0", "AquaFeeder.ino.bootloader.bin",
        "0x8000", "AquaFeeder.ino.partitions.bin",
        "0x10000", bin_file
    ]
    
    print(f"\nExecuting: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*50)
        print(" 🎉 DEVICE FLASHED SUCCESSFULLY! 🎉")
        print("="*50)
        print("The device should be rebooting now.")
        print("Open a serial monitor (115200 baud) and type 'AUTH 8888' then 'GET LORA' to see its keys!")
    except subprocess.CalledProcessError:
        print("\n[ERROR] Flashing failed. Check the esptool output above.")
        
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()

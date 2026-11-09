import os
import sys
import subprocess
import time

def ensure_dependencies():
    """Checks and auto-installs pyserial and esptool if missing."""
    needed = []
    try:
        import serial.tools.list_ports
    except ImportError:
        needed.append("pyserial")
    try:
        import esptool
    except ImportError:
        needed.append("esptool")
        
    if needed:
        print(f"[INFO] Missing required library: {', '.join(needed)}")
        print("[INFO] Attempting automatic installation via pip...")
        try:
            cmd = [sys.executable, "-m", "pip", "install", *needed]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                print(f"[OK] Successfully installed {', '.join(needed)}!\n")
            else:
                print(f"[WARNING] Automatic pip install returned an issue:\n{res.stderr.strip()}")
                print(f"[TIP] You can also manually run: python -m pip install {' '.join(needed)}\n")
        except Exception as e:
            print(f"[WARNING] Could not run pip automatically: {e}\n")

# Run dependency check
ensure_dependencies()

class PortInfo:
    def __init__(self, device, description):
        self.device = device
        self.description = description

def get_ports_winreg():
    """Detect COM ports on Windows using standard library winreg (no dependencies required)."""
    ports = []
    if sys.platform.startswith('win'):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
            for i in range(winreg.QueryInfoKey(key)[1]):
                val = winreg.EnumValue(key, i)
                port_name = val[1]
                ports.append(PortInfo(port_name, f"Serial Device ({val[0]})"))
            key.Close()
        except Exception:
            pass
    return ports

def get_esp32_ports():
    all_ports = []
    try:
        import serial.tools.list_ports
        for p in serial.tools.list_ports.comports():
            all_ports.append(PortInfo(p.device, p.description))
    except Exception:
        all_ports = get_ports_winreg()

    keywords = ["cp210", "ch340", "ftdi", "usb serial", "usb jtag", "espressif", "uart", "cdc"]
    esp_ports = []
    for port in all_ports:
        desc = (port.description + " " + port.device).lower()
        if any(kw in desc for kw in keywords):
            esp_ports.append(port)
            
    return esp_ports, all_ports

def find_binary(search_names, directories):
    for d in directories:
        for name in search_names:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    return None

def main():
    print("="*55)
    print("      AquaFeeder Field Flasher Utility (Auto-Config)")
    print("="*55)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    root_dir = os.path.dirname(parent_dir)
    search_dirs = [script_dir, parent_dir, root_dir, os.getcwd()]

    # Locate main app binary
    bin_file = find_binary(["AquaFeeder.bin", "AquaFeeder.ino.bin"], search_dirs)
    bootloader_file = find_binary(["AquaFeeder.ino.bootloader.bin", "bootloader.bin"], search_dirs)
    partitions_file = find_binary(["AquaFeeder.ino.partitions.bin", "partitions.bin"], search_dirs)
    merged_file = find_binary(["AquaFeeder_merged.bin", "AquaFeeder_merged_v1.0.bin", "AquaFeeder.ino.merged.bin"], search_dirs)

    if not bin_file and not merged_file:
        print("\n[ERROR] Could not find AquaFeeder firmware binary (.bin)!")
        print("Please ensure this script is in the same folder as AquaFeeder.bin")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Scan COM Ports
    print("\nScanning for connected USB serial ports...")
    esp_ports, all_ports = get_esp32_ports()
    
    selected_port = None
    if len(esp_ports) == 1:
        port = esp_ports[0]
        print(f"\n[FOUND] Feeder USB port detected on: {port.device} ({port.description})")
        confirm = input(f"Flash to {port.device}? (Y/n): ").strip().lower()
        if confirm == '' or confirm == 'y':
            selected_port = port.device
            
    if not selected_port:
        if len(all_ports) == 0:
            print("\n[ERROR] No COM ports detected!")
            print("1. Check that the ESP32-S3 USB cable is plugged in firmly.")
            print("2. Ensure the USB cable supports data transfer (not charge-only).")
            print("3. Check Device Manager under 'Ports (COM & LPT)' to confirm driver.")
            input("\nPress Enter to exit...")
            sys.exit(1)
            
        print("\nAvailable COM Ports:")
        for i, port in enumerate(all_ports):
            print(f"  [{i+1}] {port.device} - {port.description}")
            
        while True:
            try:
                choice = input(f"\nSelect port number (1-{len(all_ports)}): ").strip()
                choice_idx = int(choice)
                if 1 <= choice_idx <= len(all_ports):
                    selected_port = all_ports[choice_idx-1].device
                    break
            except ValueError:
                pass
            print("Invalid choice. Please enter a valid number.")
            
    print(f"\n[OK] Target Port: {selected_port}")

    # Prepare esptool command
    # Check if we have merged bin or split bins
    if bootloader_file and partitions_file and bin_file:
        print(f"[OK] Firmware components located:")
        print(f"  - Bootloader: {os.path.basename(bootloader_file)}")
        print(f"  - Partitions: {os.path.basename(partitions_file)}")
        print(f"  - App:        {os.path.basename(bin_file)}")
        flash_args = [
            "0x0", bootloader_file,
            "0x8000", partitions_file,
            "0x10000", bin_file
        ]
    elif merged_file:
        print(f"[OK] Full merged flash image located: {os.path.basename(merged_file)}")
        flash_args = ["0x0", merged_file]
    else:
        print(f"[OK] Flashing App at 0x10000: {os.path.basename(bin_file)}")
        flash_args = ["0x10000", bin_file]

    # Check how esptool should be invoked
    esptool_exec = None
    try:
        import esptool
        esptool_exec = [sys.executable, "-m", "esptool"]
    except ImportError:
        import shutil
        if shutil.which("esptool"):
            esptool_exec = ["esptool"]
        elif shutil.which("esptool.exe"):
            esptool_exec = ["esptool.exe"]

    if not esptool_exec:
        print("\n[ERROR] 'esptool' is not found!")
        print("Please run this command to install it:")
        print("    python -m pip install esptool")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print("\n" + "="*55)
    print(f"   FLASHING FIRMWARE TO {selected_port}   ")
    print("="*55)
    
    cmd = esptool_exec + [
        "--chip", "esp32s3",
        "--port", selected_port,
        "--baud", "921600",
        "--before", "default_reset",
        "--after", "hard_reset",
        "write_flash", "-z",
        "--flash_mode", "dio",
        "--flash_freq", "80m",
        "--flash_size", "16MB"
    ] + flash_args
    
    print(f"\nExecuting: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*55)
        print("   SUCCESS! FIRMWARE FLASHED SUCCESSFULLY! ")
        print("="*55)
        print("The device is rebooting with the updated firmware.")
        print("The LCD will now display the new Diagnostics Menu!")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Flashing failed with exit code {e.returncode}.")
        print("If the device didn't respond, hold the BOOT button on the board,")
        print("press RST once, then release BOOT to put it in download mode and retry.")
        
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()

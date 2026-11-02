#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AquaDelta Wi-Fi Flasher - Local High-Speed Delta OTA Tool
Uploads a ~50 KB .adelta file to the AquaFeeder SoftAP in 2 seconds.
"""

import sys
import os
import argparse
import requests

def flash_delta(adelta_path, host="192.168.4.1", pin="8888"):
    if not os.path.exists(adelta_path):
        print(f"[ERROR] File not found: {adelta_path}")
        return False

    file_size = os.path.getsize(adelta_path)
    print(f"\n=======================================================")
    print(f"   AquaFeeder High-Speed Delta OTA (Wi-Fi AP)")
    print(f"=======================================================")
    print(f"  Target Feeder:   http://{host}")
    print(f"  Delta Patch:     {adelta_path} ({file_size/1024:.2f} KB)")
    print(f"=======================================================\n")

    url = f"http://{host}/api/ota/delta"
    
    try:
        print("[HTTP] Uploading delta patch to Feeder...")
        with open(adelta_path, "rb") as f:
            files = {"file": (os.path.basename(adelta_path), f, "application/octet-stream")}
            # Authenticate with technician PIN
            response = requests.post(url, files=files, auth=("admin", pin), timeout=30)

        if response.status_code == 200:
            print("[SUCCESS] Delta patch uploaded and accepted by Feeder!")
            print(f"Server response: {response.text}")
            print("\nFeeder is now reconstructing the full 1.2 MB firmware in PSRAM,")
            print("verifying cryptographic SHA-256 checksum, and rebooting into the new version!")
            return True
        else:
            print(f"[FAILED] HTTP Status {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AquaDelta Wi-Fi Local Flasher")
    parser.add_argument("--delta", required=True, help="Path to .adelta differential patch file")
    parser.add_argument("--host", default="192.168.4.1", help="Feeder IP or mDNS hostname (default: 192.168.4.1)")
    parser.add_argument("--pin", default="8888", help="Technician Admin PIN (default: 8888)")

    args = parser.parse_args()
    flash_delta(args.delta, args.host, args.pin)

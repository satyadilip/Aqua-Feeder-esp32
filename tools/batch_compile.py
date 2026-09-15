import os
import subprocess
import shutil
import re

print("Starting batch compilation for 5 nodes...")

for i in range(1, 6):
    print(f"\n--- Compiling for Node {i} (DevEUI ending in 0x0{i}) ---")
    
    # 1. Read config
    with open('AquaFeeder/config_manager.cpp', 'r') as f:
        content = f.read()
    
    # 2. Regex replace the last byte of DevEUI
    new_content = re.sub(r'0x00, 0x0[0-9] \};', f'0x00, 0x0{i} }};', content)
    with open('AquaFeeder/config_manager.cpp', 'w') as f:
        f.write(new_content)
        
    # 2b. Regex replace the DevAddr in lora_manager.cpp
    with open('AquaFeeder/lora_manager.cpp', 'r') as f:
        lora_content = f.read()
        
    # Matches: uint32_t devAddr = 0x0072A1F6;
    new_lora_content = re.sub(r'uint32_t devAddr = 0x0072A1F[0-9];', f'uint32_t devAddr = 0x0072A1F{i};', lora_content)
    with open('AquaFeeder/lora_manager.cpp', 'w') as f:
        f.write(new_lora_content)
        
    # 3. Run arduino-cli compile 
    cmd = [
        'arduino-cli', 'compile', 
        '-b', 'esp32:esp32:esp32s3', 
        '--board-options', 'FlashMode=qio,PSRAM=opi,FlashSize=16M', 
        '--export-binaries', 'AquaFeeder'
    ]
    if i == 1:
        cmd.append('--clean')
        
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error compiling Node {i}:\n{result.stderr}")
        break
        
    # 4. Copy the resulting bin
    src_bin = 'AquaFeeder/build/esp32.esp32.esp32s3/AquaFeeder.ino.bin'
    dst_bin = f'AquaFeeder/build/AquaFeeder_Node_{i}.bin'
    
    if os.path.exists(src_bin):
        shutil.copy(src_bin, dst_bin)
        print(f"Successfully generated {dst_bin}")
    else:
        print(f"Failed to find compiled bin for Node {i}")

print("\nBatch compilation complete!")

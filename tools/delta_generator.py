#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AquaDelta Generator - Differential Firmware Patch Tool
Optimized for AquaFeeder LoRaWAN & Low-Bandwidth OTA Updates

Shrinks full 1.2 MB ESP32-S3 firmware binaries down to ~50 KB - 70 KB
differential patches (.adelta) that can be transmitted over LoRaWAN or 
flashed in seconds over local Wi-Fi / Serial.
"""

import sys
import os
import struct
import zlib
import bz2
import hashlib
import argparse
import bsdiff4

MAGIC = b"AQUADELT" # 8 bytes
FORMAT_VERSION = 1

def cp_offtin(buf):
    y = buf[7] & 0x7F
    for i in range(6, -1, -1):
        y = y * 256 + buf[i]
    if buf[7] & 0x80:
        y = -y
    return y

def create_delta(old_path, new_path, out_path, chunk_size=96):
    print(f"[DELTA] Reading old binary: {old_path}")
    with open(old_path, "rb") as f:
        old_bytes = f.read()
    old_size = len(old_bytes)
    old_sha = hashlib.sha256(old_bytes).hexdigest()

    print(f"[DELTA] Reading new binary: {new_path}")
    with open(new_path, "rb") as f:
        new_bytes = f.read()
    new_size = len(new_bytes)
    new_sha = hashlib.sha256(new_bytes).hexdigest()
    new_sha_raw = hashlib.sha256(new_bytes).digest()

    print(f"  Old: {old_size:,} bytes | SHA256: {old_sha[:16]}...")
    print(f"  New: {new_size:,} bytes | SHA256: {new_sha[:16]}...")

    # 1. Compute BSDIFF
    print("[DELTA] Computing binary differential streams via BSDIFF...")
    raw_patch = bsdiff4.diff(old_bytes, new_bytes)
    ctrl_len, diff_len, new_sz = struct.unpack('<qqq', raw_patch[8:32])

    ctrl_raw = bz2.decompress(raw_patch[32 : 32 + ctrl_len])
    diff_raw = bz2.decompress(raw_patch[32 + ctrl_len : 32 + ctrl_len + diff_len])
    extra_raw = bz2.decompress(raw_patch[32 + ctrl_len + diff_len :])

    # 2. Compress each stream with standard RFC 1950 zlib (deflate)
    ctrl_comp = zlib.compress(ctrl_raw, 9)
    diff_comp = zlib.compress(diff_raw, 9)
    extra_comp = zlib.compress(extra_raw, 9)

    # 3. Build AquaDelta Header (80 bytes)
    header = struct.pack(
        '<8sHHIIIIIIIII32s',
        MAGIC,
        FORMAT_VERSION,
        0, # flags
        old_size,
        new_size,
        len(ctrl_comp),
        len(ctrl_raw),
        len(diff_comp),
        len(diff_raw),
        len(extra_comp),
        len(extra_raw),
        zlib.crc32(new_bytes),
        new_sha_raw
    )

    adelta_bytes = header + ctrl_comp + diff_comp + extra_comp
    patch_size = len(adelta_bytes)

    # 4. Verify reconstruction integrity before writing
    print("[DELTA] Verifying self-reconstruction integrity...")
    d_ctrl = zlib.decompress(ctrl_comp)
    d_diff = zlib.decompress(diff_comp)
    d_extra = zlib.decompress(extra_comp)

    restored = bytearray(new_size)
    oldpos = 0
    newpos = 0
    c_ptr = 0
    d_ptr = 0
    e_ptr = 0

    while newpos < new_size and c_ptr < len(d_ctrl):
        c0 = cp_offtin(d_ctrl[c_ptr : c_ptr + 8])
        c1 = cp_offtin(d_ctrl[c_ptr + 8 : c_ptr + 16])
        c2 = cp_offtin(d_ctrl[c_ptr + 16 : c_ptr + 24])
        c_ptr += 24

        for i in range(c0):
            restored[newpos + i] = (old_bytes[oldpos + i] + d_diff[d_ptr + i]) & 0xFF
        newpos += c0
        oldpos += c0
        d_ptr += c0

        restored[newpos : newpos + c1] = d_extra[e_ptr : e_ptr + c1]
        newpos += c1
        e_ptr += c1

        oldpos += c2

    if restored != new_bytes:
        raise ValueError("CRITICAL ERROR: Reconstructed binary does not match target new binary!")

    print(f"[DELTA] SUCCESS: Bit-for-bit target verification PASSED!")
    
    # 5. Write .adelta file
    with open(out_path, "wb") as f:
        f.write(adelta_bytes)

    ratio = (patch_size / float(new_size)) * 100.0
    saved = 100.0 - ratio
    print(f"\n=======================================================")
    print(f"   AquaDelta Differential File Generated Successfully!")
    print(f"=======================================================")
    print(f"  Target Binary:     {new_size:,} bytes ({new_size/1024:.1f} KB)")
    print(f"  AquaDelta Patch:   {patch_size:,} bytes ({patch_size/1024:.2f} KB)")
    print(f"  Bandwidth Savings: {saved:.1f}% reduction")
    print(f"  Output Path:       {out_path}")
    
    num_chunks = (patch_size + chunk_size - 1) // chunk_size
    print(f"  LoRaWAN Chunks:    {num_chunks} chunks (@ {chunk_size} bytes/chunk)")
    print(f"=======================================================\n")
    return adelta_bytes, num_chunks

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AquaDelta Firmware Differential Patch Generator")
    parser.add_argument("--old", required=True, help="Path to base/running firmware binary")
    parser.add_argument("--new", required=True, help="Path to new/target firmware binary")
    parser.add_argument("--out", default="firmware.adelta", help="Output .adelta file path")
    parser.add_argument("--chunk-size", type=int, default=96, help="Chunk size for LoRaWAN streaming (default: 96)")

    args = parser.parse_args()
    create_delta(args.old, args.new, args.out, args.chunk_size)

#!/usr/bin/env python3
"""
aquaCON Web Dashboard Comprehensive Automated Test Suite Runner
Runs all UI, Navigation, Persistence, Metrics, Tray Checks, and Field Diagnostics tests.
"""

import sys
import os
import subprocess
import time

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=" * 70)
    print("   aquaCON Web Dashboard - Comprehensive Automated Test Suite")
    print("=" * 70)
    print(f"Target URL: http://lorawan-telemetry-stack-webhostingbucket-djy9frtf8y6f.s3-website-us-east-1.amazonaws.com")
    print(f"Test Directory: {TEST_DIR}")
    print("=" * 70 + "\n")

    start_time = time.time()
    
    # Run pytest with verbose reporting
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        TEST_DIR,
        "-v",
        "--tb=short"
    ]

    res = subprocess.run(cmd, cwd=TEST_DIR)
    elapsed = round(time.time() - start_time, 2)

    print("\n" + "=" * 70)
    if res.returncode == 0:
        print(f"[SUCCESS] ALL AUTOMATED TEST CASES PASSED in {elapsed}s!")
    else:
        print(f"[FAILURE] Test suite finished with exit code {res.returncode} in {elapsed}s.")
    print("=" * 70 + "\n")

    sys.exit(res.returncode)

if __name__ == "__main__":
    main()

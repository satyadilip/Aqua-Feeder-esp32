"""
Script to parse SYSTEM_REQUIREMENTS_SPECIFICATION.md and generate all 215 requirements
as Doorstop YAML files (.doorstop/REQ/REQ-XXX.yml) with full traceability metadata.
"""

import os
import re
import yaml

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRS_PATH = os.path.join(WORKSPACE, "docs", "SYSTEM_REQUIREMENTS_SPECIFICATION.md")
REQS_DIR = os.path.join(WORKSPACE, "requirements", "reqs")

CATEGORY_MAP = {
    1: ("Power-On, Bootup & Hardware Bring-Up", "AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino"),
    2: ("20x4 LCD Physical Screen Layouts & Text Bounds", "AquaFeeder/lcd_display.cpp"),
    3: ("Keypad Input, Debouncing & Navigation", "AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino"),
    4: ("Menu System Pagination & Submenus", "AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino"),
    5: ("Settings, Limits & NVS Persistence", "AquaFeeder/config_manager.cpp;AquaFeeder/config.h"),
    6: ("Schedule Engine, Timing & Operational Window", "AquaFeeder/feed_engine.cpp"),
    7: ("3-Phase Dispensing Engine & Actuator Control", "AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp"),
    8: ("Safety Interlocks, Current Monitoring & Motor Trip", "AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp"),
    9: ("Hopper Level Sensing, Proximity & Hooter Alarm", "AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp"),
    10: ("Pause, Resume Engine & Manual Feed", "AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino"),
    11: ("Real-Time Clock, UTC/IST & Time Synchronization", "AquaFeeder/rtc_manager.cpp"),
    12: ("Wireless Telemetry & LoRaWAN Communications Contract", "AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp"),
    13: ("Web & Mobile Dashboard UI Contract", "web_dashboard/app.js;Cloud/api_lambda.py")
}

def parse_srs():
    with open(SRS_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    reqs = []
    current_cat_num = 1
    current_cat_title = ""

    for line in lines:
        line_s = line.strip()
        cat_match = re.search(r"### Category (\d+):\s*(.*)", line_s)
        if cat_match:
            current_cat_num = int(cat_match.group(1))
            current_cat_title = cat_match.group(2).split("(")[0].strip()
            continue

        if line_s.startswith("| **REQ-"):
            parts = [p.strip() for p in line_s.split("|")[1:-1]]
            if len(parts) >= 4:
                req_id_raw = parts[0].replace("**", "").strip()
                title = parts[1].strip()
                statement = parts[2].strip()
                method_raw = parts[3].strip()
                
                method = "Test"
                if "[I]" in method_raw:
                    method = "Inspect"
                elif "[A]" in method_raw:
                    method = "Analysis"
                elif "[D]" in method_raw:
                    method = "Demo"
                elif "[T]" in method_raw:
                    method = "Test"

                num = int(req_id_raw.replace("REQ-", ""))
                reqs.append({
                    "id": f"REQ-{num:03d}",
                    "num": num,
                    "title": title,
                    "statement": statement,
                    "method": method,
                    "category_num": current_cat_num,
                    "category_title": current_cat_title or CATEGORY_MAP.get(current_cat_num, ("", ""))[0]
                })

    return reqs

def main():
    print(f"Reading SRS from: {SRS_PATH}")
    reqs = parse_srs()
    print(f"Parsed {len(reqs)} requirements.")
    
    cat_counts = {}
    for r in reqs:
        c_num = r["category_num"]
        cat_counts[c_num] = cat_counts.get(c_num, 0) + 1
        sub_idx = cat_counts[c_num]
        r["level"] = f"{c_num}.{sub_idx}"

    os.makedirs(REQS_DIR, exist_ok=True)

    for r in reqs:
        uid = r["id"]
        filename = os.path.join(REQS_DIR, f"{uid}.yml")
        
        # Check if file exists to preserve verified status if already tested
        existing_status = "PENDING"
        existing_notes = ""
        existing_date = ""
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        existing_status = data.get("status", "PENDING")
                        existing_notes = data.get("test_notes", "")
                        existing_date = data.get("verified_date", "")
            except Exception:
                pass

        cat_info = CATEGORY_MAP.get(r["category_num"], ("General", ""))
        item_data = {
            "active": True,
            "category": f"Cat {r['category_num']}: {r['category_title']}",
            "derived": False,
            "hardware_target": "Feeder 03 (ESP32-S3)",
            "header": r["title"],
            "level": r["level"],
            "links": [],
            "method": r["method"],
            "normative": True,
            "ref": cat_info[1],
            "reviewed": None,
            "status": existing_status,
            "test_notes": existing_notes,
            "text": r["statement"],
            "verified_date": existing_date
        }

        with open(filename, "w", encoding="utf-8") as f:
            yaml.dump(item_data, f, default_flow_style=False, sort_keys=True, allow_unicode=True)

    print(f"Directly wrote {len(reqs)} Doorstop YAML files into {REQS_DIR}.")

if __name__ == "__main__":
    main()

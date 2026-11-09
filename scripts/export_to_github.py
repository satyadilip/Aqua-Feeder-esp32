"""
Export Doorstop Requirements to GitHub Issues (JSON, CSV, and Direct REST API Push).
"""

import os
import csv
import json
import yaml
import glob
import argparse

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQS_DIR = os.path.join(WORKSPACE, "requirements", "reqs")
DOCS_DIR = os.path.join(WORKSPACE, "docs")

def load_doorstop_items():
    yaml_files = sorted(glob.glob(os.path.join(REQS_DIR, "REQ-*.yml")))
    items = []
    for yf in yaml_files:
        with open(yf, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            uid = os.path.splitext(os.path.basename(yf))[0]
            data["uid"] = uid
            items.append(data)
    return items

def format_issue_body(item):
    uid = item["uid"]
    header = item.get("header", "").strip()
    text = item.get("text", "").strip()
    category = item.get("category", "")
    method = item.get("method", "Test")
    target = item.get("hardware_target", "Feeder 03 (ESP32-S3)")
    ref = item.get("ref", "Firmware")
    status = item.get("status", "PENDING")
    test_notes = item.get("test_notes", "")
    verified_date = item.get("verified_date", "")

    pass_checked = "[x]" if status == "PASSED" else "[ ]"
    fail_checked = "[x]" if status == "FAILED" else "[ ]"

    body = f"""### 📋 Requirement Specification
- **ID**: `{uid}`
- **Category**: {category}
- **Verification Method**: `[{method[0]}] {method}`
- **Target Hardware**: {target}
- **Source Reference**: `{ref}`

### 📝 Requirement Statement
> {text}

---

### 🧪 Verification & Acceptance Criteria
- [ ] **Pre-Conditions**: System powered on and target peripherals initialized.
- [ ] **Success Case 1**: Normal operation complies strictly with the requirement statement without exception.
- [ ] **Success Case 2**: Timing, electrical levels, display text bounds (20x4), or telemetry bounds are within tolerance.
- [ ] **Failure / Boundary Condition**: Fault injection or abnormal state is gracefully trapped without crash or infinite loop.

---

### ✍️ Test Execution & Hardware Sign-Off
- **Status**: {pass_checked} PASS  {fail_checked} FAIL
- **Verified Date**: {verified_date or 'YYYY-MM-DD'}
- **Test Notes / Logs**:
{test_notes or '*(Record serial monitor logs, test bench observations, or attach photo here)*'}

> [!IMPORTANT]
> This requirement MUST NOT be closed until all checkboxes above are checked and verified on physical hardware.
"""
    return body

def export_json(items, output_path):
    issues = []
    for item in items:
        uid = item["uid"]
        header = item.get("header", "").strip()
        category = item.get("category", "").split(":")[0].strip()
        method = item.get("method", "Test")
        status = item.get("status", "PENDING").lower()

        issue = {
            "title": f"[{uid}] {header}",
            "body": format_issue_body(item),
            "labels": ["requirement", f"cat:{category.lower().replace(' ', '-')}", f"method:{method.lower()}", f"status:{status}"],
            "uid": uid
        }
        issues.append(issue)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(issues, f, indent=2)
    print(f"Exported {len(issues)} issues to JSON: {output_path}")
    return issues

def export_csv(items, output_path):
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["UID", "Title", "Category", "Method", "Status", "Reference", "Body"])
        for item in items:
            uid = item["uid"]
            header = item.get("header", "").strip()
            category = item.get("category", "")
            method = item.get("method", "Test")
            status = item.get("status", "PENDING")
            ref = item.get("ref", "")
            body = format_issue_body(item)
            writer.writerow([uid, f"[{uid}] {header}", category, method, status, ref, body])
    print(f"Exported {len(items)} issues to CSV: {output_path}")

def push_to_github(issues, token, repo="satyadilip/Aqua-Feeder-esp32", limit=None):
    import requests
    import time

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/repos/{repo}/issues"
    
    # Check rate limit / auth first
    resp = requests.get(f"https://api.github.com/repos/{repo}", headers=headers)
    if resp.status_code != 200:
        print(f"ERROR: GitHub API authentication failed ({resp.status_code}): {resp.text}")
        return

    print(f"Authenticated with {repo}. Creating issues...")
    created = 0
    to_push = issues[:limit] if limit else issues

    for idx, iss in enumerate(to_push):
        payload = {
            "title": iss["title"],
            "body": iss["body"],
            "labels": iss["labels"]
        }
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 201:
            issue_data = r.json()
            created += 1
            print(f"[{created}/{len(to_push)}] Created #{issue_data['number']}: {iss['title']}")
        else:
            print(f"Failed to create {iss['title']}: {r.status_code} {r.text}")
        time.sleep(0.5) # gentle rate limiting

    print(f"Finished creating {created} GitHub Issues!")

def main():
    parser = argparse.ArgumentParser(description="Export Doorstop requirements to GitHub Issues")
    parser.add_argument("--json", action="store_true", default=True, help="Export JSON file")
    parser.add_argument("--csv", action="store_true", default=True, help="Export CSV file")
    parser.add_argument("--push", action="store_true", help="Push directly to GitHub API")
    parser.add_argument("--token", help="GitHub Personal Access Token (or GITHUB_TOKEN env var)")
    parser.add_argument("--limit", type=int, help="Limit number of issues to push for testing")
    args = parser.parse_args()

    items = load_doorstop_items()
    print(f"Loaded {len(items)} Doorstop requirements.")

    json_path = os.path.join(DOCS_DIR, "github_issues.json")
    csv_path = os.path.join(DOCS_DIR, "github_issues.csv")

    issues = export_json(items, json_path)
    export_csv(items, csv_path)

    if args.push:
        token = args.token or os.environ.get("GITHUB_TOKEN")
        if not token:
            print("ERROR: --push requires a GitHub Personal Access Token (--token or GITHUB_TOKEN env var)")
            return
        push_to_github(issues, token, limit=args.limit)

if __name__ == "__main__":
    main()

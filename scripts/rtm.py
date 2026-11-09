"""
aquaCON™ Unified Requirements Traceability Matrix (RTM) Manager
Connects Doorstop (Docs-as-Code) and GitHub Issues / Projects into a single CLI tool.
"""

import os
import sys
import glob
import yaml
import json
import argparse
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQS_DIR = os.path.join(WORKSPACE, "requirements", "reqs")
DOCS_DIR = os.path.join(WORKSPACE, "docs")
MATRIX_MD_PATH = os.path.join(DOCS_DIR, "TRACEABILITY_MATRIX.md")
MATRIX_HTML_PATH = os.path.join(DOCS_DIR, "TRACEABILITY_MATRIX.html")

def load_all_items():
    yaml_files = sorted(glob.glob(os.path.join(REQS_DIR, "REQ-*.yml")))
    items = []
    for yf in yaml_files:
        with open(yf, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            uid = os.path.splitext(os.path.basename(yf))[0]
            data["uid"] = uid
            data["_filepath"] = yf
            items.append(data)
    return items

def show_status(items):
    total = len(items)
    passed = sum(1 for i in items if i.get("status") == "PASSED")
    failed = sum(1 for i in items if i.get("status") == "FAILED")
    pending = total - passed - failed

    pct_passed = (passed / total * 100) if total else 0
    pct_failed = (failed / total * 100) if total else 0

    bar_len = 30
    pass_bars = int(round(bar_len * (passed / total))) if total else 0
    fail_bars = int(round(bar_len * (failed / total))) if total else 0
    pend_bars = bar_len - pass_bars - fail_bars
    progress_bar = f"[{'#' * pass_bars}{'X' * fail_bars}{'-' * pend_bars}]"

    print("\n" + "=" * 70)
    print("       aquaCON(TM) REQUIREMENTS TRACEABILITY MATRIX (RTM)       ")
    print("=" * 70)
    print(f"Total Requirements : {total}")
    print(f"Verified & PASSED  : {passed:<4} ({pct_passed:.1f}%)")
    print(f"Test FAILED        : {failed:<4} ({pct_failed:.1f}%)")
    print(f"PENDING Testing    : {pending:<4} ({(pending/total*100):.1f}%)")
    print(f"Overall Progress   : {progress_bar} {pct_passed:.1f}%\n")

    # Group by category
    cats = {}
    for i in items:
        cat = i.get("category", "General")
        if cat not in cats:
            cats[cat] = {"total": 0, "passed": 0, "failed": 0, "pending": 0}
        cats[cat]["total"] += 1
        st = i.get("status", "PENDING")
        if st == "PASSED":
            cats[cat]["passed"] += 1
        elif st == "FAILED":
            cats[cat]["failed"] += 1
        else:
            cats[cat]["pending"] += 1

    print(f"{'Category':<50} | {'Pass':<5} | {'Fail':<5} | {'Pend':<5} | {'Ratio'}")
    print("-" * 75)
    for cat_name, c in cats.items():
        short_cat = cat_name[:48]
        ratio = f"{c['passed']}/{c['total']}"
        print(f"{short_cat:<50} | {c['passed']:<5} | {c['failed']:<5} | {c['pending']:<5} | {ratio}")
    print("=" * 75 + "\n")

def verify_requirement(uid, status, notes=""):
    uid = uid.upper()
    if not uid.startswith("REQ-"):
        uid = f"REQ-{int(uid):03d}"

    filename = os.path.join(REQS_DIR, f"{uid}.yml")
    if not os.path.exists(filename):
        print(f"ERROR: Requirement file not found: {filename}")
        return False

    with open(filename, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    status_upper = status.upper()
    if status_upper not in ["PASSED", "FAILED", "PENDING", "PASS", "FAIL"]:
        print("ERROR: Status must be PASS, FAIL, or PENDING")
        return False

    final_status = "PASSED" if status_upper in ["PASS", "PASSED"] else ("FAILED" if status_upper in ["FAIL", "FAILED"] else "PENDING")
    
    data["status"] = final_status
    data["test_notes"] = notes.strip()
    data["verified_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=True, allow_unicode=True)

    print(f"Updated {uid}: Status = {final_status}")
    if notes:
        print(f"Evidence / Notes: {notes}")

    # Re-review in doorstop
    os.system(f"doorstop review {uid} >nul 2>&1")

    # Regenerate matrix
    generate_matrix()
    return True

def generate_matrix():
    items = load_all_items()
    total = len(items)
    passed = sum(1 for i in items if i.get("status") == "PASSED")
    failed = sum(1 for i in items if i.get("status") == "FAILED")
    pending = total - passed - failed
    pct = (passed / total * 100) if total else 0

    # 1. Generate Markdown Matrix
    md = []
    md.append("# aquaCON™ Requirements Traceability & Verification Matrix\n")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    md.append(f"**Compliance Standard:** ISO/IEC/IEEE 29148:2018  ")
    md.append(f"**Status:** {passed}/{total} Passed ({pct:.1f}%) | {failed} Failed | {pending} Pending\n")
    md.append("---\n")
    md.append("| UID | Category | Title | Method | Target | Status | Verified Date | Reference |")
    md.append("|:---|:---|:---|:---:|:---:|:---:|:---:|:---|")

    for i in items:
        uid = i["uid"]
        cat = i.get("category", "").split(":")[0]
        header = i.get("header", "").strip()
        method = i.get("method", "Test")
        target = i.get("hardware_target", "Feeder 03")
        status = i.get("status", "PENDING")
        vdate = i.get("verified_date", "-")
        ref = i.get("ref", "-")

        badge = "**PASSED**" if status == "PASSED" else ("`FAILED`" if status == "FAILED" else "*PENDING*")
        md.append(f"| **{uid}** | {cat} | {header} | [{method[0]}] | {target} | {badge} | {vdate} | `{ref}` |")

    with open(MATRIX_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Generated Traceability Matrix (Markdown): {MATRIX_MD_PATH}")

    # 2. Generate HTML Matrix with interactive styling
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>aquaCON™ Requirements Traceability Matrix</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px 40px; background: #0f172a; color: #f8fafc; }}
  h1 {{ color: #38bdf8; margin-bottom: 4px; }}
  .meta {{ color: #94a3b8; font-size: 14px; margin-bottom: 20px; }}
  .kpis {{ display: flex; gap: 16px; margin-bottom: 24px; }}
  .card {{ background: #1e293b; padding: 14px 20px; border-radius: 8px; border: 1px solid #334155; min-width: 140px; }}
  .card .num {{ font-size: 28px; font-weight: 700; color: #f8fafc; }}
  .card .lbl {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; }}
  .card.pass .num {{ color: #22c55e; }}
  .card.fail .num {{ color: #ef4444; }}
  .card.pend .num {{ color: #eab308; }}
  table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; font-size: 13px; }}
  th {{ background: #334155; text-align: left; padding: 10px 12px; font-weight: 600; color: #cbd5e1; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #334155; vertical-align: middle; }}
  tr:hover {{ background: #243248; }}
  .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }}
  .badge-pass {{ background: #14532d; color: #4ade80; border: 1px solid #22c55e; }}
  .badge-fail {{ background: #7f1d1d; color: #f87171; border: 1px solid #ef4444; }}
  .badge-pend {{ background: #713f12; color: #fde047; border: 1px solid #eab308; }}
  code {{ font-family: monospace; font-size: 12px; color: #38bdf8; }}
</style>
</head>
<body>
<h1>aquaCON™ Requirements Traceability Matrix (RTM)</h1>
<div class="meta">ISO/IEC/IEEE 29148:2018 Engineering Specification & Verification Traceability</div>
<div class="kpis">
  <div class="card"><div class="num">{total}</div><div class="lbl">Total Reqs</div></div>
  <div class="card pass"><div class="num">{passed}</div><div class="lbl">Passed ({pct:.1f}%)</div></div>
  <div class="card fail"><div class="num">{failed}</div><div class="lbl">Failed</div></div>
  <div class="card pend"><div class="num">{pending}</div><div class="lbl">Pending Test</div></div>
</div>
<table>
<thead>
  <tr><th>UID</th><th>Category</th><th>Title</th><th>Method</th><th>Target</th><th>Status</th><th>Verified Date</th><th>Reference</th></tr>
</thead>
<tbody>
"""
    for i in items:
        uid = i["uid"]
        cat = i.get("category", "")
        header = i.get("header", "").strip()
        method = i.get("method", "Test")
        target = i.get("hardware_target", "Feeder 03")
        status = i.get("status", "PENDING")
        vdate = i.get("verified_date", "-")
        ref = i.get("ref", "-")
        badge_cls = "badge-pass" if status == "PASSED" else ("badge-fail" if status == "FAILED" else "badge-pend")
        html += f"""  <tr>
    <td><b>{uid}</b></td>
    <td>{cat}</td>
    <td>{header}</td>
    <td>[{method[0]}] {method}</td>
    <td>{target}</td>
    <td><span class="badge {badge_cls}">{status}</span></td>
    <td>{vdate}</td>
    <td><code>{ref}</code></td>
  </tr>\n"""

    html += """</tbody>
</table>
</body>
</html>"""
    with open(MATRIX_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated Traceability Matrix (HTML): {MATRIX_HTML_PATH}")

def main():
    parser = argparse.ArgumentParser(description="aquaCON Requirements Traceability Manager")
    subparsers = parser.add_subparsers(dest="command")

    # Status
    subparsers.add_parser("status", help="Show verification status and progress")

    # Verify
    verify_p = subparsers.add_parser("verify", help="Update requirement verification status")
    verify_p.add_argument("uid", help="Requirement UID (e.g. REQ-001 or 1)")
    verify_p.add_argument("--status", required=True, choices=["PASS", "FAIL", "PENDING"], help="Test outcome")
    verify_p.add_argument("--notes", default="", help="Test notes or serial log evidence")

    # Matrix
    subparsers.add_parser("matrix", help="Regenerate HTML and Markdown Traceability Matrix")

    # Export GitHub
    subparsers.add_parser("export-github", help="Regenerate GitHub Issues CSV & JSON")

    args = parser.parse_args()

    if args.command == "status" or not args.command:
        items = load_all_items()
        show_status(items)
    elif args.command == "verify":
        verify_requirement(args.uid, args.status, args.notes)
    elif args.command == "matrix":
        generate_matrix()
    elif args.command == "export-github":
        os.system(f"python {os.path.join(os.path.dirname(__file__), 'export_to_github.py')}")

if __name__ == "__main__":
    main()

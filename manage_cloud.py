#!/usr/bin/env python3
"""
aquaCON™ Cloud & AWS Deployment Management CLI
Athena Engineering Corp.

Usage:
    python manage_cloud.py check        # Test connection to AWS S3, Lambda, DynamoDB, API Gateway
    python manage_cloud.py status       # Check live device states and latest telemetry from DynamoDB
    python manage_cloud.py deploy-web   # Deploy web dashboard & PWA assets to S3
    python manage_cloud.py deploy-api   # Deploy api_lambda.py to AquaFeederApiHandler
    python manage_cloud.py deploy-tel   # Deploy lambda_function.py to AquaFeederTelemetryProcessor
    python manage_cloud.py deploy-all   # Deploy all Lambdas and Web Dashboard in one shot
    python manage_cloud.py test         # Run headless end-to-end verification test suite
"""

import sys
import os
import time
import zipfile
import mimetypes
import argparse
import urllib.request
import json
import boto3

# Ensure UTF-8 output encoding for Windows terminal
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(ROOT_DIR, 'web_dashboard')

# Load credentials from environment or gitignored local credentials file
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

creds_file = os.path.join(ROOT_DIR, 'scratch', 'aws_creds.json')
if not AWS_ACCESS_KEY_ID and os.path.exists(creds_file):
    try:
        with open(creds_file, 'r', encoding='utf-8') as f:
            c = json.load(f)
            AWS_ACCESS_KEY_ID = c.get('AWS_ACCESS_KEY_ID')
            AWS_SECRET_ACCESS_KEY = c.get('AWS_SECRET_ACCESS_KEY')
            AWS_REGION = c.get('AWS_REGION', AWS_REGION)
    except Exception:
        pass

S3_BUCKET = 'lorawan-telemetry-stack-webhostingbucket-djy9frtf8y6f'
S3_URL = f"http://{S3_BUCKET}.s3-website-{AWS_REGION}.amazonaws.com"
API_BASE_URL = 'https://s1ilr3py74.execute-api.us-east-1.amazonaws.com/prod'

LAMBDA_API = 'AquaFeederApiHandler'
LAMBDA_TEL = 'AquaFeederTelemetryProcessor'

def get_boto3_session():
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        return boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
    return boto3.Session(region_name=AWS_REGION)

def check_connection():
    print("=========================================================================")
    print("         aquaCON™ AWS CLOUD CONNECTIVITY & HEALTH CHECK")
    print("=========================================================================")
    session = get_boto3_session()

    # 1. Test S3 Bucket
    print("\n[1/5] Checking AWS S3 Web Hosting Bucket...")
    try:
        s3 = session.client('s3')
        head = s3.head_bucket(Bucket=S3_BUCKET)
        print(f"  [PASS] Bucket '{S3_BUCKET}' is reachable.")
        print(f"  Live URL: {S3_URL}")
    except Exception as e:
        print(f"  [FAIL] S3 Bucket error: {e}")

    # 2. Test Lambda Functions
    print("\n[2/5] Checking AWS Lambda Services...")
    lam = session.client('lambda')
    for fn in [LAMBDA_API, LAMBDA_TEL]:
        try:
            res = lam.get_function(FunctionName=fn)
            config = res.get('Configuration', {})
            state = config.get('State', 'Active')
            last_mod = config.get('LastModified')
            print(f"  [PASS] Lambda '{fn}': State={state}, LastModified={last_mod}")
        except Exception as e:
            print(f"  [FAIL] Lambda '{fn}' error: {e}")

    # 3. Test DynamoDB Tables
    print("\n[3/5] Checking DynamoDB Tables...")
    dynamo = session.client('dynamodb')
    tables = ['AquaFeeder_Devices', 'AquaFeeder_Telemetry', 'AquaFeeder_DailyMetrics', 'AquaFeeder_Settings']
    for t in tables:
        try:
            res = dynamo.describe_table(TableName=t)
            status = res.get('Table', {}).get('TableStatus')
            count = res.get('Table', {}).get('ItemCount', 0)
            print(f"  [PASS] DynamoDB '{t}': Status={status}, Items≈{count}")
        except Exception as e:
            print(f"  [FAIL] DynamoDB '{t}' error: {e}")

    # 4. Test API Gateway Endpoint
    print("\n[4/5] Checking API Gateway Live Endpoint...")
    try:
        req = urllib.request.Request(f"{API_BASE_URL}/api/devices?_t={int(time.time())}", headers={'User-Agent': 'manage_cloud'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            dev_count = len(data.get('devices', []))
            print(f"  [PASS] API Gateway HTTP {resp.status}: {dev_count} devices registered.")
    except Exception as e:
        print(f"  [FAIL] API Gateway error: {e}")

    # 5. Test Live Website HTTP response
    print("\n[5/5] Checking S3 Static Website Endpoint...")
    try:
        req = urllib.request.Request(f"{S3_URL}/index.html?_t={int(time.time())}", headers={'User-Agent': 'manage_cloud'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            print(f"  [PASS] Web App HTTP {resp.status}, Size={len(content)} bytes.")
    except Exception as e:
        print(f"  [FAIL] Web App error: {e}")

    print("\n=========================================================================")
    print("Health check completed.")
    print("=========================================================================")

def show_device_status():
    print("=========================================================================")
    print("               aquaCON™ REAL-TIME DEVICE STATUS REPORT")
    print("=========================================================================")
    session = get_boto3_session()
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table('AquaFeeder_Devices')

    try:
        res = table.scan()
        items = res.get('Items', [])
        print(f"Found {len(items)} registered devices:\n")
        print(f"{'Device ID':<18} {'Device Name':<28} {'Status':<14} {'Feed Dispensed':<16} {'Events Done':<12}")
        print("-" * 90)
        for it in items:
            dev_id = str(it.get('DeviceId', ''))
            name = str(it.get('DeviceName', ''))[:26]
            status = str(it.get('Status', 'STANDBY'))
            disp = f"{float(it.get('DispensedFeed_kg', 0)):.1f} / {float(it.get('DailyTarget_kg', 15)):.1f} kg"
            events = f"{it.get('CurrentEvent', 0)} / {it.get('TotalEvents', 150)}"
            print(f"{dev_id:<18} {name:<28} {status:<14} {disp:<16} {events:<12}")
    except Exception as e:
        print("Error reading devices:", e)
    print("=========================================================================")

def deploy_web():
    print("=========================================================================")
    print(f"  Deploying Web Dashboard to S3: s3://{S3_BUCKET}")
    print("=========================================================================")
    session = get_boto3_session()
    s3 = session.client('s3')

    if not os.path.exists(WEB_DIR):
        print(f"Error: Directory '{WEB_DIR}' not found.")
        sys.exit(1)

    uploaded = 0
    for fname in os.listdir(WEB_DIR):
        fpath = os.path.join(WEB_DIR, fname)
        if os.path.isfile(fpath):
            ctype, _ = mimetypes.guess_type(fpath)
            if not ctype:
                if fname.endswith('.html'): ctype = 'text/html'
                elif fname.endswith('.js'): ctype = 'application/javascript'
                elif fname.endswith('.css'): ctype = 'text/css'
                elif fname.endswith('.json'): ctype = 'application/json'
                else: ctype = 'text/plain'

            print(f"  Uploading: {fname:<24} ({ctype})")
            s3.upload_file(
                fpath, S3_BUCKET, fname,
                ExtraArgs={
                    'ContentType': ctype,
                    'CacheControl': 'max-age=0, no-cache, no-store, must-revalidate'
                }
            )
            uploaded += 1

    print(f"\n[PASS] Successfully uploaded {uploaded} assets to S3.")
    print(f"Live Production URL: {S3_URL}")

def deploy_api_lambda():
    print("=========================================================================")
    print(f"  Packaging & Deploying API Lambda: {LAMBDA_API}")
    print("=========================================================================")
    session = get_boto3_session()
    lam = session.client('lambda')

    src = os.path.join(ROOT_DIR, 'api_lambda.py')
    zip_path = os.path.join(ROOT_DIR, 'api_lambda.zip')

    if not os.path.exists(src):
        print(f"Error: Source file '{src}' not found.")
        sys.exit(1)

    print("  Creating api_lambda.zip...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(src, 'api_lambda.py')

    print(f"  Updating Lambda function code for '{LAMBDA_API}'...")
    with open(zip_path, 'rb') as f:
        res = lam.update_function_code(FunctionName=LAMBDA_API, ZipFile=f.read())
    print(f"  [PASS] Deployed! Revision: {res.get('RevisionId')}, Modified: {res.get('LastModified')}")

def deploy_telemetry_lambda():
    print("=========================================================================")
    print(f"  Packaging & Deploying Telemetry Lambda: {LAMBDA_TEL}")
    print("=========================================================================")
    session = get_boto3_session()
    lam = session.client('lambda')

    src = os.path.join(ROOT_DIR, 'lambda_function.py')
    zip_path = os.path.join(ROOT_DIR, 'lambda_function.zip')

    if not os.path.exists(src):
        print(f"Error: Source file '{src}' not found.")
        sys.exit(1)

    print("  Creating lambda_function.zip...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(src, 'lambda_function.py')

    print(f"  Updating Lambda function code for '{LAMBDA_TEL}'...")
    with open(zip_path, 'rb') as f:
        res = lam.update_function_code(FunctionName=LAMBDA_TEL, ZipFile=f.read())
    print(f"  [PASS] Deployed! Revision: {res.get('RevisionId')}, Modified: {res.get('LastModified')}")

def deploy_all():
    deploy_api_lambda()
    print()
    deploy_telemetry_lambda()
    print()
    deploy_web()

def run_e2e_tests():
    print("=========================================================================")
    print("  Executing Autonomous Live Production E2E Verification Suite")
    print("=========================================================================")
    test_script = os.path.join(ROOT_DIR, 'scratch', 'comprehensive_e2e_test.py')
    if os.path.exists(test_script):
        os.system(f'"{sys.executable}" "{test_script}"')
    else:
        print(f"Test script not found at: {test_script}")

def main():
    parser = argparse.ArgumentParser(description="aquaCON™ Cloud Management & Deployment Automation CLI")
    subparsers = parser.add_subparsers(dest='command', help='Action to perform')

    subparsers.add_parser('check', help='Check AWS connectivity, S3, Lambdas, and DynamoDB')
    subparsers.add_parser('status', help='View live device statuses and telemetry counts')
    subparsers.add_parser('deploy-web', help='Deploy web dashboard to S3')
    subparsers.add_parser('deploy-api', help='Deploy api_lambda.py to AquaFeederApiHandler')
    subparsers.add_parser('deploy-tel', help='Deploy lambda_function.py to AquaFeederTelemetryProcessor')
    subparsers.add_parser('deploy-all', help='Deploy both Lambdas and the web dashboard in one shot')
    subparsers.add_parser('test', help='Run autonomous headless browser E2E tests against production')

    args = parser.parse_args()

    if args.command == 'check':
        check_connection()
    elif args.command == 'status':
        show_device_status()
    elif args.command == 'deploy-web':
        deploy_web()
    elif args.command == 'deploy-api':
        deploy_api_lambda()
    elif args.command == 'deploy-tel':
        deploy_telemetry_lambda()
    elif args.command == 'deploy-all':
        deploy_all()
    elif args.command == 'test':
        run_e2e_tests()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

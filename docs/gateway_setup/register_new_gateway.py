import boto3
import argparse
import sys
import os

def register_gateway(eui, region_name='us-east-1'):
    print(f"[*] Connecting to AWS in {region_name}...")
    iot = boto3.client('iot', region_name=region_name)
    iotw = boto3.client('iotwireless', region_name=region_name)
    sts = boto3.client('sts', region_name=region_name)
    
    account_id = sts.get_caller_identity()['Account']
    
    # 1. Create Wireless Gateway in AWS IoT Wireless
    print(f"[*] Registering Wireless Gateway with EUI {eui}...")
    try:
        gw = iotw.create_wireless_gateway(
            Name=f"SenseCAP_{eui}",
            LoRaWAN={'GatewayEui': eui, 'RfRegion': 'IN865'}
        )
        gw_id = gw['Id']
        print(f"[SUCCESS] Created Wireless Gateway: {gw_id}")
    except Exception as e:
        print(f"[ERROR] Failed to create Wireless Gateway: {e}")
        sys.exit(1)
        
    # 2. Create IoT Thing
    thing_name = f"Gateway_{gw_id}"
    print(f"[*] Creating IoT Thing {thing_name}...")
    iot.create_thing(thingName=thing_name)
    
    # 3. Create Certificates
    print("[*] Generating certificates...")
    cert = iot.create_keys_and_certificate(setAsActive=True)
    cert_arn = cert['certificateArn']
    cert_id = cert['certificateId']
    
    # 4. Attach Policies and Associations
    print("[*] Attaching policies and associating entities...")
    # Make sure 'WirelessGatewayPolicy' exists in your AWS account!
    try:
        iot.attach_policy(policyName='WirelessGatewayPolicy', target=cert_arn)
    except Exception as e:
        print(f"[WARNING] Could not attach WirelessGatewayPolicy. Make sure it exists! {e}")
        
    iot.attach_thing_principal(thingName=thing_name, principal=cert_arn)
    
    # The CRITICAL step that fixes the "Connection was reset by peer" error
    iotw.associate_wireless_gateway_with_thing(Id=gw_id, ThingArn=f"arn:aws:iot:{region_name}:{account_id}:thing/{thing_name}")
    iotw.associate_wireless_gateway_with_certificate(Id=gw_id, IotCertificateId=cert_id)
    
    # 5. Save certificates to file
    with open('cert.pem', 'w') as f:
        f.write(cert['certificatePem'])
    with open('private.key', 'w') as f:
        f.write(cert['keyPair']['PrivateKey'])
        
    print("\n[SUCCESS] Gateway registered perfectly!")
    print("Files 'cert.pem' and 'private.key' have been created in this folder.")
    print("Upload these to your Gateway's Web UI along with the Amazon Root CA 1.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Register a LoRaWAN Gateway in AWS IoT Core")
    parser.add_argument("eui", help="The 16-character Gateway EUI (e.g. 2CF7F11080101354)")
    args = parser.parse_args()
    
    if len(args.eui) != 16:
        print("[ERROR] EUI must be exactly 16 characters long.")
        sys.exit(1)
        
    register_gateway(args.eui)

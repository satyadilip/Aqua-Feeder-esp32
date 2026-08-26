import boto3

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
iotwireless = session.client('iotwireless')

print("=== ACTIVE AWS IOT WIRELESS GATEWAYS ===")
gws = iotwireless.list_wireless_gateways()['WirelessGatewayList']
for g in gws:
    gw_id = g['Id']
    info = iotwireless.get_wireless_gateway(Identifier=gw_id, IdentifierType='WirelessGatewayId')
    print(f"  ID: {gw_id} | Name: {g.get('Name')} | EUI: {info.get('LoRaWAN', {}).get('GatewayEui')}")
    try:
        st = iotwireless.get_wireless_gateway_statistics(WirelessGatewayId=gw_id)
        print(f"     Status: {st.get('ConnectionStatus')} | Last Uplink: {st.get('LastUplinkReceivedAt')}")
    except Exception as e:
        print(f"     Stat error: {e}")

print("\n=== ACTIVE AWS IOT WIRELESS DEVICES ===")
devs = iotwireless.list_wireless_devices()['WirelessDeviceList']
for d in devs:
    dev_id = d['Id']
    info = iotwireless.get_wireless_device(Identifier=dev_id, IdentifierType='WirelessDeviceId')
    print(f"  ID: {dev_id} | Name: {d.get('Name')} | DevEUI: {info.get('LoRaWAN', {}).get('DevEui')}")
    try:
        st = iotwireless.get_wireless_device_statistics(WirelessDeviceId=dev_id)
        print(f"     Last Uplink: {st.get('LastUplinkReceivedAt')}")
    except Exception as e:
        print(f"     Stat error: {e}")

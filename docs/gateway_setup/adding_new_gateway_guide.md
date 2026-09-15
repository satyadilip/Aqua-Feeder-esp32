# Adding and Configuring a New SenseCAP M2 Gateway for AWS IoT Core

Follow these steps to correctly register a new SenseCAP M2 gateway in AWS IoT Core and configure it, avoiding known firmware bugs and common pitfalls.

## 1. Determine the Gateway EUI
You will need a 16-character Gateway EUI. Usually, this is printed on the gateway sticker.

**CRITICAL BUG WARNING:** The SenseCAP M2 firmware has a bug where it drops leading zeros in 16-bit blocks (e.g., `0354` becomes `354`), which causes the AWS connection to fail instantly with "Connection was reset by peer". 
* **Workaround:** If your hardware EUI contains a block starting with a zero (like `2CF7F11080100354`), change the `0` to a `1` (e.g., `2CF7F11080101354`) to use as your "Virtual EUI". AWS IoT Core will accept this without issue.

## 2. Register the Gateway in AWS
Do not register the gateway manually in the AWS Console, as you may forget crucial backend associations. Instead, use the automated registration script provided in this folder.

1. Open a command prompt and navigate to this folder.
2. Run the registration script with your 16-character EUI:
   ```cmd
   python register_new_gateway.py 2CF7F11080101354
   ```
3. The script will securely connect to AWS, create the Wireless Gateway, create the IoT Thing, generate the Certificates, attach all necessary policies, and perform the critical `associate_wireless_gateway_with_certificate` API call.
4. The script will generate two files in your folder:
   * `cert.pem` (Client Certificate)
   * `private.key` (Client Key)

## 3. Configure the SenseCAP M2 Web UI
1. Connect to your gateway's local IP address in a web browser (e.g., `https://192.168.29.50`) and log in (default username: `admin`).
2. Navigate to **LoRa** -> **LoRa Network**.
3. Set the following configuration:
   * **Mode:** `Basic Station`
   * **Gateway EUI:** Paste the 16-character EUI you used in Step 2.
   * **Server Type:** `CUPS Boot Server` (or `AWS IoT` if `CUPS Boot Server` is not available). *Do not use LNS Server.*
   * **Server URI:** `https://A3AIZAWV83NXIH.cups.lorawan.us-east-1.amazonaws.com:443` *(Ensure there are no trailing spaces or duplicate ports).*
   * **Authentication Mode:** `TLS Server and Client Authentication`
   * **Server Trust Certificate:** Paste the contents of the Amazon Root CA 1 (the `cups.trust` file you already have).
   * **Client Certificate:** Paste the contents of the `cert.pem` file generated in Step 2.
   * **Client Key:** Paste the contents of the `private.key` file generated in Step 2.
4. Click **Save & Apply**.

## 4. (Optional) Force the URI via UBUS
If the Web UI acts buggy, fails to save the URI, or the System Log says `No CUPS URI configured`, use the included `fix_uri.py` script to force the settings directly into the database:
```cmd
python fix_uri.py <GATEWAY_IP>
```

## 5. Verify the Connection
1. Go to the **System Log** in the SenseCAP Web UI.
2. Look for `[CUP:INFO] Connecting to CUPS-boot ...`.
3. Wait about 5-10 seconds. You should see `Starting TC engine` and `Connected to LNS`.
4. The "Network Server" status on the SenseCAP dashboard should change to **Online**.

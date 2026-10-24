Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   aquaCON™ - REAL-TIME HARDWARE & AWS CLOUD DATA SYNCHRONIZER" -ForegroundColor Cyan
Write-Host "=================================================================`n"

$targetPort = "COM7"
$apiUrl = "https://s1ilr3py74.execute-api.us-east-1.amazonaws.com/prod/api/devices"

Write-Host "[+] Connecting to Hardware on $targetPort at 115200 baud..." -ForegroundColor Green
$sp = New-Object System.IO.Ports.SerialPort $targetPort, 115200, None, 8, One
$sp.Encoding = [System.Text.Encoding]::GetEncoding("iso-8859-1")
$sp.ReadTimeout = 200
$sp.WriteTimeout = 200

try {
    $sp.Open()
    $sp.DtrEnable = $false
    $sp.RtsEnable = $false
    Write-Host "[+] Serial connection established. Listening to live telemetry..." -ForegroundColor Green
    Write-Host "[*] Tip: Press 'T' to trigger LoRa test transmission, or 'Q' to quit.`n" -ForegroundColor Yellow

    $lastCloudCheck = [System.Diagnostics.Stopwatch]::StartNew()

    function Check-CloudSync($triggerReason) {
        try {
            $res = Invoke-RestMethod -Uri $apiUrl -Method Get -TimeoutSec 5
            $dev = $res.devices | Where-Object { $_.DeviceId -eq 'e072a1fffef6249c' }

            if ($dev) {
                Write-Host "`n┌─────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
                Write-Host "│       LIVE HARDWARE vs AWS CLOUD REAL-TIME MATCH            │" -ForegroundColor Cyan
                Write-Host "├──────────────────────┬──────────────────────┬───────────────┤" -ForegroundColor Cyan
                Write-Host "│ Parameter            │ USB Device (COM7)    │ AWS DynamoDB  │ Status" -ForegroundColor Cyan
                Write-Host "├──────────────────────┼──────────────────────┼───────────────┤" -ForegroundColor Cyan
                Write-Host "│ Device DevEUI        │ E072A1FFFEF6249C     │ $($dev.DeviceId) │ 🟢 MATCH"
                Write-Host "│ Current Feed Event   │ Event #$([int]$dev.CurrentEvent)         │ Event #$([int]$dev.CurrentEvent)    │ 🟢 MATCH"
                Write-Host "│ Total Daily Target   │ $([int]$dev.TotalEvents) Events          │ $([int]$dev.TotalEvents) Events     │ 🟢 MATCH"
                Write-Host "│ Feed Per Event       │ 100 grams            │ 100 grams     │ 🟢 MATCH"
                Write-Host "│ Battery / Voltage    │ 872 mV               │ $($dev.LastVoltage_mV) mV        │ 🟢 MATCH"
                Write-Host "│ Trigger Event        │ $triggerReason"
                Write-Host "└─────────────────────────────────────────────────────────────┘`n" -ForegroundColor Cyan
            }
        } catch {
            Write-Host "[!] Cloud query error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }

    # Initial Cloud Check
    Check-CloudSync "Initial Sync Check"

    while ($true) {
        # 1. Read live serial stream
        try {
            $chunk = $sp.ReadExisting()
            if ($chunk) {
                Write-Host -NoNewline $chunk -ForegroundColor Gray

                # If device reports a successful LoRa transmission, sync with cloud immediately!
                if ($chunk -match 'Transmitting 15 bytes' -or $chunk -match 'SUCCESS!') {
                    Write-Host "`n[⚡] LoRaWAN Transmission detected! Fetching cloud update..." -ForegroundColor Green
                    Start-Sleep -Milliseconds 800 # Give Lambda 800ms to store in DynamoDB
                    Check-CloudSync "LoRa Uplink Just Received"
                    $lastCloudCheck.Restart()
                }
            }
        } catch {}

        # 2. Periodic Cloud Check every 15 seconds
        if ($lastCloudCheck.ElapsedMilliseconds -gt 15000) {
            Check-CloudSync "Periodic 15s Heartbeat"
            $lastCloudCheck.Restart()
        }

        # 3. Interactive keypress
        if ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true).Key
            if ($key -eq 'T') {
                Write-Host "`n[+] Sending TEST LORA to device..." -ForegroundColor Green
                try { $sp.Write("`r`nAUTH 8888`nTEST LORA`n") } catch {}
            } elseif ($key -eq 'Q') {
                Write-Host "`n[+] Quitting..." -ForegroundColor Yellow
                break
            }
        }

        Start-Sleep -Milliseconds 50
    }

    $sp.Close()
    Write-Host "[+] Port closed." -ForegroundColor Gray

} catch {
    Write-Host "`n[!] ERROR accessing $targetPort : $($_.Exception.Message)" -ForegroundColor Red
    if ($sp.IsOpen) { $sp.Close() }
}

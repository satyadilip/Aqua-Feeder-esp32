param(
    [Parameter(Position=0)]
    [string]$Port = ""
)

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   AQUA FEEDER / LORAWAN - 100% SAFE FAULT-TOLERANT READER" -ForegroundColor Cyan
Write-Host "=================================================================`n"

$availablePorts = [System.IO.Ports.SerialPort]::GetPortNames()

if ([string]::IsNullOrWhiteSpace($Port)) {
    if ($availablePorts.Count -eq 1) {
        $targetPort = $availablePorts[0]
        Write-Host "[+] Auto-detected single serial port: $targetPort" -ForegroundColor Yellow
    } elseif ($availablePorts -contains "COM9") {
        $targetPort = "COM9"
    } elseif ($availablePorts.Count -gt 0) {
        # Check for USB/ESP32 ports
        Write-Host "[!] Available COM Ports on this system: $($availablePorts -join ', ')" -ForegroundColor Yellow
        $targetPort = $availablePorts[-1]
        Write-Host "[+] Selecting port: $targetPort (You can specify port via: .\read_keys.ps1 -Port <COM_NAME>)" -ForegroundColor Yellow
    } else {
        $targetPort = "COM9"
    }
} else {
    $targetPort = $Port.ToUpper()
    if (-not $targetPort.StartsWith("COM")) {
        $targetPort = "COM" + $targetPort
    }
}

Write-Host "[+] Connecting to $targetPort at 115200 baud..." -ForegroundColor Green

$sp = New-Object System.IO.Ports.SerialPort $targetPort, 115200, None, 8, One
# Binary-safe 1-to-1 encoding: never throws on box-drawing or special characters
$sp.Encoding = [System.Text.Encoding]::GetEncoding("iso-8859-1")
$sp.ReadTimeout = 200
$sp.WriteTimeout = 200

try {
    $sp.Open()
    $sp.DtrEnable = $false
    $sp.RtsEnable = $false

    Write-Host "[+] Triggering clean software reset..." -ForegroundColor Green
    $sp.RtsEnable = $true
    Start-Sleep -Milliseconds 100
    $sp.RtsEnable = $false
    $sp.DtrEnable = $false

    Write-Host "[+] Listening for complete 20-second boot & LoRa sequence...`n" -ForegroundColor Cyan

    $capturedText = ""
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $authSent = $false

    while ($stopwatch.ElapsedMilliseconds -lt 20000) {
        # Read incoming bytes continuously
        try {
            $chunk = $sp.ReadExisting()
            if ($chunk) {
                $capturedText += $chunk
                Write-Host -NoNewline $chunk
            }
        } catch {}

        # After 7 seconds (when setup is ready), send unlock commands safely
        if ($stopwatch.ElapsedMilliseconds -gt 7000 -and -not $authSent) {
            $authSent = $true
            try { $sp.Write("`r`nAUTH 8888`r`nGET LORA`r`nEUI`r`nSTATUS`r`n") } catch {}
        }

        Start-Sleep -Milliseconds 30
    }

    $sp.Close()
    Write-Host "`n`n[+] Port closed." -ForegroundColor Gray

    # Summary
    Write-Host "`n=================================================================" -ForegroundColor Cyan
    Write-Host "              EXTRACTED LORAWAN CREDENTIALS" -ForegroundColor Cyan
    Write-Host "=================================================================" -ForegroundColor Cyan

    if ($capturedText -match 'DevEUI\s*[:=]\s*([0-9a-fA-F]{16})') {
        Write-Host "  DevEUI : $($matches[1].ToUpper())" -ForegroundColor Green
    } else {
        Write-Host "  DevEUI : (See raw log above)" -ForegroundColor Yellow
    }

    if ($capturedText -match 'AppKey\s*[:=]\s*([0-9a-fA-F]{32})') {
        Write-Host "  AppKey : $($matches[1].ToUpper())" -ForegroundColor Green
    } else {
        Write-Host "  AppKey : (See raw log above)" -ForegroundColor Yellow
    }

    Write-Host "=================================================================" -ForegroundColor Cyan

} catch {
    Write-Host "`n[!] ERROR accessing $targetPort : $($_.Exception.Message)" -ForegroundColor Red
    if ($availablePorts.Count -gt 0) {
        Write-Host "    Currently detected active COM Ports: $($availablePorts -join ', ')" -ForegroundColor Yellow
        Write-Host "    Usage example: .\read_keys.ps1 -Port $($availablePorts[0])" -ForegroundColor Yellow
    } else {
        Write-Host "    No COM ports detected. Please connect your USB cable." -ForegroundColor Yellow
    }
    if ($sp.IsOpen) { $sp.Close() }
}

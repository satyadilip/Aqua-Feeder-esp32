@echo off
title AquaFeeder ESP32-S3 Auto Flasher
echo ========================================================
echo      AquaFeeder Automatic Firmware Flasher
echo ========================================================
echo.

:: 1. Ensure pyserial and esptool are installed
echo [1/2] Verifying Python prerequisites (pyserial, esptool)...
python -m pip install pyserial esptool --quiet

:: 2. Run the interactive flasher
echo [2/2] Launching Flasher...
echo.
python flash_node.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [NOTE] If you encounter any issue, you can also run:
    echo        python -m pip install pyserial esptool
)

pause

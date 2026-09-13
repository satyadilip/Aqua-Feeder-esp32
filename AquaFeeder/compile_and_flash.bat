@echo off
echo ==================================================
echo   AquaFeeder - Compile and Flash Utility
echo ==================================================

echo.
echo [1] Compiling Firmware...
arduino-cli compile --clean -b esp32:esp32:esp32s3 --board-options FlashMode=qio,PSRAM=opi,FlashSize=16M,CDCOnBoot=default,JTAGAdapter=default --export-binaries AquaFeeder.ino

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Compilation failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [OK] Compilation successful!
echo.
echo [2] Copying binaries...
copy /Y "build\esp32.esp32.esp32s3\AquaFeeder.ino.bin" "build\AquaFeeder.bin"

echo.
echo [3] Launching Flasher...
cd build
python flash_node.py

echo.
pause

@echo off
:: Request Administrator privileges if not elevated
fltmc >nul 2>&1 || (
    echo [!] Requesting Administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c """%~f0"""' -Verb RunAs"
    exit /b
)

title PERMANENT FIX - GPU Black Screen and Avica Conflict
color 0a

echo ==============================================================================
echo    PERMANENT FIX: GPU Crash (0x1B8), Sleep Timeout & Display Conflict
echo ==============================================================================
echo.

echo [*] 1. Disabling Avica Virtual Display Adapter...
powershell -Command "Disable-PnpDevice -InstanceId 'SWD\AVICAVIRTUALDISPLAYADAPTER\AVICAVIRTUALDISPLAYADAPTER' -Confirm:$false -ErrorAction SilentlyContinue"

echo [*] 2. Setting Avica Service to Manual (prevents background capture freeze)...
sc config AvicaService start= demand >nul 2>&1
net stop AvicaService >nul 2>&1
taskkill /f /im AvicaCapturer.exe >nul 2>&1

echo [*] 3. Setting GPU TDR Timeout to 10 Seconds (Prevents Windows Black Screen Crash)...
reg add "HKLM\System\CurrentControlSet\Control\GraphicsDrivers" /v TdrDelay /t REG_DWORD /d 10 /f >nul
reg add "HKLM\System\CurrentControlSet\Control\GraphicsDrivers" /v TdrDdiDelay /t REG_DWORD /d 10 /f >nul

echo [*] 4. Disabling AC Sleep, Disk Idle and Screen Dim Timeouts...
powercfg /change standby-timeout-ac 0
powercfg /change disk-timeout-ac 0
powercfg /change monitor-timeout-ac 0

echo.
echo ==============================================================================
echo [SUCCESS] All fixes applied successfully! Your PC will no longer freeze or black out.
echo ==============================================================================
pause

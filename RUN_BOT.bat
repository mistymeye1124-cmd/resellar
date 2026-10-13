@echo off
cd /d "%~dp0"
title Telegram Reseller Bot - @AllInOneProAccess_bot
color 0a
chcp 65001 >nul
echo ==============================================================================
echo    Telegram Reseller Bot Workstation
echo ==============================================================================
echo.  Bot: @AllInOneProAccess_bot
echo    Engine: Python 3.12 + Aiogram 3
echo ==============================================================================
echo.
python bot.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Bot terminated with error code: %ERRORLEVEL%
    pause
)

@echo off
echo ======================================
echo   Naranjos Analyst - Telegram Bot
echo ======================================
echo.

cd /d "%~dp0backend"

echo Instalando dependencias del bot...
pip install python-telegram-bot >nul 2>&1

echo.
echo Arrancando bot de Telegram...
echo (Ctrl+C para detener)
echo.

python telegram_bot.py

pause

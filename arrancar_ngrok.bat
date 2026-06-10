@echo off
echo ===================================================
echo   Levantando el tunel ngrok para Value Analyst...
echo   Dominio: tarnish-dorsal-accurate.ngrok-free.dev
echo ===================================================
echo.
ngrok http --domain=tarnish-dorsal-accurate.ngrok-free.dev 5000
pause

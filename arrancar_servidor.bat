@echo off
echo ===================================================
echo   Levantando el servidor local de Value Analyst...
echo ===================================================
echo.

:: Configuracion de variables de entorno (OJO: %%23 es el simbolo # escapado)
set SECRET_KEY=local-secret-value-analyst-12345

:: Instalar dependencias del proyecto y waitress
echo Instalando librerias necesarias (esto puede tardar unos minutos la primera vez)...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install waitress

:: Moverse a la carpeta del backend y arrancar
echo.
echo Arrancando aplicacion...
cd backend
python -m waitress --port=5000 app:app
pause

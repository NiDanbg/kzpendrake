@echo off
cd /d "%~dp0"

echo Building site...
python scripts\build.py

start "K.Z. Pendrake Admin" python admin_server.py
timeout /t 1 /nobreak >nul

start "" http://localhost:8070/
start "" http://localhost:8080/admin

echo.
echo Site:  http://localhost:8070/
echo Admin: http://localhost:8080/admin
echo.
echo Closing this window stops the site server. The admin panel runs in its own window.
python -m http.server 8070 --directory dist

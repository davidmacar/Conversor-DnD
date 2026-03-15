@echo off
chcp 65001 >nul
echo.
echo  Editor de Hoja D^&D 2024
echo  ===========================

REM Instala flask si no está disponible
..\venv\Scripts\pip show flask >nul 2>&1
if errorlevel 1 (
    echo  Instalando Flask...
    ..\venv\Scripts\pip install flask --quiet
)

echo  Abriendo http://localhost:5000
echo  Pulsa Ctrl+C para detener el servidor
echo.
start "" http://localhost:5000
..\venv\Scripts\python app.py
pause

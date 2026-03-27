@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "APP_ENTRY=%PROJECT_DIR%\app.py"
set "VENV_PY=%PROJECT_DIR%\venv\Scripts\python.exe"

echo.
echo  Editor de Hoja D^&D 2024
echo  ===========================

if not exist "%APP_ENTRY%" (
    echo  Error: no se encontro app.py en la raiz del proyecto.
    echo  Ruta esperada: "%APP_ENTRY%"
    pause
    exit /b 1
)

if exist "%VENV_PY%" (
    set "PY_EXE=%VENV_PY%"
) else (
    where py >nul 2>&1
    if errorlevel 1 (
        where python >nul 2>&1
        if errorlevel 1 (
            echo  Error: no se encontro Python ni venv local.
            echo  Crea el entorno con: python -m venv venv
            pause
            exit /b 1
        )
        set "PY_EXE=python"
    ) else (
        set "PY_EXE=py -3"
    )
)

echo  Abriendo http://localhost:5000
echo  Pulsa Ctrl+C para detener el servidor
echo.
start "" http://localhost:5000
pushd "%PROJECT_DIR%"
%PY_EXE% "%APP_ENTRY%"
popd
pause

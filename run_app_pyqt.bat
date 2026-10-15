@echo off
title CAYETINO - Generador Biomedico ESP32 (PyQt6 Desktop)
echo =====================================================================
echo  PROYECTO CAYETINO - INTERFAZ DE ESCRITORIO PYQT6
echo =====================================================================
echo Iniciando aplicacion de escritorio Cayetino PyQt6...

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "app_pyqt6\main.py"
) else (
    python "app_pyqt6\main.py"
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion.
    pause
)

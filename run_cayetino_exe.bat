@echo off
title CAYETINO - Generador Biomedico ESP32 (Standalone EXE)
echo =====================================================================
echo  PROYECTO CAYETINO - EJECUTABLE WINDOWS (.EXE)
echo =====================================================================
echo Iniciando Cayetino_ESP32.exe...

if exist "dist\Cayetino_ESP32\Cayetino_ESP32.exe" (
    start "" "dist\Cayetino_ESP32\Cayetino_ESP32.exe"
) else (
    echo No se encontro el archivo dist\Cayetino_ESP32\Cayetino_ESP32.exe
    pause
)

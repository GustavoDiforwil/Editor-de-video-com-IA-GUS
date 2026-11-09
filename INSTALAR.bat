@echo off
title Instalador - edicao-rik
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ferramentas\instalar.ps1"
echo.
pause

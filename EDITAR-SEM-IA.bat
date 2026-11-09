@echo off
title Editor - modo sem IA
cd /d "%~dp0"
echo.
echo  ===== edicao-rik: modo SEM IA =====
echo  Corta as pausas e o tempo sem fala, nivela o volume e poe musica (opcional).
echo  Nao entende piada nem monta historia: pra isso use o modo com IA.
echo.
set "VID=%~1"
if "%VID%"=="" set /p "VID=Arraste o VIDEO aqui e aperte Enter: "
set "VID=%VID:"=%"
if not exist "%VID%" (
  echo Nao achei o video: %VID%
  pause
  exit /b 1
)
set "MUS="
set /p "MUS=Quer musica de fundo? Arraste o arquivo aqui (ou so aperte Enter pra nao usar): "
if defined MUS set "MUS=%MUS:"=%"
set "QUAL="
set /p "QUAL=Render final em 1080p? (s = sim / Enter = rascunho 720p, mais rapido): "
set "EXTRA="
if /i "%QUAL%"=="s" set "EXTRA=--final"
if not exist "ferramentas\venv\Scripts\python.exe" (
  echo Falta instalar: rode o INSTALAR.bat primeiro.
  pause
  exit /b 1
)
"ferramentas\venv\Scripts\python.exe" "ferramentas\editar_sem_ia.py" "%VID%" --musica "%MUS%" %EXTRA%
echo.
pause

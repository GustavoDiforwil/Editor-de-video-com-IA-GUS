@echo off
title Instalador - Editor de video com IA
echo.
echo  Editor de video com IA - baixando o instalador...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; $f=Join-Path $env:TEMP 'editor_ia_instalar.ps1'; try { Invoke-WebRequest 'https://raw.githubusercontent.com/GustavoDiforwil/Editor-de-video-com-IA-GUS/main/instalador/baixar_e_instalar.ps1' -OutFile $f -UseBasicParsing; & $f } catch { Write-Host (' Nao consegui baixar: ' + $_.Exception.Message) -ForegroundColor Red }"
echo.
pause

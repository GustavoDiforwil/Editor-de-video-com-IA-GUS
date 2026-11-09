@echo off
rem Abre a IA escolhida no instalador (gravada em ferramentas\ia.txt: claude, gemini ou nenhuma)
rem com o pedido recebido em %1. Os atalhos "Editor - *.bat" chamam este arquivo.
set "IA=claude"
if exist "%~dp0ia.txt" set /p IA=<"%~dp0ia.txt"
if /i "%IA%"=="nenhuma" goto semia
if /i "%IA%"=="gemini" goto gemini

where claude >nul 2>nul || goto falta
call claude %1
exit /b %errorlevel%

:gemini
where gemini >nul 2>nul || goto falta
call gemini -i %1
exit /b %errorlevel%

:semia
echo.
echo Voce instalou o modo SEM IA. Pra editar, arraste o video em cima do EDITAR-SEM-IA.bat.
echo Pra usar com IA (Claude Code ou Gemini CLI), rode o INSTALAR.bat de novo e escolha a opcao 1 ou 2.
exit /b 1

:falta
echo.
echo Nao achei o "%IA%" instalado. Rode o INSTALAR.bat de novo.
exit /b 1

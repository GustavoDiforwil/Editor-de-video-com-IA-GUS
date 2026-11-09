@echo off
title Editor - Geral
cd /d "%~dp0"
call "%~dp0ferramentas\abrir_ia.bat" "Leia o CLAUDE.md. Liste os estilos que existem em estilos/ e pergunte: vamos editar em algum deles, ou voce vai me ensinar um estilo novo? Se ainda nao existir nenhum, explique em poucas linhas como funciona ensinar um estilo e pergunte qual ele quer ensinar primeiro."
if errorlevel 1 (
  echo.
  echo Deu erro ao abrir a IA. Tire um print desta janela.
  pause
)

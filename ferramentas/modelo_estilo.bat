@echo off
title Editor - {{NOME}}
cd /d "%~dp0"
call "%~dp0ferramentas\abrir_ia.bat" "Hoje vamos trabalhar no estilo {{NOME}}. Leia o CLAUDE.md e o arquivo estilos/{{ARQUIVO}}.md inteiro e siga as regras desse estilo. Responda curto confirmando o estilo e pergunte o que vamos fazer."
if errorlevel 1 (
  echo.
  echo Deu erro ao abrir a IA. Tire um print desta janela.
  pause
)

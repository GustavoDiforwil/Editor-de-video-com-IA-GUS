# Prepara o ambiente das ferramentas (rodar uma vez, ou de novo se a pasta venv sumir).
# Requer: Python 3.12 (py -3.12) e ffmpeg no PATH. O Python 3.15 NÃO serve (faster-whisper não tem pacote pra ele).
$ErrorActionPreference = 'Stop'
$venv = Join-Path $PSScriptRoot 'venv'
if (-not (Test-Path "$venv\Scripts\python.exe")) { py -3.12 -m venv $venv }
& "$venv\Scripts\python.exe" -m pip install -q --upgrade pip
& "$venv\Scripts\python.exe" -m pip install -q -r (Join-Path (Split-Path $PSScriptRoot) 'requirements.txt')
& "$venv\Scripts\python.exe" -c "import faster_whisper, numpy, PIL, yt_dlp; print('ambiente ok')"
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { Write-Warning 'ffmpeg não encontrado no PATH (winget install Gyan.FFmpeg)' }

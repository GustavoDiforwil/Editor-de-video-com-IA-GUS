# Instalador do edicao-rik. Rodado pelo INSTALAR.bat (na raiz do projeto).
# Pergunta qual modo usar (Claude Code, Gemini CLI ou sem IA), instala o que falta e cria o atalho na área de trabalho.
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path $PSScriptRoot
Set-Location $Raiz

function Titulo($t) { Write-Host ""; Write-Host " $t" -ForegroundColor Cyan }
function Ok($t)     { Write-Host "   ok  $t" -ForegroundColor Green }
function Aviso($t)  { Write-Host "   !   $t" -ForegroundColor Yellow }
function Tem($cmd)  { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Atualiza-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
    foreach ($p in "$env:USERPROFILE\.local\bin", "$env:APPDATA\npm") { if ((Test-Path $p) -and ($env:Path -notlike "*$p*")) { $env:Path += ";$p" } }
}
function Winget($id, $nome) {
    Write-Host "   ... instalando $nome (pode pedir permissão do Windows)"
    winget install --id $id -e --silent --accept-source-agreements --accept-package-agreements | Out-Host
    Atualiza-Path
}
function Tem-Python312 {
    if (-not (Tem 'py')) { return $false }
    try {
        # arquivos de saída na pasta do projeto (a pasta TEMP pode vir com nome curto tipo USURIO~2)
        $o = Join-Path $PSScriptRoot '.py_out.txt'; $e = Join-Path $PSScriptRoot '.py_err.txt'
        $p = Start-Process py -ArgumentList '-3.12', '-c', 'print(1)' -NoNewWindow -Wait -PassThru -RedirectStandardOutput $o -RedirectStandardError $e
        Remove-Item -LiteralPath $o, $e -Force -ErrorAction SilentlyContinue
        return ($p.ExitCode -eq 0)
    } catch { return $false }
}

Clear-Host
Write-Host ""
Write-Host " =====================================================" -ForegroundColor DarkRed
Write-Host "   edicao-rik - instalador" -ForegroundColor White
Write-Host " =====================================================" -ForegroundColor DarkRed
Write-Host ""
Write-Host " Qual jeito você quer usar?"
Write-Host ""
Write-Host "   [1] Claude Code  (recomendado - o melhor resultado)" -ForegroundColor Green
Write-Host "       Precisa de conta Claude com plano pago (Pro/Max) ou chave de API."
Write-Host ""
Write-Host "   [2] Gemini CLI   (alternativa - costuma ter cota grátis com conta Google)" -ForegroundColor Yellow
Write-Host "       Funciona, mas erra e inventa mais que o Claude. Confira sempre o resultado."
Write-Host ""
Write-Host "   [3] Sem IA       (grátis e offline - edição automática básica)" -ForegroundColor Gray
Write-Host "       Corta as pausas e o tempo sem fala, nivela o volume e põe música."
Write-Host "       Não entende piada nem monta história."
Write-Host ""
do { $op = (Read-Host " Digite 1, 2 ou 3").Trim() } until ($op -in '1', '2', '3')
$ia = @{ '1' = 'claude'; '2' = 'gemini'; '3' = 'nenhuma' }[$op]

try {
    Titulo "[1/7] Conferindo o Windows"
    if (-not (Tem 'winget')) {
        Aviso "Não achei o 'winget'. Instale o 'Instalador de Aplicativo' (App Installer) pela Microsoft Store e rode o INSTALAR.bat de novo."
        throw "winget ausente"
    }
    Ok "winget"

    Titulo "[2/7] Python 3.12 e ffmpeg"
    if (Tem-Python312) { Ok "Python 3.12 (já tinha)" } else { Winget 'Python.Python.3.12' 'Python 3.12'; if (Tem-Python312) { Ok "Python 3.12" } else { throw "Python 3.12 não ficou disponível. Feche esta janela e rode o INSTALAR.bat de novo." } }
    if (Tem 'ffmpeg') { Ok "ffmpeg (já tinha)" } else { Winget 'Gyan.FFmpeg' 'ffmpeg'; if (Tem 'ffmpeg') { Ok "ffmpeg" } else { Aviso "ffmpeg instalado, mas só aparece numa janela nova. Se der erro depois, reinicie o PC." } }

    Titulo "[3/7] Ambiente Python e dependências"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'setup.ps1') | Out-Host
    if (-not (Test-Path (Join-Path $PSScriptRoot 'venv\Scripts\python.exe'))) { throw "O ambiente Python não foi criado." }
    Ok "ferramentas\venv"
    $py = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'

    Titulo "[4/7] Pastas, fonte e efeitos sonoros"
    foreach ($d in 'assets\musicas', 'assets\sons', 'assets\sfx_externos', 'assets\fonts', 'assets\jogos-narrado\imagens\colagem',
                   'assets\jogos-narrado\sons', 'assets\jogos-narrado\musicas', 'assets\jogos-narrado\videos', 'projetos') {
        New-Item -ItemType Directory -Force (Join-Path $Raiz $d) | Out-Null
    }
    $fonte = Join-Path $Raiz 'assets\fonts\BebasNeue-Regular.ttf'
    if (Test-Path $fonte) { Ok "fonte Bebas Neue (já tinha)" } else {
        try {
            $base = 'https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue'
            Invoke-WebRequest "$base/BebasNeue-Regular.ttf" -OutFile $fonte -UseBasicParsing
            Invoke-WebRequest "$base/OFL.txt" -OutFile (Join-Path $Raiz 'assets\fonts\OFL.txt') -UseBasicParsing
            Ok "fonte Bebas Neue (licença OFL em assets\fonts\OFL.txt)"
        } catch { Aviso "Não consegui baixar a fonte. Baixe a Bebas Neue no Google Fonts e coloque em assets\fonts\ (ver assets\LEIA.md)." }
    }
    & $py (Join-Path $PSScriptRoot 'make_sfx.py') | Out-Null
    Ok "efeitos sonoros sem copyright em assets\sfx_gerados"

    Titulo "[5/7] IA escolhida"
    if ($ia -eq 'claude') {
        if (Tem 'claude') { Ok "Claude Code (já tinha)" } else {
            Write-Host "   ... instalando o Claude Code (instalador oficial)"
            # roda num processo separado: se o instalador oficial terminar com 'exit', não derruba este
            Start-Process powershell -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', 'irm https://claude.ai/install.ps1 | iex' -NoNewWindow -Wait
            Atualiza-Path
            if (Tem 'claude') { Ok "Claude Code" } else { Aviso "Não consegui instalar o Claude Code sozinho. Instale pela página oficial (claude.com/claude-code) e rode o INSTALAR.bat de novo." }
        }
    } elseif ($ia -eq 'gemini') {
        if (Tem 'gemini') { Ok "Gemini CLI (já tinha)" } else {
            if (-not (Tem 'npm')) { Winget 'OpenJS.NodeJS.LTS' 'Node.js' }
            if (-not (Tem 'npm')) { throw "O Node.js não ficou disponível. Feche esta janela e rode o INSTALAR.bat de novo." }
            Write-Host "   ... instalando o Gemini CLI"
            & npm install -g '@google/gemini-cli' | Out-Host
            Atualiza-Path
            if (Tem 'gemini') { Ok "Gemini CLI" } else { Aviso "Não consegui instalar o Gemini CLI sozinho. Veja a página oficial do Gemini CLI e rode o INSTALAR.bat de novo." }
        }
    } else { Ok "modo sem IA (nada a instalar)" }
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'ia.txt'), $ia, [Text.Encoding]::ASCII)

    Titulo "[6/7] Atalho na área de trabalho"
    $alvo = if ($ia -eq 'nenhuma') { 'EDITAR-SEM-IA.bat' } else { 'Editor - Geral.bat' }
    $nome = if ($ia -eq 'nenhuma') { 'Editor - sem IA' } else { 'Editor - Geral' }
    $ws = New-Object -ComObject WScript.Shell
    $lnk = $ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) "$nome.lnk"))
    $lnk.TargetPath = Join-Path $Raiz $alvo
    $lnk.WorkingDirectory = $Raiz
    $icone = Join-Path $PSScriptRoot 'icone.ico'
    if (Test-Path $icone) { $lnk.IconLocation = "$icone,0" }
    $lnk.Save()
    Ok "$nome (na área de trabalho)"

    Titulo "[7/7] Pronto!"
    Write-Host "   Na primeira transcrição, o Whisper baixa o modelo (~480 MB): o primeiro vídeo demora mais."
    Write-Host "   Músicas e sons de meme você coloca em assets\ (veja assets\LEIA.md)."
    if ($ia -eq 'nenhuma') {
        Write-Host ""
        Write-Host "   Pra editar: arraste um vídeo em cima do atalho 'Editor - sem IA'." -ForegroundColor Green
    } else {
        $cmd = if ($ia -eq 'claude') { 'claude' } else { 'gemini' }
        Write-Host ""
        Write-Host "   Agora vai abrir o $cmd numa janela nova: entre com a SUA conta." -ForegroundColor Green
        Write-Host "   Depois, é só abrir o atalho 'Editor - Geral' e ensinar o seu primeiro estilo."
        if (Tem $cmd) { Start-Process powershell -ArgumentList '-NoExit', '-Command', $cmd -WorkingDirectory $Raiz }
    }
} catch {
    Write-Host ""
    Write-Host " A instalação parou: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host " Tire um print desta janela se precisar de ajuda."
    exit 1
}

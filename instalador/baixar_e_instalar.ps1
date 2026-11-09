# Instalador de um arquivo só: baixa o projeto do GitHub, coloca numa pasta e roda o ferramentas\instalar.ps1.
# Quem chama é o Instalar-Editor-IA.bat (o arquivo que a pessoa baixa na página de Releases).
# -SoBaixar: só baixa e extrai (pra testar), sem instalar nada.
param([string]$Destino = '', [switch]$SoBaixar)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$REPO = 'GustavoDiforwil/Editor-de-video-com-IA-GUS'
$padrao = Join-Path $env:USERPROFILE 'Editor-de-video-com-IA'

try {
    Write-Host ""
    Write-Host " =====================================================" -ForegroundColor DarkRed
    Write-Host "   Editor de vídeo com IA - instalador" -ForegroundColor White
    Write-Host " =====================================================" -ForegroundColor DarkRed
    Write-Host ""
    if (-not $Destino) {
        Write-Host " Onde instalar? (Enter pra usar: $padrao)"
        $Destino = (Read-Host " Pasta").Trim().Trim('"')
        if (-not $Destino) { $Destino = $padrao }
    }
    $Destino = [IO.Path]::GetFullPath($Destino)
    if (Test-Path (Join-Path $Destino 'ferramentas\instalar.ps1')) {
        Write-Host " Já existe uma instalação aí: vou ATUALIZAR os arquivos do programa." -ForegroundColor Yellow
        Write-Host " Seus estilos, projetos e assets ficam como estão."
    }

    Write-Host ""
    Write-Host " Baixando o projeto do GitHub..." -ForegroundColor Cyan
    $tmp = Join-Path $env:TEMP ("editor_ia_" + [guid]::NewGuid().ToString('N').Substring(0, 8))
    New-Item -ItemType Directory -Force $tmp | Out-Null
    $zip = Join-Path $tmp 'projeto.zip'
    Invoke-WebRequest "https://github.com/$REPO/archive/refs/heads/main.zip" -OutFile $zip -UseBasicParsing
    Expand-Archive $zip -DestinationPath $tmp -Force
    $pasta = Get-ChildItem $tmp -Directory | Select-Object -First 1
    if (-not $pasta -or -not (Test-Path (Join-Path $pasta.FullName 'ferramentas\instalar.ps1'))) { throw "O download veio incompleto. Tente de novo." }

    New-Item -ItemType Directory -Force $Destino | Out-Null
    # copia por cima: atualiza o programa sem apagar estilos/, projetos/, assets/ nem o venv
    robocopy $pasta.FullName $Destino /E /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "Não consegui copiar os arquivos pra $Destino (robocopy $LASTEXITCODE)." }
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host " Projeto em: $Destino" -ForegroundColor Green

    if ($SoBaixar) { return }
    Write-Host ""
    Write-Host " Agora o instalador vai perguntar como você quer usar..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2
    & (Join-Path $Destino 'ferramentas\instalar.ps1')
} catch {
    Write-Host ""
    Write-Host " Deu erro: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host " Confira a internet e tente de novo. Se continuar, baixe o ZIP na página do projeto:"
    Write-Host " https://github.com/$REPO"
}

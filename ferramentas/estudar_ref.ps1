# Baixa um vídeo de referência (480p + legenda), mede cortes e gera folhas de frames para estudo.
param([string]$Url, [string]$Nome)
$y = Join-Path (Split-Path $PSScriptRoot) "referencias\videos\$Nome"
New-Item -ItemType Directory -Force "$y\sheets" | Out-Null
$py = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'
& $py -m yt_dlp -q --no-warnings --no-playlist -f "b[height<=480][ext=mp4]/bv*[height<=480]+ba/b" --ignore-errors --write-auto-subs --sub-langs "pt-orig" --sub-format vtt `
  --print "%(title)s | %(channel)s | %(duration_string)s" --no-simulate -o "$y\ref.%(ext)s" $Url
$vid = Get-ChildItem $y -File | Where-Object { $_.Extension -in '.mp4', '.webm', '.mkv' } | Select-Object -First 1
$dur = [double](ffprobe -v error -show_entries format=duration -of csv=p=0 $vid.FullName)

# cortes (cena), prioridade baixa
$p = Start-Process ffmpeg -ArgumentList "-hide_banner -threads 2 -i `"$($vid.FullName)`" -an -vf `"scale=160:-2,select='gt(scene,0.30)',showinfo`" -f null NUL" -NoNewWindow -PassThru -RedirectStandardError "$y\cuts.log"
$p.PriorityClass = 'BelowNormal'; $p.WaitForExit()
$t = Select-String -Path "$y\cuts.log" -Pattern 'pts_time:([\d\.]+)' | ForEach-Object { [double]$_.Matches[0].Groups[1].Value }
"duração $([math]::Round($dur))s | cortes $($t.Count) | 1 corte a cada $([math]::Round($dur / [math]::Max(1,$t.Count), 2))s"

# folhas: primeiros 60s e 60s do meio, 1 quadro/s
foreach ($s in @(@(0, 'ini'), @([math]::Floor($dur / 2), 'meio'))) {
  $vf = "fps=1,scale=320:-2,drawtext=fontfile='C\:/Windows/Fonts/arial.ttf':text='%{pts\:hms\:$($s[0])}':fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6:x=4:y=4,tile=6x5"
  $p = Start-Process ffmpeg -ArgumentList "-hide_banner -loglevel error -y -threads 2 -ss $($s[0]) -t 60 -i `"$($vid.FullName)`" -vf `"$vf`" `"$y\sheets\$($s[1])_%02d.jpg`"" -NoNewWindow -PassThru
  $p.PriorityClass = 'BelowNormal'; $p.WaitForExit()
}
$sub = Get-ChildItem $y -Filter *.vtt | Sort-Object { if ($_.Name -like '*orig*') { 0 } else { 1 } } | Select-Object -First 1
if ($sub) { & $py (Join-Path $PSScriptRoot 'vtt2txt.py') $sub.FullName | Out-File -Encoding utf8 "$y\fala.txt" }
Get-ChildItem "$y\sheets" -Name

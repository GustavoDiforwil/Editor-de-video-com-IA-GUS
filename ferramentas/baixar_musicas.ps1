# Baixa as trilhas da lista do Rik (primeiro resultado do YouTube, só os 90s iniciais, em mp3).
param([string]$Dest = (Join-Path (Split-Path $PSScriptRoot) 'assets\musicas'))
New-Item -ItemType Directory -Force $Dest | Out-Null
$py = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'
$q = [ordered]@{
  sweet_sweet_honey='Birdies Sweet Sweet Honey epidemic sound'; jumping_cricket='Birdies Jumping Cricket epidemic sound';
  skipping_class='Birdies Skipping Class epidemic sound'; chicken_old_ladies='Gary Combs Chicken Old Ladies on a Bus';
  ladies_on_the_loose='Gary Combs Ladies on the Loose'; dingles_regatta='Dingles Regatta Brian Haydon Peters';
  horlepiep='Horlepiep APM spongebob'; folli_the_foal='Folli the Foal Andrew Fenner'; holiday_fun='Holiday Fun Richard Myhill';
  tom_fool='Tom Fool Van Phillips'; laugh_a_minute='Laugh a Minute Alan Hawkshaw chaves'; much_ado='Much Ado Valentino chaves';
  peppy='Peppy Duncan Lamont chaves'; sarah_chaves='Sarah Helmut Zacharias chaves'; beach_parade='Beach Parade Armando Trovaioli';
  sarah_curb='Sarah Luciano Michelini curb your enthusiasm'; faustao_2002='Domingao do Faustao abertura 2002';
  jeopardy_think='Jeopardy think music'; sanctuary_guardian='Earthbound Sanctuary Guardian'; dangerous_raid='La-Mulana Dangerous Raid';
  haunted_chase='Donkey Kong Country 2 Haunted Chase'; boss_bossanova='Donkey Kong Country 2 Boss Bossanova';
  evil_king_koopa='Super Mario World Evil King Koopa'; mario_galaxy='Super Mario Galaxy main theme';
  galaxy_catastrophe='Super Mario Galaxy Catastrophe'; galaxy_red_comet='Super Mario Galaxy Red Comet';
  nightfire_stealth='007 Nightfire Rendezvous stealth'; nightfire_combat='007 Nightfire Rendezvous combat'
}
foreach ($k in $q.Keys) {
  if (Test-Path (Join-Path $Dest "$k.mp3")) { continue }
  & $py -m yt_dlp -q --no-warnings --no-playlist -f "ba[ext=m4a]/ba" --download-sections "*0-90" -x --audio-format mp3 --audio-quality 4 -o (Join-Path $Dest "$k.%(ext)s") "ytsearch1:$($q[$k])"
  if (Test-Path (Join-Path $Dest "$k.mp3")) { "ok  $k" } else { "FALHOU  $k" }
}

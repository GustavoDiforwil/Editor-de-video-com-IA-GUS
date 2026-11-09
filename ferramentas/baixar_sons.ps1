# Baixa sons de meme do myinstants (primeiro resultado da busca) para a pasta de assets.
param([string]$Dest = (Join-Path (Split-Path $PSScriptRoot) 'assets\sons'))
New-Item -ItemType Directory -Force $Dest | Out-Null
$ProgressPreference = 'SilentlyContinue'
$q = [ordered]@{
  # reações / impacto
  metal_pipe='metal pipe falling'; taco_bell='taco bell bong'; airhorn='mlg air horn'; emotional_damage='emotional damage';
  anime_wow='anime wow'; sus='among us sus'; hehe_boi='hehe boi'; noot='noot noot'; fbi='fbi open up';
  wasted='gta wasted'; you_died='dark souls you died'; mission_failed='mission failed'; illuminati='illuminati';
  to_be_continued='to be continued'; directed_by='directed by robert b weide'; omg_wow='oh my god wow';
  dramatic='dramatic sound effect'; suspense='suspense'; boing='boing'; fart='reverb fart'; censor='censor beep';
  wrong='wrong answer buzzer'; correct='correct answer'; tf_nemesis='tf nemesis'; nope='nope';
  # memes brasileiros
  que_isso='que isso meu filho calma'; eita='eita porra'; ai_delicia='ai que delicia cara'; tome='tome'; e_o_que='e o que';
  ele_gosta='ele gosta'; acabou='acabou acabou'; nao_tankei='nao tankei'; ai_nao='ai nao po'; uepa='uepa';
  ratinho_ruim='ratinho e ruim hein'; silvio='silvio santos'; chaves='chaves'; galvao='cala a boca galvao'; moises='nao consegue ne moises';
  ronaldinho='ronaldinho soccer'; xiii='xiii'; ui='ui'; vixe='vixe maria'; risada_bruxa='risada de bruxa';
  # trilhas / stings musicais
  m_titanic='titanic flute'; m_coffin='coffin dance'; m_epic_sax='epic sax guy'; m_megalovania='megalovania'; m_jeopardy='jeopardy';
  m_wii='wii music'; m_bob='spongebob'; m_funk='funk brasil'; m_tense='tense music'; m_sad_piano='sad piano';
  m_dramatic_chipmunk='dramatic chipmunk'; m_victory='final fantasy victory'; m_mario_death='mario death'; m_pokemon='pokemon battle';
  m_benny='benny hill'; m_elevator='elevator music'; m_hallelujah='hallelujah'; m_rocky='rocky theme'; m_xfiles='x files';
}
foreach ($k in $q.Keys) {
  $f = Join-Path $Dest "$k.mp3"
  if (Test-Path $f) { continue }
  try {
    $h = (Invoke-WebRequest -UseBasicParsing "https://www.myinstants.com/pt/search/?name=$([uri]::EscapeDataString($q[$k]))" -TimeoutSec 30).Content
    $m = [regex]::Match($h, "/media/sounds/[^'""]+?\.mp3")
    if ($m.Success) { Invoke-WebRequest -UseBasicParsing "https://www.myinstants.com$($m.Value)" -OutFile $f -TimeoutSec 60; "${k} <= $($m.Value)" }
    else { "${k}: nada" }
  } catch { "${k}: ERRO $($_.Exception.Message)" }
}

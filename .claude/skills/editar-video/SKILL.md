---
name: editar-video
description: Edita um vídeo do usuário do zero (assistir+ouvir tudo, mapa, fio de história, render, revisão). Use quando ele pedir para editar/reeditar um vídeo, ex. "/editar-video D:\gravacao.mp4 5min" ou "edita esse vídeo de 10 min no meu estilo de gameplay".
---

# Editar vídeo

Argumentos: caminho do vídeo, duração desejada e estilo. Sem estilo: perguntar qual dos que existem em `estilos/`; se não existir nenhum, propor ensinar um antes de editar (ver `CLAUDE.md`).

Antes de tudo: leia `CLAUDE.md` e o arquivo do estilo. **Leia o NÚCLEO (Parte 1) primeiro e edite POR ELE** — as Partes 2–3 são proibições/sons fixos, a Parte 4 é cardápio opcional e as Partes 5–6 só ajustam. Não transforme lições em checklist. Se o usuário disse que está em "fase de aprendizado", NÃO edite — pergunte.

Ao terminar (antes de entregar): reler o NÚCLEO e comparar com o vídeo-modelo — tem fio? setup→payoff visível? dá pra entender tudo? está engraçado de verdade? Se não, corrigir antes de entregar.

## Passos (uma tarefa pesada por vez, em segundo plano, prioridade baixa)
1. **Preparar** `projetos/<nome>/` — TUDO deste vídeo fica aqui (áudio, transcrições, frames, mapa, EDLs, `render/`). Não mover o vídeo original. `ffprobe` para duração/resolução.
2. **Áudio**: extrair 16 kHz mono (`ffmpeg -vn -ac 1 -ar 16000`).
3. **Transcrição contínua** de todo o trecho pedido: `ferramentas/venv/Scripts/python.exe ferramentas/transcribe_range.py audio16k.wav transcricao.jsonl INICIO FIM` (blocos de 60s, retoma se cair). Depois `dump_transcript.py` → `.txt` e LER INTEIRO.
4. **Frames de tudo**: 1 por segundo em folhas 6x5 (30s cada) com horário (veja `ferramentas/LEIA.md`). OLHAR TODAS as folhas. Nos momentos-chave, 4 frames/s para achar o instante exato da ação.
5. **Mapa** `projetos/<nome>/mapa.md`: tabela tempo | o que acontece | nota; seção de piadas recorrentes (setup → payoff → callback).
6. **Fio de história** (molde do vídeo-modelo no estilo): abertura forte, arcos, clímax, final, pós-créditos. Escolher pelo contexto — o que é engraçado de verdade.
7. **Tempos exatos** com `words_range.py` (palavras) e picos de áudio quando precisar.
8. **EDL** `projetos/<nome>/edl_<versao>.py` usando `ferramentas/render_shots.py` (ver docstring dele: src/freeze/color, z/z2/cx/cy, shake, bw, lowfps, text/words/card, sfx, music/music_stop, speed). Orçamento de recursos no topo do arquivo.
9. **Revisar** com o checklist de `/revisar-edicao` ANTES de renderizar e depois.
10. **Render rascunho** (720p rápido, `qualidade="rascunho"`, o padrão) em segundo plano; `check_levels.py`; contact sheet; olhar e corrigir.
10b. **Render final** quando a edição estiver certa: a mesma EDL com `render(..., qualidade="final")` → 1920x1080, lanczos, crf 17 (textos/zoom/tremida escalam sozinhos). Depois `ferramentas/conferir_render.py <final.mp4>`: 1 frame em qualidade cheia do meio de CADA plano (folhas 2x2) — olhar todas: zoom no lugar certo, texto legível e não em cima de nada importante, nenhum plano caindo em tela de loading/menu sem querer.
11. **Entregar**: caminho do arquivo, o que tem (arcos), o que aprendeu. Registrar 1–3 lições no arquivo do estilo.

## Lembretes que mais erram
- Mostrar a ação (a morte/queda inteira), não só a fala sobre ela.
- Plano mínimo ~1,2s quando há fala/ação a entender.
- SFX nunca em cima de palavra.
- Não repetir o mesmo recurso; sem emoji; texto só quando acrescenta.
- Não bater duração com material fraco — avisar.

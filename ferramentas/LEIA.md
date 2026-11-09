# Ferramentas

Python: `ferramentas\venv\Scripts\python.exe` (criar com `setup.ps1`). ffmpeg/ffprobe no PATH. Modelo Whisper `small` em `ferramentas\models`.
Tudo pesado roda com prioridade baixa e 4 threads; rode UMA coisa pesada por vez.

| Arquivo | Para quê |
|---|---|
| `setup.ps1` | cria o venv (Python 3.12) e instala faster-whisper, numpy, pillow, yt-dlp |
| `render_narrado.py` | renderer do estilo **jogos-narrado**: imagens/clipes sobre a narração (zoom lento, meme sobre fundo desfocado, fades, grão, texto, imagem girando, música com ducking, sfx). Ver docstring; exemplo completo: `projetos/bioshock-infinite/edl_completo_v1.py`. Tem cache de planos (só re-renderiza o que mudou; mude `VERSAO_PLANO` ao mexer em `render_plano`), imagens animadas (`sobre` com x2/y2/mov), `contador`, reverb na voz (`voz_fx`) e `cortar_narracao()` |
| `colagem.py` | tema de papel do **jogos-narrado**: gera papel amassado/rasgado, recorte mal feito, pontilhado, jornal e letras recortadas, e renderiza as cenas (vídeo mudo; o áudio sai do `render_narrado`). Exemplo: `projetos/zelda-majoras-mask/teste_motion.py` |
| `colagem_kit.py` | peças prontas para montar cenas do tema de papel (asset, imagem/vídeo na folha, palavra recortada, profundidade, adiantamento). `pesado(cena)` = momento pesado (fundo preto, P&B, letra branca). Exemplo: `projetos/zelda-majoras-mask/teste_ritmo.py`; edição inteira: `projetos/death-stranding-solitude/edl_r4.py` |
| `render_narrado.render(..., tela=(1080, 1920))` | vídeo em pé (shorts): a legenda passa pra PlayRes 1080x1920. No `colagem`, setar `c.W, c.H = 1080, 1920` antes de montar qualquer peça. Base pronta de shorts em papel: `projetos/death-stranding-solitude/shorts/base.py` (trechos da narração -> short, legenda inteira, cartela "vídeo completo") |
| `render_narrado.vozes_personagem()` | voz de personagem só nos trechos marcados (timbres grave/aguda/radio/telefone/robo), antes da mistura |
| `recortar_assets.py` | separa as folhas de assets do usuário em peças com fundo transparente (`assets/jogos-narrado/imagens/colagem/`) |
| `ilhas_fala.py` | acha as ilhas de fala da narração (ilha sem palavra do whisper = respiração/ruído) |
| `voz_vs_fundo.py` | mede se a voz fica acima da música/efeitos na mistura (fala vs. pausas), por minuto. Bom: ≥ 12 dB |
| `transcribe_range.py audio.wav saida.jsonl INI FIM` | transcrição contínua em blocos de 60s, com tempo por palavra; retoma se cair |
| `transcribe_windows.py audio.wav cands.json saida.jsonl PRE POST` | transcreve só janelas em volta de candidatos |
| `dump_transcript.py entrada.jsonl saida.txt` | transcrição legível (uma fala por linha com h:mm:ss) |
| `words_range.py transcricao.jsonl "a-b" ...` | palavras com tempo exato nos intervalos (segundos) |
| `find_peaks.py audio.wav saida.json` | picos de reação no áudio (gritos/risadas) — só para triagem, nunca para escolher sozinho |
| `frames_windows.py video cands.json pasta PRE POST` | folhas de frames em volta de candidatos |
| `render_shots.py` | **o editor**: renderiza uma lista de planos (ver docstring). Usado pelas EDLs |
| `check_levels.py video` | volume a cada 0,5s; aponta ALTO/baixo |
| `editar_sem_ia.py video [--musica arq] [--final]` | **modo sem IA**: transcreve, mantém só os trechos com fala (corta pausas > 1,5s) e renderiza com o `render_shots.py`. Usado pelo `EDITAR-SEM-IA.bat` |
| `instalar.ps1` | instalador (rodado pelo `INSTALAR.bat`): pergunta Claude/Gemini/sem IA, instala o que falta via `winget`, cria o atalho; grava a escolha em `ia.txt` |
| `abrir_ia.bat "pedido"` | abre a IA gravada em `ia.txt` (`claude` ou `gemini`) com o pedido; os atalhos `Editor - *.bat` chamam ele |
| `conferir_render.py final.mp4` | 1 frame em qualidade cheia do meio de cada plano usado (folhas 2x2) — conferência do render final |

**Qualidade do render:** `render(..., qualidade="rascunho")` (padrão: 1280x720, veryfast, crf 21 — para revisar rápido) ou `qualidade="final"` (1920x1080, lanczos, medium, crf 17 — para entregar). O render também salva `<saida>_planos.json` (usado pela conferência).
| `audio_ref.py video INI DUR saida.txt` | análise de áudio de referência (fala + volume + picos) |
| `estudar_ref.ps1 -Url <link> -Nome <apelido>` | baixa referência, mede cortes, folhas de frames, fala |
| `vtt2txt.py legenda.vtt` | legenda do YouTube → texto com minutagem |
| `baixar_sons.ps1` / `baixar_musicas.ps1` | baixar sons de meme (myinstants) / trilhas do Rik (yt-dlp) |
| `make_sfx.py` | gera sons sintéticos sem copyright em `assets/sfx_gerados` |
| `niveis.json` | cache de volume médio de cada som/música (para nivelar) |

Folhas de frames do vídeo inteiro (**1 por segundo**, 6x5 = 30s por folha), em prioridade baixa:
```
ffmpeg -hide_banner -loglevel error -threads 2 -ss INI -t DUR -i VIDEO -an -vf "fps=1,scale=320:-2,drawtext=fontfile='C\:/Windows/Fonts/arial.ttf':text='%{pts\:hms\:INI}':fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6:x=4:y=4,tile=6x5" -q:v 4 pasta\f%04d.jpg
```
Momento-chave (4 frames/s, 12s por folha): troque `fps=1` por `fps=4` e `tile=6x5` por `tile=6x8`, com `-ss` alguns segundos antes da ação.

EDL mínima (`projetos/<nome>/edl.py`):
```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ferramentas"))
from render_shots import render
S = [{"src": (12.0, 14.5), "music": ("...mp3", 0, 0.42)}, {"src": (14.5, 16.0), "z": 1.4, "music_stop": True}]
render(VIDEO, S, SONS, IMAGENS, PASTA_TRABALHO, SAIDA_MP4)
```

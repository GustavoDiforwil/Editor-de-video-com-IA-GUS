# assets/

Os materiais de edição não vão pro repositório: músicas, sons de meme e imagens têm direitos de terceiros.
Esta pasta é onde você coloca os seus. Estrutura que as ferramentas esperam:

| Pasta | O que vai | Usado por |
|---|---|---|
| `fonts/BebasNeue-Regular.ttf` | Fonte Bebas Neue (licença livre OFL, baixe no [Google Fonts](https://fonts.google.com/specimen/Bebas+Neue)) | `render_shots.py` (texto estilo chat do jogo) |
| `musicas/` | Trilhas pra gameplay (`ferramentas/baixar_musicas.ps1` baixa uma lista; troque pela sua) | EDLs de gameplay |
| `sons/` | Sons de meme (`ferramentas/baixar_sons.ps1` baixa a lista) | EDLs de gameplay |
| `sfx_gerados/` | Efeitos sintetizados sem copyright: gere com `python ferramentas/make_sfx.py` | EDLs de gameplay |
| `sfx_externos/` | Sons de tiro pra montagem (de fora da gameplay) | `render_montagem.py` |
| `assets do narrando jogos/` | Suas folhas de desenhos/recortes pro tema de papel | `recortar_assets.py` |
| `jogos-narrado/` | Material do vídeo narrado em colagem: `imagens/colagem/` (peças recortadas), `sons/` (papel, clique de câmera), `musicas/`, `videos/` | `render_narrado.py`, `colagem_kit.py` |

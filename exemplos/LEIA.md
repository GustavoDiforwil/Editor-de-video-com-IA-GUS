# exemplos/

Duas edições reais, pra mostrar o formato de uma EDL (a lista de edição que a IA escreve e o renderer transforma em vídeo).
Elas apontam pros vídeos e áudios da máquina do autor, então **não rodam como estão**: servem de referência.

| Arquivo | Estilo | O que mostra |
|---|---|---|
| `repo_2025_07_05/edl_v7_5min.py` | Gameplay Rik | O vídeo-modelo do estilo: ~5 min tirados da 1ª hora de R.E.P.O., com planos curtos, zoom, freeze, música e efeitos (`render_shots.py`) |
| `death-stranding-solitude/edl_r4.py` | Jogos Narrado | Uma edição inteira em colagem de papel sobre a narração, com vozes de personagem e legendas (`colagem_kit.py` + `render_narrado.py`) |

Pra usar com um vídeo seu: crie `projetos/<nome-do-video>/`, copie um destes pra lá e troque os caminhos do topo do arquivo.
Os dois importam as ferramentas por caminho relativo (`../../ferramentas`), então funcionam em `projetos/<video>/` ou em `exemplos/<video>/`.

---
name: revisar-edicao
description: Checklist de revisão de uma edição (EDL e vídeo renderizado) antes de entregar ao usuário. Use antes de cada render/entrega ou quando ele pedir "revisa".
---

# Revisar edição

Na EDL:
- [ ] Cada momento-chave mostra a AÇÃO (frames conferidos), não só a fala sobre ela; setup e payoff visíveis.
- [ ] Nenhum plano com fala/ação a entender abaixo de ~1,2s.
- [ ] Nenhum SFX começando antes do fim da última palavra do plano (conferir com `words_range.py`).
- [ ] Recursos contados: preto e branco ≤1, repetição de fala ≤1, freeze/cartela poucos, time-lapse ≤1 e só se cabe, texto só onde acrescenta.
- [ ] Nada da lista NÃO fazer do estilo (emoji, sons vetados, apresentação de personagens…).
- [ ] Música troca por arco e corta seco nos punchlines; silêncio só quando é piada.
- [ ] Fio de história claro (abertura, arcos, clímax, final).

No vídeo renderizado:
- [ ] `check_levels.py`: pico ≤ −1 dB, sem trechos "ALTO"; trechos "baixo" só onde o silêncio é proposital.
- [ ] `ffprobe`: duração de vídeo e áudio iguais (diferença < 0,1s) e ambos começando em 0.
- [ ] Contact sheet (`fps=1/4,tile`) olhada: zooms no lugar certo, textos legíveis, nada cortado.
- [ ] No render FINAL (1080p): `conferir_render.py` rodado e TODAS as folhas olhadas (qualidade cheia, 1 frame por plano). Nenhum plano em tela de loading/menu sem intenção; texto não cobre nada importante.
- [ ] Duração próxima do pedido; se ficou curta por falta de material bom, avisar em vez de encher.

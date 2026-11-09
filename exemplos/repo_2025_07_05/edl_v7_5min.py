"""v7 — 5 minutos da 1ª hora (vista inteira: transcrição contínua + frames a cada 3s).

Fio da meada: o "pai do Gustavo" (quadro assombrado) → caos na loja → slackers → JP morre →
saga do Capiche (morre / "está vivo" / morre de novo) → banana → pato → o narrador cai no MESMO buraco
que zoou o JP → GAME OVER → "KING OF THE LOSERS" → "estou com coroinha, meu patrão". Pós-créditos: macaco.

Orçamento de recursos (regras do usuário): repetição artificial 1x (os "Não!" do pato), PB 1x (morte do
Capiche), freeze 1x (chat "they deserted me"), time-lapse 1x (banana), texto só onde ajuda (3x),
vine boom 2x, metal pipe 1x, taco bell 1x, what 1x, wrong 1x. Sem emoji, sem tema triste do Chaves,
sem risada/tururu/"que isso meu filho".
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ferramentas"))
from render_shots import render  # noqa: E402

W_ = r"D:\rik_edicao\Gravar_2025_07_05"
SRC = r"D:\Gravar_2025_07_05_22_26_26_696.mp4"
SONS = r"D:\edicao-rik\assets\sons"
IMG = r"D:\edicao-rik\assets\sons"
MUS = r"D:\edicao-rik\assets\musicas"


def m(nome, off=0.0, vol=0.42):
    return (os.path.join(MUS, nome + ".mp3"), off, vol)


S = []
add = S.append

# ── ABERTURA (flash-forward): a loja sendo destruída a laser, "Eu morrei!"
add({"src": (3561.0, 3562.6)})
add({"src": (3563.0, 3564.4), "z": 1.3, "shake": True})
add({"src": (3578.2, 3579.9), "z": 1.5})

# ── "Cadê o Gustavo?" / "Valeron Gustavo" / "o que o meu tapete tá gritando?"
add({"src": (3.2, 6.4), "music": m("sweet_sweet_honey")})
add({"src": (12.3, 13.7), "z": 1.25})
add({"src": (14.7, 16.4)})

# ── O PAI DO GUSTAVO (quadro assombrado)
add({"src": (124.2, 125.6), "music": m("folli_the_foal")})
add({"src": (131.4, 133.8)})
add({"src": (136.5, 137.5)})
add({"src": (137.5, 139.6), "z": 1.0, "z2": 1.9, "cx": 0.72, "cy": 0.08})        # zoom no quadro
add({"src": (139.6, 141.2)})
add({"src": (141.7, 143.3), "z": 1.3, "music_stop": True})
add({"src": (179.9, 183.2), "music": m("folli_the_foal", 6)})
add({"src": (183.3, 187.0), "z": 1.3})

# ── LOJA: "a vida é de quem?"
add({"src": (246.8, 248.0), "music": m("chicken_old_ladies")})
add({"src": (252.0, 253.6)})
add({"src": (253.6, 255.6), "z": 1.3})
add({"src": (257.5, 259.2)})
add({"src": (260.4, 262.4)})
add({"src": (263.1, 265.2), "z": 1.25})
add({"src": (273.0, 274.3), "vol": 0.0, "music_stop": True})                   # cara do robô, silêncio
add({"src": (306.5, 309.0), "music": m("chicken_old_ladies", 12)})
add({"src": (317.5, 321.5)})
add({"src": (321.5, 323.5), "z": 1.3})
add({"src": (330.9, 332.0), "z": 1.5})

# ── "DESTROYING SLACKERS": ficou pra fora do caminhão
add({"src": (375.0, 377.6), "music": m("dangerous_raid")})
add({"src": (377.6, 378.5)})
add({"src": (378.5, 380.0), "z": 1.3, "shake": True, "music_stop": True, "sfx": [("taco_bell", 0.0, 0.5)]})
add({"src": (389.0, 392.1)})

# ── "Gustavo, tem feito muitos chifres?"
add({"src": (434.2, 440.4), "music": m("sarah_chaves")})
add({"src": (1248.0, 1249.8), "vol": 0.0, "z": 1.1, "music_stop": True, "sfx": [("what", 0.3, 0.5)]})

# ── "Gustavo! Gustavo! Gustavo!" / a caveira / JP morre
add({"src": (540.3, 543.7), "music": m("sanctuary_guardian")})
add({"src": (546.4, 549.0)})                                                   # "cadê a caveira?"
add({"src": (549.9, 550.9), "z": 1.3})                                         # "foi atrás do Capiche"
add({"src": (585.6, 587.0), "z": 1.3, "cx": 0.9, "cy": 0.45, "music_stop": True, "sfx": [("vine_boom", 0.35, 0.55)]})
add({"src": (604.3, 605.1)})
add({"src": (621.9, 624.1), "music": m("sanctuary_guardian", 20)})
add({"src": (627.6, 628.6), "z": 1.3})
add({"src": (636.2, 638.3)})
add({"src": (640.3, 642.8), "words": [("linguadão.", 641.3)]})

# ── "esse é o arrombado que me matou... deixa eu fazer carinho"
add({"src": (770.8, 772.4), "z": 1.4, "music": m("holiday_fun")})
add({"src": (773.5, 775.8)})
add({"src": (780.8, 783.4)})
add({"src": (783.6, 785.8), "z": 1.3})
add({"src": (811.7, 815.6), "music_stop": True})                               # "gente, eu estou sozinha..."
add({"src": (913.6, 915.0), "z": 1.4})
add({"src": (917.2, 921.0)})

# ── abandonado no chão por 1 minuto e meio
add({"src": (1014.9, 1017.2)})
add({"freeze": (1110.5, 1.4), "z": 2.4, "cx": 0.0, "cy": 1.0})                 # chat: "They deserted me..."
add({"src": (1116.9, 1119.6)})

# ── atirando no Gustavo na loja
add({"src": (1176.8, 1178.0), "music": m("laugh_a_minute")})
add({"src": (1179.4, 1181.9), "z": 1.2})
add({"src": (1187.6, 1189.0)})
add({"src": (1193.1, 1194.6), "z": 1.4})
add({"src": (1231.2, 1234.3)})
add({"src": (1235.1, 1237.2), "z": 1.25})
add({"src": (1202.2, 1203.4), "z": 1.3})                                       # "a panela não foi!"
add({"src": (1204.2, 1205.9)})
add({"src": (1209.9, 1211.3), "z": 1.4})

# ── caldeirão / "pra esquecer de sua mamãe"
add({"src": (1332.9, 1336.3), "music": m("horlepiep")})
add({"src": (1341.4, 1343.9), "z": 1.2})
add({"src": (1462.0, 1463.2)})
add({"src": (1465.3, 1468.4), "z": 1.3})

# ── SAGA DO CAPICHE
add({"src": (1402.3, 1403.4), "music": m("much_ado")})
add({"src": (1407.6, 1409.7)})
add({"src": (1411.2, 1414.3)})
add({"src": (1414.3, 1418.1), "z": 1.25})
add({"src": (1418.1, 1419.8), "z": 1.5})
add({"src": (1736.2, 1739.4)})
add({"src": (1748.9, 1751.6), "z": 1.0, "z2": 1.3, "bw": True, "music_stop": True})  # "o Capiche morreu?"
add({"src": (1805.6, 1807.0)})
add({"src": (1809.8, 1810.9)})
add({"src": (1811.8, 1814.0), "z": 1.3})
add({"src": (1908.1, 1909.1), "z": 1.5, "music": m("peppy"), "sfx": [("vine_boom", 0.1, 0.55)]})  # "está VIVO"
add({"src": (1911.5, 1913.6)})
add({"src": (1915.6, 1916.7), "z": 1.3})
add({"src": (1916.9, 1918.9), "words": [("agressivamente.", 1918.2)]})
add({"src": (2100.7, 2103.4)})
add({"src": (2144.0, 2145.7)})
add({"src": (2147.4, 2150.0), "z": 1.3})
add({"src": (2303.0, 2306.0), "music": m("peppy", 10)})                       # "é um patinho... cuidado"
add({"src": (2315.3, 2317.2), "z": 1.25})
add({"src": (2318.3, 2319.0), "music_stop": True})
add({"src": (2319.0, 2320.3), "z": 1.45, "shake": True})
add({"src": (2322.2, 2323.6)})
add({"src": (3328.6, 3330.0)})
add({"src": (3333.3, 3335.4), "z": 1.25})
add({"src": (3504.2, 3505.3), "z": 1.4, "music_stop": True})                  # "como é que você morreu, capiche?"

# ── LOJA: "como é que lê?" (e tudo explode)
add({"src": (1983.6, 1985.4), "z": 1.3, "shake": True, "music": m("jumping_cricket")})
add({"src": (1986.3, 1989.3)})
add({"src": (1990.1, 1991.9), "z": 1.25})
add({"src": (1991.9, 1994.0)})
add({"src": (1994.0, 1995.0), "z": 1.6})
add({"src": (1998.0, 2000.8)})

# ── A BANANA
add({"src": (2474.6, 2476.0), "music": m("tom_fool")})
add({"src": (2486.7, 2489.6)})
add({"src": (2490.0, 2491.6), "vol": 0.0, "z": 1.2})
add({"src": (2496.0, 2616.0), "speed": 20})                                    # 2 minutos de banana em 6s
add({"src": (2790.6, 2794.0), "music": m("skipping_class")})
add({"src": (2805.8, 2806.7), "z": 1.3})
add({"src": (2806.9, 2808.9)})
add({"src": (2822.4, 2824.3), "z": 1.25})

# ── setup: o JP caiu no buraco (e ele riu)
add({"src": (2638.7, 2641.4), "music_stop": True})
add({"src": (2648.8, 2650.6), "z": 1.3})

# ── O PATO
add({"src": (2866.9, 2871.0), "music": m("ladies_on_the_loose")})
add({"src": (2879.9, 2881.7), "z": 1.25})
add({"src": (2884.9, 2886.2)})
add({"src": (2897.9, 2898.6), "z": 1.4})
add({"src": (2904.2, 2907.1)})
add({"src": (2908.3, 2909.7)})
add({"src": (2913.8, 2915.6)})
add({"src": (2915.6, 2917.6), "z": 1.3})
add({"src": (2917.6, 2919.3), "z": 1.6, "shake": True})

# ── CLÍMAX: "não vai dar, né? 12 mil" → cai no MESMO buraco → rei dos perdedores
add({"src": (2991.6, 2993.0), "music": m("jeopardy_think", 0, 0.5), "sfx": [("wrong", 1.0, 0.35)]})
add({"src": (3000.1, 3001.0)})
add({"src": (3001.8, 3003.6), "z": 1.3, "shake": True, "music_stop": True, "sfx": [("metal_pipe", 0.4, 0.5)]})
add({"src": (3004.5, 3006.2)})
add({"src": (3010.8, 3013.2), "z": 1.2, "words": [("eu falei do joão pedro", 3011.0), ("e morri igual.", 3012.5)]})
add({"src": (3016.0, 3019.5), "z": 1.0, "z2": 1.15})
add({"src": (3023.5, 3027.5), "music": m("faustao_2002", 0, 0.5)})
add({"src": (3044.5, 3046.0)})
add({"src": (3050.3, 3052.3)})
add({"src": (3055.8, 3057.6), "z": 1.0, "z2": 1.25})
add({"src": (3093.0, 3095.0)})
add({"src": (3096.5, 3099.3)})
add({"src": (3099.3, 3101.7), "z": 1.4})

# ── volta do pai: "seu pai é aquele safado"
add({"src": (3273.2, 3276.6), "music": m("folli_the_foal", 20)})
add({"src": (3279.9, 3282.9), "z": 1.3, "music_stop": True})

# ── pós-créditos: o deus macaco
add({"color": "black", "dur": 0.6})
add({"src": (3337.5, 3343.0)})
add({"src": (3529.0, 3535.6), "z": 1.3})

if __name__ == "__main__":
    render(SRC, S, SONS, IMG, W_, os.path.join(W_, "rik_v7_5min.mp4"))

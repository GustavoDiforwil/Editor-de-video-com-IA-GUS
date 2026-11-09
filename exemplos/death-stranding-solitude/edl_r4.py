"""Solitude — gravação 2 (roteiro v4: o livro "Solidão", do Anthony Storr). Edição inteira do zero no tema de papel
(estilo Jogos Narrado, NÚCLEO). Modelo: projetos/zelda-majoras-mask/teste_junto.py.

Tempos das cenas = tempos da narração ORIGINAL (narracao2.wav / palavras2.txt). V() leva pro vídeo: passa pelo corte
(mapa_tempo2.json, de corte_narracao2.py) e soma EM + as vinhetas de capítulo (silêncio inserido na narração).

Fios recorrentes: o livro do Storr (capa volta toda vez que ele é citado) · o "sofá" (a moça lendo do Hammershøi = alguém
por perto) · o bebê e a colher (o BB no pote do Death Stranding) · o amigo do "jogo de gente triste" · o bilhete fixado
"não precisar de ninguém" (a pegadinha: plantado no cap. I, volta no fim do cap. II e no momento pesado do cap. III).
Momento pesado (fundo preto, P&B, sem piada): do mercado até "sem nada guardado por dentro".

uso: edl_r4.py quadros  -> folhas com 1 quadro por cena (render/quadros_r4/)
     edl_r4.py mudo     -> só a imagem (blocos de 60s em _papel/_blocos/, retoma)
     edl_r4.py audio    -> só refaz a mistura
     edl_r4.py          -> imagem + mistura
     edl_r4.py refaz 3 5 -> apaga os blocos 3 e 5 antes
"""
import json
import os
import random
import re
import subprocess
import sys
import unicodedata

from PIL import Image, ImageDraw, ImageOps

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ferramentas"))
import colagem as c  # noqa: E402
import render_narrado as rn  # noqa: E402
from colagem import Camada, DETALHE  # noqa: E402
from colagem_kit import A, abrir, cena, com_imagem, com_video, frente_peca, fundo_peca, palavra, peca, pesado, som, texto  # noqa: E402
from colagem_kit import ciclo, fala_e_pisca, foto_viva, olho_piscando, piscadas, pontos_sumindo, tela_chiando, tela_rolando  # noqa: E402

P = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(P, "_papel")
GQ = os.path.join(TMP, "gp")
BLOCOS = os.path.join(TMP, "_blocos")
os.makedirs(BLOCOS, exist_ok=True)
VERSAO = "r4v1"
SAIDA = os.path.join(P, "render", f"solitude_{VERSAO}.mp4")
EM = 0.2
VIN = 3.6
ADIANTA = 0.17
QUEBRAS = [36.0, 147.5, 338.5]  # vinhetas (tempo ORIGINAL, no meio da pausa): fim da intro, cap. II, cap. III
PES_A, PES_B = 359.3, 391.6     # momento pesado (tempo original)

# ---------- tempo: original -> narração cortada -> vídeo ----------
_MAPA = json.load(open(os.path.join(P, "mapa_tempo2.json"), encoding="utf-8"))
NARR_TOTAL = _MAPA[-1][1]
ILHAS = [(a, b, f) for a, b, f, _ in _MAPA[:-1]]


def CUT(o):
    """tempo original -> tempo na narração cortada (pedaço que saiu: vai pro começo da próxima ilha)"""
    for a, b, f in ILHAS:
        if a - 0.06 <= o <= b + 0.1:
            return round(f + max(0.0, o - a), 3)
    for a, b, f in ILHAS:
        if a > o:
            return f
    return NARR_TOTAL


def V(o):
    return round(CUT(o) + EM + VIN * sum(1 for q in QUEBRAS if o >= q), 2)


def FIM_FALA(o):
    """fim (no vídeo) da ilha de fala que contém ou vem antes de o: onde cabe efeito sonoro"""
    antes = [(a, b) for a, b, _ in ILHAS if a <= o + 0.01]
    a, b = antes[-1]
    return V(b) + 0.06


FIM = V(QUEBRAS[-1] + 1) + (NARR_TOTAL - CUT(QUEBRAS[-1] + 1)) + 1.6


def _norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(ch for ch in w if unicodedata.category(ch) != "Mn"))


PALAVRAS = []
for _l in open(os.path.join(P, "transcricao2.jsonl"), encoding="utf-8"):
    for _s in json.loads(_l)["segs"]:
        PALAVRAS += [(w[0], _norm(w[2])) for w in _s["words"]]
PALAVRAS.sort()


def W(p, perto, janela=2.5):
    """instante ORIGINAL em que a palavra é dita, perto de 'perto'"""
    alvo = _norm(p)
    cs = [t for t, w in PALAVRAS if abs(t - perto) <= janela and (w == alvo or w.startswith(alvo))]
    if not cs:
        print(f"  [W] não achei '{p}' perto de {perto}")
        return perto
    return min(cs, key=lambda t: abs(t - perto))


# ---------- peças ----------
SEED = [500]


def _s():
    SEED[0] += 1
    return SEED[0]


def _de(d):
    return None if d is None else V(d)


def Pc(nome, lado, x, y, de=None, rot=0, **kw):
    return peca(nome, lado, x, y, rot=rot, de=_de(de), seed=_s(), z=kw.pop("z", 1.3), **kw)


def Fd(nome, lado, x, y, de=None, rot=0, **kw):
    return fundo_peca(nome, lado, x, y, rot=rot, seed=_s(), de=_de(de), **kw)


def TX(txt, fs, x, y, de, rot=-4, ent="pop"):
    cm = texto(txt, fs, x, y, V(de), rot=rot, seed=_s())
    cm.entrada = ent
    return cm


def PAL(txt, x, y, de, alt=128, passo=0.03, ent="queda"):
    return palavra(txt, x, y, V(de), alt=alt, passo=passo, seed=_s(), entrada=ent)


def AS(nome, lado, x, y, de, rot=0, ent="pop", **kw):
    """asset do usuário como Camada solta (motion: caminhos, chaves, cópias)"""
    im = abrir(nome, lado)
    if kw.pop("espelho", False):
        im = ImageOps.mirror(im)
    caminho = kw.pop("caminho", None)
    if caminho:
        caminho = [(V(t), x_, y_) for t, x_, y_ in caminho]
    ch = kw.pop("chaves", None)
    cm = Camada(im, x, y, rot=rot, de=V(de), amp=kw.pop("amp", 5), gira=kw.pop("gira", 1.0), seed=_s(), entrada=ent,
                z=kw.pop("z", 1.3), sombra=kw.pop("sombra", 14), caminho=caminho, **kw)
    if ch:
        cm.chaves = {k: [(V(t), v) for t, v in pts] for k, pts in ch.items()}
    return cm


def net(n):
    """imagem do projeto (net/) ou do material do estilo (memes, pinturas...)"""
    for pasta in [os.path.join(P, "net")] + [os.path.join(A, "imagens", d) for d in os.listdir(os.path.join(A, "imagens"))]:
        for ext in (".jpg", ".png"):
            if os.path.exists(os.path.join(pasta, n + ext)):
                return os.path.join(pasta, n + ext)
    raise FileNotFoundError(n)


_REC = {}


def _recorte(arq, lado, caixa=None, forma="ret"):
    k = (arq, lado, caixa, forma)
    if k not in _REC:
        im = Image.open(arq).convert("RGB")
        if caixa:
            W_, H_ = im.size
            im = im.crop((int(caixa[0] * W_), int(caixa[1] * H_), int(caixa[2] * W_), int(caixa[3] * H_)))
        e = lado / max(im.size)
        im = im.resize((round(im.width * e), round(im.height * e)), Image.LANCZOS).convert("RGBA")
        _REC[k] = c.recorte_mal(im, forma, seed=len(_REC) + 7, torto=0.03)
    return _REC[k]


def RC(nome, lado, x, y, de, caixa=None, ent="queda", forma="ret", **kw):
    """recorte de uma imagem da net (capa do livro, foto, colher...) como peça solta"""
    caminho = kw.pop("caminho", None)
    if caminho:
        caminho = [(V(t), x_, y_) for t, x_, y_ in caminho]
    ch = kw.pop("chaves", None)
    img = kw.pop("img", None) or _recorte(net(nome), lado, caixa, forma)
    cm = Camada(img, x, y, rot=kw.pop("rot", 5), de=V(de), amp=4, gira=0.8, seed=_s(), entrada=ent,
                z=kw.pop("z", 1.3), sombra=18, caminho=caminho, **kw)
    if ch:
        cm.chaves = {k: [(V(t), v) for t, v in pts] for k, pts in ch.items()}
    return cm


def LIVRO(lado, x, y, de, ent="queda", **kw):
    """a capa do 'Solidão' (Storr): personagem recorrente — volta toda vez que o livro é citado"""
    return RC("storr-capa", lado, x, y, de, ent=ent, **kw)


def EXP(raio, x, y, de, vel=40, seed=7):
    return Camada(c.explosao(raio, seed=seed), x, y, de=V(de), amp=3, gira=0.4, sombra=14, seed=_s(), entrada="gira", vel=vel, z=0.15)


def VIVO(sprites, x, y, de, chaves, rot=0, ent="pop", **kw):
    ch = {k: [(V(t), v) for t, v in pts] for k, pts in chaves.items()}
    caminho = kw.pop("caminho", None)
    if caminho:
        caminho = [(V(t), x_, y_) for t, x_, y_ in caminho]
    return Camada(None, x, y, rot=rot, de=V(de), amp=kw.pop("amp", 4), gira=kw.pop("gira", 0.8), seed=_s(), entrada=ent,
                  z=kw.pop("z", 1.3), sombra=kw.pop("sombra", 16), sprites=sprites, chaves=ch, caminho=caminho, **kw)


def FALAS(t0, t1):
    return [(t, t + 0.24) for t, _ in PALAVRAS if t0 <= t <= t1]


def olhar(t0, t1, seed=4):
    ch = piscadas(t0, t1, cada=1.4, seed=seed)
    r = random.Random(seed)
    extra, t = [], t0 + 0.5
    while t < t1 - 0.4:
        lado = r.choice((3, 4))
        extra += [(t, lado), (t + 0.45, 0)]
        t += r.uniform(1.0, 1.6)
    return sorted(ch + extra)


def VAIVEM(t0, t1, x, y, dx, dy, passo=0.2):
    pts, t, k = [], t0, 0
    while t <= t1:
        pts.append((t, x + (dx if k % 2 else 0), y + (dy if k % 2 else 0)))
        t += passo
        k += 1
    return pts


def GIRA(t0, passos):
    """chaves de rotação: [(dt, graus)] a partir de t0"""
    return {"rot": [(t0 + dt, g) for dt, g in passos]}


OLHO_P = olho_piscando(300)
BALAO = pontos_sumindo(520)
TV = tela_chiando("tv-cabeca", 640, (0.28, 0.25, 0.71, 0.56), tirar=((0.0, 0.43, 0.37, 1.0), (0.6, 0.41, 1.0, 1.0)))
CEL = tela_rolando("celular-maos", 700, (0.45, 0.35))
AMIGO = foto_viva("d01", 540, boca=(0.28, 0.515, 0.45, 0.64))      # o amigo do "jogo de gente triste"
MAE = foto_viva("c07", 600, olhos=((0.585, 0.265, 0.655, 0.295), (0.70, 0.262, 0.785, 0.292)))  # "filho, você não sai não?"


def CABECA(x, y, de, abre, lado=600):
    """a cabeça (d01) com a tampa (d00): a tampa pula e o cérebro (c06) sobe lá de dentro"""
    s = lado / 1152
    cab = Camada(abrir("d01", lado), x, y, de=V(de), amp=3, gira=0.4, seed=_s(), entrada="sobe", z=0.5, sombra=18)
    fx, fy = x + 59 * s, y - 669 * s
    ax, ay = x + 90 * s, y - 1000 * s
    tampa = Camada(abrir("d00", round(771 * s)), fx, fy, de=V(de), amp=3, gira=0.4, seed=_s(), entrada="sobe", z=0.5, sombra=18,
                   caminho=[(V(abre), fx, fy), (V(abre) + 0.18, ax, ay - 40 * s), (V(abre) + 0.4, ax, ay)], flutua=(10, 0.8))
    tampa.chaves = {"rot": [(V(abre), 0), (V(abre) + 0.18, -18), (V(abre) + 0.5, -10)]}
    cer = Camada(abrir("c06", round(560 * s)), x, y - 420 * s, de=V(abre), amp=3, gira=0.6, seed=_s(), entrada=None, z=0.5, sombra=14,
                 caminho=[(V(abre), x, y - 380 * s), (V(abre) + 0.5, x, y - 760 * s)], pulsa=(0.04, 2.0))
    return [cer, cab, tampa]


# ---------- papéis feitos aqui ----------
def _papel(w, h, seed, cor=(0xF0, 0xEA, 0xD8)):
    return c.rasgar(c.amassado(w, h, cor, seed, forca=0.12), "tblr", amp=12, fibra=7, seed=seed)


def bilhete(txt, seed=61):
    """o bilhete da pegadinha, escrito à mão: 'não precisar de ninguém'"""
    n = c.nota(txt, 64)
    pap = _papel(n.width + 90, n.height + 110, seed, (0xF4, 0xEC, 0xC8))
    pap.alpha_composite(n, (45, 70))
    return pap


def prova():
    """'parece pergunta de prova': a folha da prova com a questão"""
    pap = _papel(860, 700, 52)
    pap.alpha_composite(c.nota("PROVA", 70, (30, 28, 26)), (330, 30))
    d = ImageDraw.Draw(pap)
    d.line([(60, 140), (800, 140)], fill=(90, 86, 80, 255), width=4)
    pap.alpha_composite(c.nota("Questão 1:", 54, (30, 28, 26)), (70, 170))
    for k in range(5):
        y = 470 + k * 44
        d.line([(80, y), (790, y)], fill=(150, 146, 140, 255), width=3)
    return pap


def etiqueta(linhas, carimbo=None, seed=71):
    """etiqueta da encomenda (Death Stranding = entregas): DESTINATÁRIO / CONTEÚDO / REMETENTE"""
    pap = _papel(980, 560, seed, (0xEE, 0xE4, 0xCC))
    d = ImageDraw.Draw(pap)
    d.rectangle((40, 40, 940, 520), outline=(40, 36, 32, 255), width=5)
    y = 80
    for rot, val in linhas:
        pap.alpha_composite(c.nota(rot, 46, (40, 36, 32)), (70, y))
        pap.alpha_composite(c.nota(val, 50), (100, y + 62))
        y += 200
    return pap


def capa_edith():
    """a capa do 'Seven Years Solitary' é de pano vermelho liso: cola uma tira de papel com o título e a autora"""
    im = Image.open(net("edith-capa")).convert("RGBA")
    e = 520 / im.height
    im = im.resize((round(im.width * e), 520), Image.LANCZOS)
    tira = _papel(im.width - 40, 170, 81, (0xF4, 0xEE, 0xDC))
    tira.alpha_composite(c.nota("Seven Years\nSolitary", 46, (30, 28, 26)), (24, 10))
    im.alpha_composite(tira, (20, 60))
    rod = c.nota("Edith Bone", 40, (240, 236, 226))
    im.alpha_composite(rod, ((im.width - rod.width) // 2, 440))
    return c.recorte_mal(im, "ret", seed=82, torto=0.03)


# ---------- gameplay ----------
GP_INI = {}
for _l in open(os.path.join(P, "baixar_gameplay.py"), encoding="utf-8"):
    _m = re.match(r'\s*"([\w-]+)": \(\w+, (\d+), (\d+)\),', _l)
    if _m:
        GP_INI[_m.group(1)] = int(_m.group(2))
GP_INI.update({"bb-fofo": 0, "bb-acalmar": 0, "bb-deadman": 0})
SEM_LEGENDA = "iw*0.834:ih*0.834:iw*0.083:ih*0.01"
CROP = {"chuva-a": None, "chuva-b": None, "rio": None, "gs-links": None,
        "gs-estrutura": SEM_LEGENDA, "gs-estrada": SEM_LEGENDA,
        "bb-fofo": "iw*0.78:ih*0.78:iw*0.11:ih*0.09",       # tira o selo do canto e a legenda de baixo
        "bb-acalmar": "iw*0.56:ih*0.56:iw*0.2:ih*0.26",     # só o pote (o HUD fica dos lados)
        "bb-deadman": "iw*0.86:ih*0.86:iw*0.0:ih*0.02"}     # tira a marca do canto de baixo

POS = [(860, 500, -1.6, (-1500, 0)), (1090, 520, 1.8, (1500, 0)), (900, 470, 1.2, (0, -1100)),
       (1040, 540, -1.4, "pulo"), (840, 520, 1.6, (0, 1100)), (1100, 480, -1.8, (1500, 0))]
CAMS = [(-14, 6, 14, -6), (12, -6, -12, 6), (0, 12, 0, -12), (-12, 0, 12, 0), (10, 6, -10, -6), (0, -10, 0, 10)]
SPECS = []


def S(t, pr=None, pecas=(), ex=(), cam=None, socos=(), tremor=(), zoom=None):
    """cena a partir do instante ORIGINAL t até a próxima. pr: IMG(...) | VID(...) | Camada | None"""
    plano = []
    for e in ex:
        plano += e if isinstance(e, list) else [e]
    SPECS.append(dict(t=t, pr=pr, pecas=list(pecas), ex=plano, cam=cam, zoom=zoom, socos=[(V(a), f) for a, f in socos],
                      tremor=[(V(a), d, f) for a, d, f in tremor]))


def IMG(nome, w=1040, h=640, pos=None, caixa=None, entrada="padrao"):
    return ("img", nome, w, h, pos, caixa, entrada)


def VID(nome, t_orig, w=1280, h=720, pos=None, entrada="padrao", vcrop="padrao"):
    return ("vid", nome, t_orig, w, h, pos, entrada, vcrop)


M = 0.5
ZI, ZF = (1.0, 1.07), (1.0, 1.12)
NOTA = bilhete("não precisar\nde ninguém.")
ED = capa_edith()

# =====================================================================================================
# INTRODUÇÃO (rápida, ~1 imagem por segundo, motion: zoom contínuo, carimbo, peças atravessando)
# =====================================================================================================
# "Um amigo meu me viu jogar" — o Sam andando; o olho no canto espia (o amigo vendo)
S(1.5, VID("chuva-a", 10.0, pos=(900, 500, -1.6, "pulo")),
  [Fd("b13", 520, 1640, 820)],
  [VIVO(OLHO_P, 1600, 280, 2.4, {"q": olhar(2.4, 3.6)}, rot=6, ent="carimbo")],
  zoom=ZI, cam=(0, 0, 0, 0))
# "num jogo em que você passa 30 horas" — o relógio gira rápido, 30 horas batem como carimbo
S(3.6, None,
  [Fd("a13", 480, 1600, 300, vel=-160)],
  [AS("a00", 620, 900, 500, 3.6, ent="gira", vel=-420, z=M), TX("30 horas", 150, 960, 900, W("30", 4.2), rot=-5, ent="carimbo")],
  zoom=ZF, socos=[(W("30", 4.2), 0.06)], cam=(0, 0, 0, 0))
# "sozinho," — o Sam sozinho na praia, zoom
S(W("sozinho", 4.9) - 0.1, VID("praia", 1810.0, pos=(960, 500, 1.4, "pulo")),
  [Fd("a01", 420, 1680, 820, flutua=(10, 0.6))], [], zoom=(1.0, 1.12))
# "Death Stranding." — o título do jogo
S(5.6, VID("paisagem", 103.0, pos=(940, 480, -1.2, (0, -1100))),
  [], [TX("(Death Stranding)", 84, 1450, 900, 5.8, rot=-4, ent="carimbo")], zoom=ZI)
# "E falou:" — o amigo sobe, já com a boca mexendo
S(8.35, None,
  [Fd("b09", 420, 1620, 280, flutua=(8, 0.7))],
  [VIVO(AMIGO, 760, 620, 8.4, {"q": fala_e_pisca(FALAS(8.4, 9.1), 8.4, 9.3, seed=3)}, ent="sobe", z=M)],
  zoom=ZI, cam=(-10, 0, 10, 0))
# "cara, isso é jogo de gente triste." (voz do amigo) — o balão sai da boca; TRISTE cai em letras; o joinha pra baixo
S(15.0, None,
  [Fd("a00", 480, 1620, 300, vel=-40)],
  [VIVO(AMIGO, 620, 620, 15.0, {"q": fala_e_pisca(FALAS(15.0, 17.2), 15.0, 17.6, seed=5)}, ent=None, z=M),
   AS("a02", 380, 1000, 300, 15.1, ent="carimbo", balanca=(5, 1.4)),
   AS("c01", 300, 1560, 640, W("triste", 16.7), ent="carimbo", chaves=GIRA(W("triste", 16.7) + 0.2, [(0, 0), (0.15, -14), (0.3, 10), (0.45, -12), (0.6, 0)]))]
  + PAL("TRISTE", 1180, 880, W("jogo", 16.3), alt=150, passo=0.05, ent="carimbo"),
  socos=[(W("triste", 16.7), 0.07)], zoom=ZI, cam=(0, 0, 0, 0))
# "Eu dei risada," — o Leo rindo
S(18.25, IMG("laughing-leo", 900, 640, (900, 500, -1.6, "pulo")), [Fd("b05", 300, 1640, 820, vel=60)], [], zoom=ZI)
# "mas fiquei com duas perguntas na cabeça." — a cabeça abre, sobem DUAS interrogações
S(19.05, None, [Fd("a04", 460, 1620, 280)],
  CABECA(800, 760, 19.05, W("perguntas", 19.6) - 0.2) +
  [AS("b09", 260, 1220, 300, W("perguntas", 19.6), ent="carimbo", balanca=(8, 1.2)),
   AS("c11", 240, 1500, 420, W("perguntas", 19.6) + 0.15, ent="carimbo", balanca=(8, 1.0)),
   TX("2", 160, 1360, 720, W("2", 19.5), rot=-6, ent="carimbo")], zoom=ZI, cam=(12, 0, -12, 0))
# "Por que tem gente que adora ficar sozinha" — a moça lendo sozinha, feliz da vida; estrelas
S(20.6, IMG("estudante", 760, 760, (880, 520, -1.6, (-1500, 0))),
  [Pc("b05", 220, 1560, 280, de=W("adora", 21.4), vel=90), Pc("b08", 160, 1700, 760, de=W("adora", 21.4) + 0.1, vel=-90)],
  [TX("adora", 110, 1500, 520, W("adora", 21.4), rot=-6, ent="carimbo")], zoom=ZI)
# "e gente que não aguenta 5 minutos?" — a ampulheta vira desesperada, a exclamação treme
S(22.7, None, [Fd("a13", 460, 360, 300, vel=180)],
  [AS("c03", 520, 900, 500, 22.7, ent="gira", z=M, chaves=GIRA(22.9, [(0, 0), (0.25, 180), (0.5, 180), (0.75, 360), (1.0, 360)])),
   AS("b07", 340, 1450, 500, W("aguenta", 23.3), ent="carimbo", balanca=(14, 3.0)),
   TX("5 minutos", 130, 960, 920, W("5", 23.5), rot=-4, ent="carimbo")],
  zoom=ZF, socos=[(W("5", 23.5), 0.06)], tremor=[(W("minutos", 23.8), 0.3, 6)], cam=(0, 0, 0, 0))
# "E quem não aguenta... dá pra aprender?" — a mão escreve; a lâmpada acende em "aprender"
S(24.85, None, [Fd("b09", 420, 1620, 300, flutua=(10, 0.7))],
  [AS("a09", 700, 900, 620, 24.9, ent="sobe", z=M, caminho=[(25.0, 900, 620), (25.8, 800, 650), (26.6, 960, 610)]),
   AS("a08", 300, 1380, 260, W("aprender", 26.3), ent="queda", pisca=1.0),
   TX("dá pra aprender?", 110, 1350, 880, W("dá", 26.0), rot=-4)], zoom=ZI, cam=(-12, 6, 12, -6))
# "Eu fui atrás" — a cientista de binóculo atravessa procurando
S(27.05, None, [Fd("a01", 440, 1640, 300, vel=20)],
  [AS("b14", 640, 0, 0, 27.1, ent=None, caminho=[(27.1, -300, 600), (28.1, 900, 600)], z=M)],
  zoom=ZI, cam=(0, 0, 0, 0))
# "e achei um livro de psiquiatra" — O LIVRO bate como carimbo, explosão atrás
S(W("achei", 28.1) - 0.05, None, [Pc("b05", 220, 1600, 260, de=28.3, vel=120), Pc("b08", 160, 320, 820, de=28.4, vel=-140)],
  [EXP(480, 960, 520, 28.1, vel=40), LIVRO(560, 960, 520, W("livro", 28.4), ent="carimbo", rot=-4),
   TX("psiquiatra", 100, 1500, 880, W("psiquiatra", 28.7), rot=-6)],
  socos=[(W("livro", 28.4), 0.08)], zoom=ZF, cam=(0, 0, 0, 0))
# "que responde as duas," — o livro de lado; as duas interrogações viram exclamação
S(29.45, None, [Fd("a00", 440, 1640, 820, vel=-30)],
  [LIVRO(460, 620, 520, 29.45, ent=None, rot=-6),
   AS("b09", 230, 1250, 330, 29.5, ent="pop"), AS("c11", 220, 1520, 330, 29.5, ent="pop"),
   AS("b07", 260, 1250, 330, W("duas", 30.1) - 0.1, ent="carimbo"), AS("b07", 260, 1520, 330, W("duas", 30.1), ent="carimbo")],
  zoom=ZI, cam=(10, 0, -10, 0))
# "e no meio do caminho achei uma coisa minha" — o Sam na trilha; a lupa atravessa
S(30.75, VID("chuva-a", 40.0, pos=(940, 500, 1.4, (1500, 0))), [],
  [AS("a11", 420, 0, 0, 31.4, ent=None, caminho=[(31.4, 2200, 760), (32.6, -300, 640)], rot=-10)], zoom=ZI)
# "que eu nunca contei pra ninguém." — o balão perde os pontos um a um: segredo
S(32.85, None, [Fd("b13", 520, 1600, 820)],
  [VIVO(BALAO, 900, 520, 32.9, {"q": [(32.9, 0), (W("nunca", 33.1), 1), (W("contei", 33.2) + 0.15, 2), (W("ninguem", 33.6), 3)]},
        ent="carimbo", balanca=(4, 1.2), z=M),
   TX("(nunca contei)", 90, 1450, 900, W("nunca", 33.1), rot=-5)], zoom=ZI, cam=(0, -8, 0, 8))

# =====================================================================================================
# CAPÍTULO I — FICAR SOZINHO É ERRADO?   (humor forte; música leve)
# =====================================================================================================
S(38.9, IMG("festa-multidao", 1060, 660, (940, 500, -1.4, (0, 1100))), [Fd("b06", 380, 1660, 820, vel=60)],
  [TX("gente feliz", 96, 1500, 230, W("feliz", 40.2), rot=6)], zoom=ZI)
S(42.6, IMG("festa-multidao", 1200, 680, (960, 500, 1.2, None), (0.25, 0.2, 0.75, 0.7)), [],
  [TX("gente\ngente\ngente", 88, 330, 300, 42.6, rot=-6), TX("(redundante)", 80, 1520, 880, 42.7, rot=-5)], cam=(0, 6, 0, -6))
# "foto de aniversário lotada" — a festa do Bruegel, o flash estoura (estrelas)
S(44.55, IMG("festa-pintura", 1040, 660, (1060, 500, 1.6, (1500, 0))),
  [Pc("b05", 260, 360, 260, de=W("lotada", 45.3), entrada="carimbo"), Pc("b08", 180, 520, 820, de=W("lotada", 45.3) + 0.1, entrada="carimbo")],
  [TX("foto do niver", 84, 380, 560, W("aniversario", 45.0), rot=-6)], socos=[(W("lotada", 45.3), 0.05)])
# "o grupo da família apitando" — o celular rola mensagem sem parar; o megafone grita
S(46.05, None, [Fd("a00", 440, 1640, 820, vel=60)],
  [VIVO(CEL, 860, 560, 46.1, {"q": ciclo(46.1, 48.4, 6, 0.1)}, rot=-4, ent="sobe", z=M),
   AS("a12", 380, 1450, 330, W("pintando", 47.4), ent="carimbo", balanca=(8, 2.4)),
   TX("grupo da família", 80, 1450, 860, W("familia", 46.5), rot=-5)])
# "sexta à noite em casa?" — a janela do Hammershøi de noite; o despertador
S(48.45, IMG("noite-janela", 1000, 680, (900, 500, -1.4, (0, -1100))),
  [Pc("a13", 300, 1640, 300, de=W("noite", 49.0), entrada="queda", balanca=(10, 1.4))],
  [TX("sexta, 22h", 90, 1500, 880, W("noite", 49.0), rot=-5)])
# "posta um story rapidinho, pra ninguém achar que você tá sozinho." — o celular; a de binóculo vigiando
S(49.85, None, [Fd("b13", 520, 1620, 820)],
  [RC("celular", 560, 860, 540, 49.9, caixa=(0.25, 0.05, 0.75, 0.95), ent="pulo", rot=-4),
   TX("story :)", 100, 860, 300, W("ensinar", 50.1), rot=-4, ent="carimbo"),
   AS("b14", 520, 1500, 640, W("ninguem", 51.2), ent="sobe", caminho=[(51.6, 1500, 640), (52.0, 1440, 620), (52.4, 1520, 650)])],
  cam=(-10, 0, 10, 0))
# "Se você tá sozinho, tem alguma coisa errada." — a sala vazia; a exclamação cai
S(52.85, IMG("sala-vazia", 940, 680, (900, 520, 1.4, (1500, 0))),
  [Pc("b07", 320, 1600, 640, de=W("errada", 54.5), entrada="queda", balanca=(10, 1.6))],
  [TX("algo errado.", 90, 1500, 260, W("errada", 54.5), rot=6)])
# "O meu amigo pensa assim," — o amigo concorda com a cabeça
S(55.0, None, [Fd("b09", 380, 1640, 300)],
  [VIVO(AMIGO, 760, 600, 55.0, {"q": fala_e_pisca([], 55.0, 56.3, seed=8), "rot": [(55.2, 0), (55.4, 4), (55.6, -2), (55.8, 4), (56.0, 0)]},
        ent="sobe", z=M), TX("o amigo", 90, 1350, 860, 55.3, rot=-5)])
# "a minha mãe pensa assim. 'Filho, você não sai não?'" (voz da mãe) — a mãe fala, o balão
S(56.25, None, [Fd("a00", 440, 1640, 820, vel=-30)],
  [VIVO(MAE, 820, 580, 56.3, {"q": fala_e_pisca(FALAS(57.8, 59.4), 56.3, 59.8, seed=9),
                              "rot": [(57.9, 0), (58.1, 2.5), (58.3, -1), (58.5, 2.5), (58.7, -1), (58.9, 0)]}, ent="sobe", z=M),
   AS("a03", 340, 1460, 280, W("filho", 57.9), ent="carimbo", balanca=(6, 1.4)), TX("a mãe", 90, 1460, 880, 56.5, rot=-4)])
# "Saio, mãe. Pro mercado." — a fila do mercado (a piada respira)
S(59.95, IMG("fila-mercado", 1000, 660, (980, 500, 1.6, "pulo")), [Fd("b09", 380, 330, 300)],
  [TX("(pro mercado)", 96, 1450, 900, W("mercado", 61.7), rot=-5, ent="carimbo")])
# "Só que em 1988," — o relógio volta no tempo; o ano carimba
S(63.65, None, [Fd("b13", 520, 1640, 820)],
  [AS("a00", 560, 820, 500, 63.7, ent="gira", vel=-300, z=M), TX("1988", 170, 1380, 560, W("1988", 64.1), rot=-5, ent="carimbo")],
  socos=[(W("1988", 64.1), 0.06)])
# "um psiquiatra inglês chamado Anthony Storr" — a foto dele
S(65.25, IMG("storr-foto", 660, 760, (820, 520, -1.6, (0, 1100))), [Fd("a04", 420, 1640, 300)],
  [TX("Anthony Storr", 100, 1450, 820, W("anthony", 66.4), rot=-5)])
# "escreveu um livro inteiro questionando isso." — a capa; a interrogação de jornal
S(67.95, None, [Fd("b09", 400, 1660, 300, flutua=(8, 0.7))],
  [LIVRO(620, 880, 520, 68.0, ent="pulo", rot=-3, z=M),
   AS("c11", 330, 1450, 700, W("questionando", 69.2), ent="queda", balanca=(10, 1.2))])
# "O nome é Solidão." — SOLIDÃO em letras por cima da capa
S(70.15, None, [Fd("a01", 420, 1640, 300, vel=20)],
  [LIVRO(520, 560, 480, 70.15, ent=None, rot=-5, z=M)] + PAL("SOLIDA~O", 1200, 760, W("solidao", 70.6), alt=150, passo=0.05, ent="carimbo"),
  socos=[(W("solidao", 70.6), 0.07)])
# "E o subtítulo é o que me pegou: um retorno a si mesmo." — zoom no subtítulo, a lupa passa (voz com eco)
S(73.55, IMG("storr-capa", 560, 860, (760, 520, -1.2, "pulo")), [],
  [AS("a11", 400, 0, 0, 74.4, ent=None, caminho=[(74.4, 1900, 820), (75.6, 1200, 760)], rot=-12),
   TX("um retorno a si mesmo", 92, 960, 900, W("retorno", 76.2), rot=-3)], zoom=(1.0, 1.1))
# "O Storr passou a vida atendendo gente," — a foto dele; a mão anota
S(78.55, IMG("storr-foto", 760, 760, (1000, 520, 1.6, (1500, 0)), (0, 0.0, 1, 0.8)),
  [Fd("b13", 520, 330, 820)],
  [AS("a09", 520, 420, 600, W("atendendo", 79.4), ent="sobe", caminho=[(79.6, 420, 600), (80.2, 360, 630), (80.8, 450, 590)])])
# "...a psicologia tratou os relacionamentos como a única fonte de saúde e de felicidade," — as mãos de Michelangelo
S(81.75, IMG("maos-tocando", 1100, 620, (940, 500, -1.4, (0, -1100))),
  [Pc("a08", 280, 1650, 280, de=W("felicidade", 87.9), entrada="queda")],
  [TX("relacionamentos", 84, 960, 900, W("relacionamentos", 84.7), rot=-3), TX("a ÚNICA fonte?", 84, 420, 230, W("unica", 86.0), rot=-6)])
# "e que isso engana as pessoas," — o joinha pra baixo
S(88.95, IMG("maos-tocando", 1180, 660, (960, 500, 1.2, None), (0.3, 0.2, 0.75, 0.8)),
  [Pc("c01", 320, 1640, 760, de=W("engana", 89.5), entrada="carimbo")],
  [TX("engana.", 100, 360, 860, W("engana", 89.5), rot=-6)], zoom=ZI)
# "porque muitas das experiências mais profundas... acontecem por dentro," — o crânio, o cérebro pulsa dentro
S(90.75, None, [Fd("a04", 480, 1620, 300)],
  [AS("b12", 640, 860, 560, 90.8, ent="sobe", z=M),
   AS("c06", 300, 800, 430, W("dentro", 94.7) - 0.3, ent="pop", pulsa=(0.05, 2.0)),
   TX("por dentro", 100, 1450, 860, W("dentro", 94.7), rot=-5)])
# "Sozinho." — o Sam sozinho na montanha
S(95.25, VID("saida-caverna", 848.0, pos=(940, 480, -1.4, "pulo")), [], [], zoom=(1.0, 1.1))
# "E aí ele lembra de um monte de gente que mudou o mundo" — o homem vitruviano gira
S(96.45, IMG("homem-vitruviano", 720, 760, (900, 520, 1.4, (0, 1100))),
  [Pc("a01", 360, 1600, 300, de=W("mundo", 98.7), entrada="gira", vel=40)],
  [TX("mudaram o mundo", 90, 1450, 860, W("mudou", 98.2), rot=-5)])
# "Descartes nunca casou," / "Newton nunca casou," / "o Kant nunca casou" — 3 retratos, 3 carimbos
S(101.6, IMG("descartes", 700, 800, (820, 520, -1.6, (-1500, 0))), [],
  [TX("nunca casou", 110, 1460, 760, W("nunca", 102.2), rot=-8, ent="carimbo")], socos=[(W("casou", 102.3), 0.05)])
S(103.3, IMG("newton", 700, 800, (1060, 520, 1.6, (1500, 0))), [],
  [TX("nunca casou", 110, 460, 760, W("nunca", 103.7), rot=6, ent="carimbo")], socos=[(W("casou", 104.0), 0.05)])
S(104.8, IMG("kant", 700, 800, (860, 520, -1.4, (0, -1100))), [],
  [TX("nunca casou", 110, 1460, 300, W("nunca", 105.1), rot=-6, ent="carimbo")], socos=[(W("casou", 105.3), 0.05)])
# "e saía pra caminhar todo dia no mesmo horário." — o Kant passeando; o despertador balança
S(105.75, IMG("kant-passeio", 760, 820, (1000, 520, 1.6, "pulo")),
  [Pc("a13", 320, 400, 300, de=W("horario", 107.3), entrada="queda", balanca=(12, 1.6))],
  [TX("todo dia, 15h30", 84, 420, 860, W("horario", 107.3), rot=-5)])
# "tão certinho que os vizinhos acertavam o relógio por ele," — os vizinhos de binóculo; o relógio gira
S(110.25, None, [Fd("b13", 520, 1640, 820)],
  [RC("kant-passeio", 520, 1240, 560, 110.3, ent="pop", rot=4, z=M),
   AS("b14", 440, 420, 600, W("vizinhos", 111.7), ent="sobe"),
   AS("a00", 380, 620, 260, W("relogio", 112.8), ent="carimbo", chaves=GIRA(W("relogio", 112.8), [(0, 0), (0.6, 360)]))])
# "o homem era um relógio de carne e osso." — o relógio no lugar da cabeça do Kant
S(113.95, IMG("kant", 760, 800, (960, 520, -1.2, "pulo")), [],
  [AS("a13", 300, 960, 360, W("relogio", 114.5), ent="carimbo", balanca=(5, 1.4)),
   TX("relógio de\ncarne e osso", 84, 1500, 820, W("relogio", 114.5) + 0.2, rot=-5)], socos=[(W("relogio", 114.5), 0.06)])
# "E mudou a filosofia." — estrelas
S(115.4, IMG("kant", 1000, 640, (960, 500, 1.2, None), (0.0, 0.05, 1.0, 0.55)),
  [Pc("b05", 260, 1640, 280, de=116.0, vel=80), Pc("b08", 180, 300, 820, de=116.1, vel=-80)], [], zoom=ZI)
# "Agora, calma." — a mão de calma (o cartaz Don't Panic)
S(116.75, None, [Fd("b09", 420, 1640, 820)],
  [AS("dont-panic", 520, 900, 520, 116.8, ent="carimbo", z=M, balanca=(4, 1.0))], cam=(0, 6, 0, -6))
# "O Storr não tá dizendo pra você largar todo mundo e ir morar numa cabana." — a cabana; joinha pra baixo
S(118.8, IMG("walden-cabana", 760, 800, (880, 520, -1.6, (0, 1100))),
  [Pc("c01", 300, 1600, 760, de=W("cabana", 121.5), entrada="carimbo")],
  [LIVRO(300, 1560, 300, 118.9, ent="queda", rot=8), TX("cabana? não.", 90, 360, 860, W("cabana", 121.5), rot=-6)])
# "Ele não é contra as pessoas." — a festa de novo, pequena, e o livro
S(122.65, IMG("festa-multidao", 980, 640, (960, 500, 1.4, "pulo")), [Fd("a01", 380, 1660, 300, flutua=(8, 0.6))], [], zoom=ZI)
# "Ele só diz que ficar sozinho não é defeito. É uma capacidade." — "defeito" riscado pelo raio; CAPACIDADE em letras
S(124.4, None, [Fd("b13", 520, 1640, 820), Fd("a00", 420, 300, 260, vel=20)],
  [TX("defeito", 120, 960, 330, W("defeito", 125.9), rot=-4, ent="carimbo"),
   AS("b04", 380, 960, 330, W("defeito", 125.9) + 0.35, ent="carimbo", rot=-60)]
  + PAL("CAPACIDADE", 960, 700, W("capacidade", 127.1), alt=130, passo=0.04, ent="carimbo"),
  socos=[(W("capacidade", 127.1), 0.07)])
# "Só que tem gente que escuta isso e entende outra coisa." — a orelha com os raios; a interrogação
S(128.25, None, [Fd("a04", 440, 1640, 820)],
  [AS("b11", 660, 840, 520, 128.3, ent="sobe", z=M, pulsa=(0.04, 2.5)),
   AS("c11", 300, 1460, 360, W("outra", 129.8), ent="queda", balanca=(10, 1.2))])
# "Entende que o certo é não precisar de ninguém. Ser independente. Se bastar." — o rei sozinho no alto; os outros caem
S(130.65, None, [Fd("b00", 820, 960, 540, vel=8)],
  [AS("a07", 420, 960, 520, 130.7, ent="queda", z=M),
   AS("a07", 220, 560, 640, 130.7, ent="pop", caminho=[(W("ninguem", 132.5), 560, 640), (W("ninguem", 132.5) + 0.4, 520, 1400)]),
   AS("a07", 220, 1360, 640, 130.7, ent="pop", caminho=[(W("ninguem", 132.5) + 0.1, 1360, 640), (W("ninguem", 132.5) + 0.5, 1400, 1400)]),
   TX("independente.", 90, 960, 880, W("independente", 133.2), rot=-4), TX("se bastar.", 90, 1500, 300, W("bastar", 134.3), rot=6)])
# "Guarda essa ideia." — o BILHETE é fixado com a tachinha (volta no fim do cap. II e no cap. III)
S(136.75, None, [Fd("b13", 520, 1620, 820)],
  [Camada(NOTA, 900, 540, rot=-4, de=V(136.8), amp=4, gira=0.5, sombra=18, seed=_s(), entrada="queda", z=M),
   AS("b02", 200, 900, 330, 137.2, ent="carimbo")], socos=[(137.2, 0.05)])
# "Ela tem uma pegadinha. E eu caí direitinho nela." — o desenho da pessoa caindo
S(137.85, None, [],
  [Camada(NOTA, 520, 420, rot=-6, de=V(137.85), amp=4, gira=0.5, sombra=18, seed=_s(), z=0.15), AS("c05", 600, 1200, 560, W("direitinho", 139.3) - 0.4, ent="queda", z=M),
   TX("pegadinha", 100, 520, 860, W("pegadinha", 138.3), rot=-6, ent="carimbo")], tremor=[(W("direitinho", 139.3), 0.3, 6)])
# "Porque se ficar sozinho é uma capacidade, por que pra uns ela é descanso," — o Sam andando em paz
S(140.75, VID("chuva-b", 330.0, pos=(940, 500, -1.4, (0, 1100))), [],
  [TX("descanso", 100, 1500, 880, W("descanso", 144.1), rot=-5)])
# "e pra outros, é castigo?" — a cela
S(W("outros", 144.8) - 0.2, IMG("cela", 760, 780, (960, 520, 1.6, "pulo")), [],
  [TX("castigo?", 110, 1500, 860, W("castigo", 145.3), rot=-6, ent="carimbo")], zoom=ZI)

# =====================================================================================================
# CAPÍTULO II — COMO SE APRENDE A FICAR SOZINHO   (o bebê da colher; humor pouco)
# =====================================================================================================
# "Pra responder isso, o Storr vai buscar um pediatra," — o livro chama o Winnicott
S(149.4, IMG("winnicott", 700, 800, (1060, 520, 1.6, (1500, 0))),
  [], [LIVRO(380, 420, 560, 149.5, ent="queda", rot=-8), TX("pediatra", 90, 1560, 900, W("pediatra", 151.6), rot=-5)])
# "o Donald Winnicott," — o nome
S(153.25, IMG("winnicott", 860, 760, (960, 500, -1.2, None), (0.1, 0.05, 0.9, 0.75)), [Fd("a08", 360, 1660, 300, pisca=1.2)],
  [TX("Donald Winnicott", 96, 1400, 900, W("donald", 153.6), rot=-4)], zoom=ZI)
# "que escreveu um artigo com um nome que parece pergunta de prova:" — a folha da prova
S(157.25, None, [Fd("b13", 520, 1640, 820)],
  [Camada(prova(), 900, 540, rot=-3, de=V(157.3), amp=4, gira=0.5, sombra=18, seed=_s(), entrada=(0, 1100), z=M),
   AS("a09", 520, 1350, 760, W("prova", 160.4), ent="sobe", caminho=[(161.6, 1350, 760), (162.3, 1260, 780), (162.9, 1360, 750)]),
   TX("A capacidade de\nficar sozinho (1958)", 64, 880, 600, W("capacidade", 161.7), rot=-3)])
# "E ele começa com uma coisa que parece contradição." — as duas setas, uma pra cada lado
S(163.75, None, [Fd("b09", 400, 1640, 300)],
  [AS("c12", 440, 700, 560, 163.8, ent="carimbo", rot=90, caminho=VAIVEM(164.2, 166.4, 700, 560, -30, 0)),
   AS("c13", 440, 1220, 560, 164.0, ent="carimbo", rot=-90, caminho=VAIVEM(164.3, 166.4, 1220, 560, 30, 0)),
   TX("contradição", 100, 960, 880, W("contra", 165.8), rot=-4)])
# "A base de saber ficar sozinho é ter ficado sozinho com alguém por perto." — o casal lendo em silêncio, lado a lado
S(166.95, IMG("silencio-junto", 820, 760, (900, 520, -1.4, (0, 1100))), [Fd("a03", 380, 1660, 300)],
  [TX("com alguém\npor perto", 90, 1500, 820, W("alguem", 169.9), rot=-5)], zoom=ZI)
# "Pensa num bebê no chão da sala, brincando com uma colher." — o BB acena; a colher chega girando
S(171.85, VID("bb-fofo", 41.0, pos=(860, 500, -1.4, "pulo")), [],
  [RC("bebe-colher", 520, 1480, 760, W("colher", 174.4) - 0.3, caixa=(0.28, 0.55, 0.72, 0.85), ent="gira", rot=-20,
      chaves=GIRA(W("colher", 174.4), [(0, 0), (0.5, 20), (1.0, -10), (1.5, 15)]))])
# "Ele tá sozinho. Não chama ninguém. Não precisa de nada." — o pote sozinho na grama
S(175.15, VID("bb-fofo", 16.0, pos=(1000, 500, 1.4, (1500, 0))), [],
  [RC("bebe-colher", 420, 400, 800, 175.2, caixa=(0.28, 0.55, 0.72, 0.85), ent=None, rot=-14),
   TX("sozinho.", 96, 400, 260, W("sozinho", 175.4), rot=-6)])
# "Mas a mãe tá ali no sofá. Lendo, vendo novela, sei lá." — O SOFÁ (a moça lendo do Hammershøi); a TV chia
S(178.05, IMG("mae-lendo", 760, 820, (900, 520, -1.4, (0, -1100))),
  [Pc("b09", 260, 1640, 820, de=W("sei", 180.9), entrada="queda", balanca=(10, 1.4))],
  [AS("c12", 320, 1440, 400, W("sofa", 178.8), ent="carimbo", rot=200),
   TX("lendo", 72, 1560, 300, W("lendo", 179.5), rot=6), AS("b10", 300, 1580, 600, W("novela", 180.3), ent="carimbo")])
# "Ela não tá brincando com ele. Ela só tá... ali." — os dois na mesma cena: o pote de um lado, ela do outro
S(181.85, None, [],
  [RC("mae-lendo", 560, 1320, 520, 181.9, ent=None, rot=3, z=M),
   com_video(os.path.join(P, "gameplay", "bb-fofo.mp4"), 16.0, 5.5, 640, 520, 600, 560, -2.0, V(181.9), _s(), GQ,
             vcrop=CROP["bb-fofo"], entrada=(-1500, 0)),
   AS("c13", 300, 1320, 900, W("ali", 186.0) - 0.2, ent="carimbo", rot=-20),
   TX("só... ali.", 90, 1640, 230, W("ali", 186.0), rot=6)])
# "E é justamente por isso que ele consegue esquecer dela e mergulhar na colher." — o BB boiando, de perto
S(188.15, VID("bb-fofo", 30.5, pos=(960, 500, 1.2, "pulo")), [],
  [RC("bebe-colher", 380, 1560, 820, W("colher", 191.7) - 0.2, caixa=(0.28, 0.55, 0.72, 0.85), ent="queda", rot=12)], zoom=(1.0, 1.12))
# "Agora, se a mãe sai da sala?" — ELA SAI: desliza pra fora; fica a sala vazia
S(192.45, IMG("sala-vazia", 940, 680, (860, 520, -1.4, None)), [],
  [RC("mae-lendo", 520, 1360, 520, 192.5, ent="pop", rot=3,
      caminho=[(W("sala", 194.0) - 0.2, 1360, 520), (W("sala", 194.0) + 0.3, 2400, 520)])])
# "Acabou a colher." — a colher cai
S(194.65, None, [Fd("b13", 520, 1640, 820)],
  [RC("bebe-colher", 640, 960, 460, 194.7, caixa=(0.28, 0.55, 0.72, 0.85), ent="pop", rot=-10,
      caminho=[(195.0, 960, 460), (195.5, 980, 1500)], chaves=GIRA(195.0, [(0, 0), (0.5, 160)])),
   AS("b04", 360, 1450, 360, 195.1, ent="carimbo")])
# "Começa o berreiro." — o BB chorando no pote; o megafone; treme
S(195.55, VID("bb-acalmar", 40.0, pos=(900, 500, -1.6, (0, 1100))), [],
  [AS("a12", 420, 1550, 360, 195.6, ent="carimbo", balanca=(10, 3.0))], tremor=[(195.7, 0.5, 8)], socos=[(195.7, 0.06)])
# "Ninguém nasce sabendo ficar sozinho." — o recém-nascido
S(196.65, IMG("bebe-chorando", 940, 680, (980, 500, 1.6, (1500, 0))), [], [], zoom=ZI)
# "A gente aprende. E aprende acompanhado." — mãe e filho (Cassatt)
S(198.35, IMG("cassatt-mae", 720, 820, (900, 520, -1.4, (0, -1100))), [Fd("b05", 300, 1640, 300, vel=20)],
  [TX("acompanhado", 96, 1460, 860, W("acompanhado", 199.9), rot=-5)])
# TESE: "Ninguém aprende a ficar sozinho... sozinho." — a frase escrita, e SOZINHO cai em letras (silêncio depois)
S(201.65, None, [],
  [EXP(560, 960, 640, W("sozinho", 203.3) - 0.05, vel=20),
   TX("Ninguém aprende a ficar sozinho...", 92, 960, 330, 201.7, rot=-2)]
  + PAL("SOZINHO", 960, 650, W("sozinho", 203.3), alt=190, passo=0.07, ent="carimbo"),
  socos=[(W("sozinho", 203.3), 0.06)], cam=(0, 0, 0, 0))
# "Então talvez a pergunta não seja por que tem gente que aguenta e gente que não." — ampulheta + interrogação
S(205.95, None, [Fd("a13", 440, 1640, 300, vel=-60)],
  [AS("c03", 460, 760, 520, 206.0, ent="pop", z=M), AS("c11", 360, 1240, 520, W("pergunta", 206.9), ent="queda", balanca=(8, 1.2))])
# "É: quem teve alguém no sofá enquanto aprendia?" — o sofá de novo, e o BB pequenininho
S(210.15, IMG("mae-lendo", 700, 780, (1100, 520, 1.6, (1500, 0))), [],
  [TX("quem teve alguém\nno sofá?", 84, 450, 330, W("sofa", 211.9), rot=-5)])
# "Peraí. Então pra ficar sozinho eu preciso de alguém? Isso não faz o menor sentido." (voz de quem assiste)
S(215.0, None, [Fd("b09", 420, 1640, 820, flutua=(10, 0.8))],
  [VIVO(TV, 820, 560, 215.0, {"q": ciclo(215.0, 219.8, 5, 0.1)}, ent="sobe", z=M),
   TX("(quem assiste)", 80, 1450, 300, 215.2, rot=6),
   AS("b07", 300, 1450, 700, W("sentido", 219.2), ent="carimbo", balanca=(12, 2.0))], tremor=[(W("sentido", 219.2), 0.3, 6)])
# "Eu sei, calma, calma, senta aí," — as cadeiras deslizam pra baixo da TV
S(220.15, None, [Fd("b13", 520, 1640, 820)],
  [VIVO(TV, 820, 500, 220.15, {"q": ciclo(220.2, 222.4, 5, 0.25)}, ent=None, z=M),
   RC("cadeiras", 560, 820, 900, W("senta", 221.9) - 0.1, ent=None, rot=2,
      caminho=[(W("senta", 221.9) - 0.1, 2400, 900), (W("senta", 221.9) + 0.25, 820, 900)]),
   TX("senta aí.", 96, 1500, 300, W("senta", 221.9), rot=6)])
# "Eu pensei a mesma coisa. Até lembrar que tem vídeo no YouTube" — o computador; dentro da tela, a moça estudando
S(225.25, None, [Fd("a04", 420, 1640, 300)],
  [AS("b10", 760, 900, 560, 225.3, ent="sobe", z=M),
   RC("estudante", 250, 840, 390, W("video", 227.4), ent="pop", rot=0, z=M)])
# "com milhões de visualizações, de uma pessoa estudando." — estrelas, views
S(229.95, None, [Fd("b13", 520, 330, 820)],
  [AS("b10", 760, 900, 560, 230.0, ent=None, z=M), RC("estudante", 250, 840, 390, 230.0, ent=None, rot=0, z=M),
   TX("milhões de views", 90, 1450, 260, W("milhoes", 230.3), rot=6, ent="carimbo"),
   AS("b05", 200, 1550, 520, W("milhoes", 230.3) + 0.2, ent="carimbo", vel=60)])
# "Só isso. Em silêncio. Por três horas." — a moça lendo (zoom lento); o relógio
S(232.85, IMG("estudante", 820, 820, (900, 520, -1.2, "pulo"), (0.1, 0.25, 0.9, 0.95)),
  [Pc("a00", 320, 1600, 300, de=W("tres", 234.4), entrada="pop", vel=-120)],
  [TX("3 horas.", 110, 1500, 860, W("tres", 234.4), rot=-5, ent="carimbo")], zoom=(1.0, 1.1))
# "E milhões de pessoas abrem esse vídeo pra conseguir estudar. Sozinhas." — os computadores se multiplicam
S(236.15, None, [Fd("b13", 520, 1640, 820)],
  [AS("b10", 360, 380 + 290 * k, 300 + 420 * (k % 2), 236.3 + 0.18 * k, ent="carimbo") for k in range(5)]
  + [TX("sozinhas.", 96, 1500, 960, W("sozinhas", 239.1), rot=-4)])
# "Do lado de um desconhecido que nem sabe que elas existem." — o olho dela não vê: a moça lendo, de costas
S(240.45, IMG("estudante", 700, 800, (1080, 520, 1.6, (1500, 0))), [Fd("a04", 400, 380, 300)],
  [TX("(nem sabe)", 90, 420, 860, W("sabe", 242.2), rot=-6)])
# "É o bebê com a colher. Só que com apostila." — o BB de volta + a colher + a mão escrevendo
S(243.75, VID("bb-fofo", 43.0, w=900, h=640, pos=(760, 500, -1.6, "pulo")), [],
  [RC("bebe-colher", 380, 1480, 300, 244.6, caixa=(0.28, 0.55, 0.72, 0.85), ent="carimbo", rot=-20),
   AS("a09", 420, 1500, 780, W("postila", 246.2) - 0.1, ent="sobe"),
   TX("+ apostila", 90, 1520, 560, W("postila", 246.2), rot=-5, ent="carimbo")])
# "E olha, agora editando esse vídeo eu percebi uma coisa." — a lupa no computador
S(247.15, None, [Fd("b09", 400, 1640, 300)],
  [AS("b10", 700, 860, 560, 247.2, ent="pulo", z=M), AS("a11", 420, 1380, 700, W("percebi", 249.0), ent="queda", rot=-14)])
# "São duas da manhã, eu tô há seis horas sozinho no quarto," — a janela de noite; o relógio
S(249.75, IMG("noite-janela", 980, 660, (940, 500, -1.4, (0, -1100))),
  [Pc("a13", 300, 1640, 300, de=W("duas", 250.1), entrada="queda", balanca=(9, 1.4))],
  [TX("2h da manhã", 90, 420, 230, W("duas", 250.1), rot=-6, ent="carimbo"), TX("6h sozinho", 90, 1450, 900, W("seis", 251.6), rot=-4)])
# "fazendo um vídeo sobre ficar sozinho..." — o computador com o arquivo
S(252.95, None, [Fd("a01", 420, 1640, 820)],
  [AS("b10", 720, 900, 540, 253.0, ent="pop", z=M), TX("solitude_v1.mp4", 76, 900, 900, W("sobre", 253.6), rot=-3)])
# "com uma pessoa estudando aberta na outra aba." — a moça na tela, de novo (a seta aponta)
S(255.45, None, [Fd("b13", 520, 330, 820)],
  [AS("b10", 720, 900, 540, 255.5, ent=None, z=M), RC("estudante", 230, 843, 379, 255.9, ent="carimbo", rot=0, z=M),
   AS("c12", 300, 1360, 300, W("aba", 259.0) - 0.4, ent="carimbo", rot=210), TX("outra aba", 84, 1500, 860, W("aba", 259.0), rot=-5)])
# "Faz um teste comigo." — o dedo aponta pra quem assiste
S(260.95, None, [Fd("a04", 420, 1640, 300)], [AS("c00", 560, 900, 540, 261.0, ent="carimbo", z=M)], socos=[(261.2, 0.06)])
# "Pensa na última vez que você ficou em silêncio do lado de alguém. Sem precisar puxar assunto. E foi bom." (+ o silêncio)
S(262.05, IMG("silencio-junto", 860, 780, (940, 520, -1.2, (0, 1100))), [],
  [AS("a03", 300, 1600, 280, W("assunto", 265.9), ent="pop", balanca=(4, 1.0))], zoom=(1.0, 1.12))
# "Achou?" — a interrogação
S(270.25, None, [Fd("a08", 400, 1640, 300, pisca=1.2)], [AS("b09", 440, 960, 520, 270.3, ent="carimbo", z=M, balanca=(6, 1.2))])
# "Isso que você lembrou é o contrário da solidão." — o Sam e a Fragile olhando a montanha
S(271.35, VID("dupla", 600.0, pos=(940, 500, -1.4, "pulo")), [],
  [TX("o contrário\nda solidão", 84, 1560, 860, W("contrario", 272.6), rot=-5)], zoom=ZI)
# "Só que o Storr vai mais longe." — o livro, a seta pra frente
S(273.95, None, [Fd("b13", 520, 1640, 820)],
  [LIVRO(520, 760, 520, 274.0, ent="pulo", rot=-4, z=M),
   AS("c12", 380, 1380, 560, W("longe", 275.8) - 0.3, ent=None, rot=90, caminho=[(275.6, 1300, 560), (276.1, 1600, 560)])])
# "Porque tem gente que não escolhe ficar sozinha." — a porta fechada
S(279.65, IMG("porta-fechada", 720, 800, (940, 520, 1.4, (0, 1100))), [], [], zoom=ZI)
# "Ele conta de uma médica chamada Edith Bone." — o livro dela
S(287.75, None, [Fd("a04", 420, 1640, 300)],
  [Camada(ED, 820, 540, rot=-4, de=V(287.8), amp=4, gira=0.6, sombra=18, seed=_s(), entrada="pulo", z=M),
   TX("Edith Bone", 110, 1460, 760, W("edith", 289.4), rot=-5)])
# "Em 1949, ela foi presa na Hungria" — Budapeste
S(290.95, IMG("budapeste", 820, 760, (960, 520, -1.4, (1500, 0))), [],
  [TX("1949", 150, 400, 300, W("em", 291.0), rot=-8, ent="carimbo"), TX("Hungria", 90, 1500, 880, W("hungria", 293.6), rot=-5)],
  socos=[(W("em", 291.0) + 0.15, 0.05)])
# "e passou sete anos numa solitária." — a cela (a porta bate depois)
S(294.05, IMG("cela", 720, 800, (900, 520, 1.6, "pulo")), [], [TX("solitária", 96, 1460, 860, W("solitaria", 295.5), rot=-5)], zoom=ZI)
# "Sete anos." — os risquinhos na parede, um por um
S(296.65, None, [Fd("b13", 520, 1640, 820)],
  [TX("|", 200, 600 + 110 * k, 520, 296.7 + 0.12 * k, rot=random.Random(k).uniform(-6, 6), ent="carimbo") for k in range(7)]
  + [TX("7 anos", 110, 960, 880, 297.1, rot=-4)], cam=(0, 0, 0, 0))
# "Sem livro, sem papel, sem ninguém." — os três somem: o livro, o papel, o balão
S(299.55, IMG("cela", 1000, 660, (960, 500, -1.2, None), (0.1, 0.2, 0.9, 0.8)), [],
  [Camada(ED, 400, 300, rot=-8, de=V(299.6), amp=3, gira=0.4, sombra=14, seed=_s(), entrada="pop", z=1.3, saida="pop"),
   AS("b04", 300, 400, 300, W("livros", 300.1) + 0.1, ent="carimbo"),
   AS("a05", 300, 960, 900, W("papel", 300.6), ent="pop"), AS("b04", 300, 960, 900, W("papel", 300.6) + 0.15, ent="carimbo"),
   AS("a02", 300, 1520, 300, W("ninguem", 301.1), ent="pop"), AS("b04", 300, 1520, 300, W("ninguem", 301.1) + 0.15, ent="carimbo")])
# "E sabe o que ela fez?" — interrogação
S(302.15, None, [Fd("a01", 420, 1640, 820)], [AS("c11", 460, 900, 520, 302.2, ent="carimbo", z=M, balanca=(8, 1.0))])
# "Recitava de cabeça os poemas que sabia, em várias línguas." — a boca com os raios; os versos voam
S(303.55, None, [Fd("b13", 520, 1640, 820)],
  [AS("b11", 620, 820, 540, 303.6, ent="sobe", z=M, pulsa=(0.04, 2.5)),
   TX("Ich weiß nicht...", 60, 1480, 260, W("problemas", 304.8) + 0.1, rot=6), TX("Sous le pont...", 60, 1500, 420, W("linguas", 306.0) - 0.4, rot=-4),
   TX("O, my Luve...", 60, 1460, 580, W("linguas", 306.0), rot=5), TX("Minha terra...", 60, 1500, 740, W("linguas", 306.0) + 0.3, rot=-6)])
# "Fazia conta com um ábaco de bolinha de pão." — o ábaco; o pão
S(306.65, IMG("abaco", 640, 760, (820, 520, -1.6, (0, 1100)), (0.1, 0.3, 0.75, 0.75)), [],
  [RC("pao", 420, 1460, 700, W("pao", 310.0) - 0.3, ent="queda", forma="oval"), TX("1 + 1", 110, 1460, 300, W("conta", 307.2), rot=-6)])
# "E andava, na imaginação, pelas ruas das cidades que conhecia." — o Sam andando; o mapa antigo atrás
S(311.2, VID("chuva-a", 60.0, pos=(1080, 520, 1.4, (1500, 0))), [],
  [RC("mapa-antigo", 560, 380, 520, 311.3, ent="sobe", rot=-8, z=0.15),
   TX("(na imaginação)", 80, 1080, 960, W("imaginacao", 312.3), rot=-3)])
# "Ela tava sozinha. Mas não tava vazia." — a cela; VAZIA em letras, riscada pelo raio
S(315.15, IMG("cela", 700, 760, (560, 500, -1.6, "pulo")), [],
  PAL("VAZIA", 1360, 520, W("vazia", 316.8), alt=150, passo=0.05, ent="carimbo")
  + [AS("b04", 520, 1360, 520, W("vazia", 316.8) + 0.4, ent="carimbo", rot=-70)],
  socos=[(W("vazia", 316.8) + 0.4, 0.06)])
# "Aquela cela tava cheia de gente que ela carregava por dentro." — a cela enche de gente recortada
S(317.85, IMG("cela", 1000, 680, (960, 500, -1.2, None), (0.1, 0.15, 0.9, 0.85)), [],
  [AS(n, 300, x, y, 318.6 + 0.2 * k, ent="pop") for k, (n, x, y) in enumerate(
      [("c07", 560, 640), ("a04", 1340, 420), ("a07", 760, 420), ("b14", 1260, 700), ("d01", 960, 560)])]
  + [AS("c06", 220, 960, 300, W("dentro", 320.2), ent="carimbo", pulsa=(0.05, 2.0))])
# "Os poetas. As cidades. Quem tinha ensinado tudo aquilo pra ela." — a mão escrevendo, Budapeste, mãe e filho
S(321.05, None, [Fd("b13", 520, 1640, 820)],
  [AS("a09", 520, 460, 400, 321.1, ent="carimbo", rot=-6),
   RC("budapeste", 480, 1000, 600, W("cidades", 321.8), ent="carimbo", rot=4),
   RC("cassatt-mae", 440, 1500, 420, W("ensinado", 322.8), ent="carimbo", rot=-5)])
# "O bebê com a colher... só que a colher era tudo que ela tinha guardado." — a colher no meio, o que ela guardou em volta
S(324.15, VID("bb-fofo", 43.5, w=760, h=560, pos=(560, 500, -1.6, "pulo")), [],
  [RC("bebe-colher", 620, 1340, 520, W("colher", 326.1) - 0.2, caixa=(0.28, 0.55, 0.72, 0.85), ent="carimbo", rot=-16, pulsa=(0.03, 1.5)),
   AS("a09", 260, 1100, 240, W("tudo", 327.0), ent="pop"), AS("b06", 240, 1600, 240, W("tudo", 327.0) + 0.15, ent="pop", vel=40),
   RC("mapa-antigo", 260, 1640, 820, W("guardado", 327.6), ent="pop", rot=6)])
# "E aqui esse vídeo deixa de ser sobre um livro." — o livro vai embora
S(330.85, None, [Fd("b09", 400, 1640, 300)],
  [LIVRO(560, 900, 520, 330.9, ent="pop", rot=-4, z=M, caminho=[(332.0, 900, 520), (332.6, 900, 1500)])])
# "Porque foi lendo isso que eu entendi a minha pegadinha." — O BILHETE volta (a tachinha)
S(333.45, None, [Fd("b13", 520, 1640, 820)],
  [Camada(NOTA, 900, 520, rot=-4, de=V(333.5), amp=4, gira=0.5, sombra=18, seed=_s(), entrada="queda", z=M),
   AS("b02", 200, 900, 300, 333.9, ent="carimbo"), TX("a pegadinha", 90, 1450, 900, W("pegadinha", 335.1), rot=-5)])

# =====================================================================================================
# CAPÍTULO III — QUANDO EU ME ISOLEI   (relato pessoal; momento pesado no meio; humor só volta com o amigo)
# =====================================================================================================
# "Uns anos atrás, eu me mudei de cidade" — o Sam carregando as coisas; as caixas
S(342.15, VID("chuva-caverna", 326.0, pos=(1000, 500, 1.4, (0, 1100))),
  [], [RC("caixas", 420, 380, 760, W("mudei", 343.3), ent="queda", rot=-6)])
# "e achei que tava vivendo a tal da solitude." — a montanha, linda
S(344.4, VID("saida-caverna", 851.0, pos=(940, 480, -1.4, "pulo")), [Fd("b05", 300, 1640, 280, vel=30)],
  [TX("solitude!", 96, 1500, 880, W("solitude", 346.0), rot=-5, ent="carimbo")], zoom=ZI)
# "Casa minha, silêncio, ninguém pra dar satisfação." — a sala; a lista à mão
S(347.05, IMG("sala-vazia", 860, 700, (820, 520, -1.4, (0, -1100))), [],
  [TX("casa minha", 72, 1520, 300, W("casa", 347.1), rot=-3), TX("silêncio", 72, 1520, 440, W("silencio", 348.0), rot=-3),
   TX("ninguém", 72, 1520, 580, W("ninguem", 348.6), rot=-3)])
# "Eu falava pra todo mundo que tava ótimo." — joinha pra cima
S(349.95, None, [Fd("a01", 420, 1640, 820)],
  [AS("c01", 520, 900, 520, 350.0, ent="carimbo", rot=180, z=M), TX("ótimo!", 110, 1450, 300, W("otimo", 351.0), rot=6)])
# "E tava. No começo." — o joinha murcha devagar
S(351.85, None, [],
  [AS("c01", 520, 900, 520, 351.85, ent=None, rot=180, z=M, chaves=GIRA(352.4, [(0, 0), (0.6, 90)])),
   TX("no começo.", 96, 1450, 860, W("comeco", 352.6), rot=-4)])
# "Aí as mensagens foram ficando sem resposta." — o balão perde os pontos
S(353.55, None, [Fd("b13", 520, 1640, 820)],
  [VIVO(BALAO, 900, 520, 353.6, {"q": [(353.6, 0), (354.4, 1), (354.8, 2), (355.0, 3)]}, ent="carimbo", z=M),
   TX("sem resposta", 90, 1450, 880, W("resposta", 355.0), rot=-4)])
# "Primeiro porque eu tava ocupado. Depois porque eu não sabia mais o que responder." — o computador; a interrogação
S(355.95, None, [Fd("a00", 420, 1640, 820, vel=-30)],
  [AS("b10", 640, 820, 540, 356.0, ent="pop", z=M), TX("ocupado", 90, 1450, 280, W("ocupado", 356.6), rot=6),
   AS("c11", 320, 1450, 720, W("depois", 357.1), ent="queda", balanca=(8, 1.0))])
# ===== MOMENTO PESADO (fundo preto, P&B, sem piada, menos peças, mais lento) =====
# "Um dia, no mercado, a moça do caixa perguntou:"
S(359.25, IMG("fila-mercado", 1040, 680, (960, 520, -1.2, (0, 1100))), [], [], zoom=(1.0, 1.06))
# "Crédito ou débito?" "Débito."
S(361.95, None, [], [RC("maquininha", 520, 960, 520, 362.0, ent="pop", rot=-4, z=M),
                     TX("crédito ou débito?", 76, 960, 900, 362.0, rot=-2)], zoom=(1.0, 1.05))
# "E percebi que era a primeira palavra que eu falava em voz alta em três semanas."
S(363.75, None, [], [AS("a02", 380, 960, 480, 363.8, ent="pop", z=M), TX("3 semanas.", 110, 960, 860, W("semanas", 366.6), rot=-3)],
  zoom=(1.0, 1.06), cam=(0, 0, 0, 0))
# "Naquela noite, em casa, eu falei o meu próprio nome. Só pra ouvir uma voz." — a janela de noite, só
S(369.1, IMG("noite-janela", 1100, 700, (960, 500, -1.0, None)), [], [], zoom=(1.0, 1.1), cam=(0, 0, 0, 0))
# "Aquilo não era solitude." — só a frase
S(373.75, None, [], [TX("aquilo não era solitude.", 100, 960, 540, W("aquilo", 373.8), rot=-2)], cam=(0, 0, 0, 0))
# "Lembra da ideia de que saber ficar sozinho é não precisar de ninguém? Era essa a pegadinha." — o bilhete
S(378.45, None, [], [Camada(NOTA, 960, 520, rot=-3, de=V(378.5), amp=3, gira=0.3, sombra=18, seed=_s(), entrada="pop", z=M)],
  zoom=(1.0, 1.08), cam=(0, 0, 0, 0))
# "Eu achei que tava aprendendo a ficar sozinho. Eu só tava tirando todo mundo da sala." — a sala; as pessoas saem uma a uma
S(383.65, IMG("sala-vazia", 1000, 700, (960, 520, -1.0, None)), [],
  [AS(n, 260, x, 640, 383.7, ent="pop", caminho=[(W("todo", 386.2) + 0.25 * k, x, 640), (W("todo", 386.2) + 0.25 * k + 0.6, x, 1500)])
   for k, (n, x) in enumerate([("c07", 640), ("a07", 900), ("b14", 1160), ("d01", 1400)])], cam=(0, 0, 0, 0))
# "Era o bebê no chão. Sem ninguém no sofá. E sem nada guardado por dentro." — o pote sozinho na incubadora; a colher some
S(387.55, VID("bb-deadman", 30.0, pos=(960, 500, -1.0, None)), [],
  [RC("bebe-colher", 360, 1560, 820, 387.6, caixa=(0.28, 0.55, 0.72, 0.85), ent=None, rot=-12,
      caminho=[(W("nada", 390.3), 1560, 820), (W("nada", 390.3) + 0.8, 1600, 1500)])], zoom=(1.0, 1.08), cam=(0, 0, 0, 0))
# ===== fim do momento pesado: volta o bege =====
# "Mas tinha uma pessoa. Aquele mesmo amigo, do 'jogo de gente triste'." — o amigo volta; TRISTE pequenininho
S(391.9, None, [Fd("b09", 400, 1640, 300, flutua=(8, 0.7))],
  [VIVO(AMIGO, 820, 600, 391.95, {"q": fala_e_pisca([], 391.95, 395.5, seed=11)}, ent="sobe", z=M),
   TX("(jogo de gente triste)", 72, 1460, 880, W("jogo", 393.9), rot=-4)])
# "Ele me mandava um meme por dia." — o celular rola; os memes chegam
S(395.65, None, [],
  [VIVO(CEL, 760, 580, 395.7, {"q": ciclo(395.7, 397.2, 6, 0.15)}, rot=-4, ent="sobe", z=M),
   RC("surprised-pikachu", 320, 1400, 300, W("meme", 396.3), ent="carimbo", rot=8)])
# "Todo santo dia." — os dias da semana, um meme em cada
S(397.15, None, [Fd("b13", 520, 1640, 820)],
  [TX(d, 72, 260 + 300 * k, 230, 397.2 + 0.16 * k, rot=random.Random(k + 3).uniform(-6, 6), ent="carimbo")
   for k, d in enumerate(["seg", "ter", "qua", "qui", "sex"])]
  + [RC(m, 260, 260 + 300 * k, 540, 397.25 + 0.16 * k, ent="pop", rot=random.Random(k).uniform(-8, 8))
     for k, m in enumerate(["is-this-a-pigeon", "monkey-puppet", "drake-hotline-bling", "this-is-fine", "surprised-pikachu"])])
# "Eu não respondia nenhum. E ele continuava mandando." — o balão sem pontos; os memes empilham
S(398.35, None, [],
  [VIVO(BALAO, 500, 520, 398.4, {"q": [(398.4, 3)]}, ent="pop", z=M)]
  + [RC(m, 300, 1200 + 70 * k, 420 + 60 * k, 399.9 + 0.12 * k, ent="queda", rot=random.Random(k + 9).uniform(-12, 12))
     for k, m in enumerate(["sad-pablo-escobar", "evil-kermit", "futurama-fry", "mocking-spongebob", "change-my-mind"])])
# "Não perguntava se eu tava bem. Não cobrava nada. Só deixava ali." — o celular parado, a tachinha
S(401.05, None, [Fd("a01", 420, 1640, 820)],
  [RC("celular", 520, 900, 540, 401.1, caixa=(0.25, 0.05, 0.75, 0.95), ent="pop", rot=-4, z=M),
   AS("b02", 180, 900, 300, W("deixava", 403.6), ent="carimbo"), TX("só deixava ali.", 84, 1450, 880, W("deixava", 403.6), rot=-4)])
# "Eu demorei pra entender o que ele tava fazendo." — a lâmpada acende devagar
S(404.95, None, [Fd("b13", 520, 1640, 820)],
  [AS("c06", 440, 820, 560, 405.0, ent="pop", z=M, pulsa=(0.03, 1.2)), AS("a08", 300, 1300, 300, W("fazendo", 406.6), ent="queda", pisca=0.8)])
# "Ele tava sentado no sofá." — O AMIGO DENTRO DA SALA DO HAMMERSHØI: ele era o "alguém no sofá"
S(407.55, IMG("mae-lendo", 820, 840, (900, 520, -1.2, "pulo")), [],
  [VIVO(AMIGO, 1080, 700, W("sentado", 407.9), {"q": fala_e_pisca([], 407.9, 409.0, seed=12)}, ent="sobe", z=M)],
  zoom=(1.0, 1.08), socos=[(W("sofa", 408.3), 0.04)])
# "Um dia, eu respondi um meme com 'kkkk'." — o celular; kkkk carimba
S(409.15, None, [Fd("a00", 420, 1640, 820)],
  [VIVO(CEL, 820, 560, 409.2, {"q": ciclo(409.2, 410.0, 6, 0.2)}, rot=-4, ent="pop", z=M),
   TX("kkkk", 150, 1400, 360, W("kkk", 410.1), rot=-8, ent="carimbo")], socos=[(W("kkk", 410.1), 0.05)])
# "Foi a coisa mais difícil que eu escrevi naquele ano." — a mão escrevendo, pesada
S(410.85, None, [Fd("b13", 520, 1640, 820)],
  [AS("a09", 700, 860, 600, 410.9, ent="sobe", z=M, caminho=[(411.0, 860, 600), (412.3, 820, 620)]),
   TX("kkkk", 80, 1300, 380, 411.2, rot=-6)])
# "O Storr diz que a capacidade de ficar sozinho é um sinal de maturidade." — o livro volta, com a foto
S(412.85, IMG("storr-foto", 640, 760, (1160, 520, 1.6, (1500, 0))), [],
  [LIVRO(440, 520, 520, 412.9, ent="queda", rot=-6), TX("maturidade", 90, 1180, 960, W("maturidade", 415.7), rot=-4)])
# "Eu achava que maturidade era não precisar de ninguém." — o rei sozinho de novo (o independente)
S(416.55, None, [Fd("b00", 820, 960, 540, vel=8)], [AS("a07", 460, 960, 520, 416.6, ent="queda", z=M)])
# "Não é." — o raio no rei
S(419.75, None, [Fd("b00", 820, 960, 540, vel=8)],
  [AS("a07", 460, 960, 520, 419.75, ent=None, z=M, chaves=GIRA(420.0, [(0, 0), (0.1, -12), (0.2, 10), (0.3, 0)])),
   AS("b04", 420, 1120, 380, 419.8, ent="carimbo")], tremor=[(419.9, 0.3, 7)], socos=[(419.9, 0.05)])
# "É conseguir ficar sozinho... porque você sabe que tem alguém." — a Fragile encosta no ombro do Sam
S(420.4, VID("toque", 456.0, pos=(940, 500, -1.2, "pulo")), [], [], zoom=(1.0, 1.1))

# ===== FINAL =====
# "E quem não aguenta ficar sozinho... dá pra aprender?" — a ampulheta da introdução volta
S(425.45, None, [Fd("a13", 460, 360, 300, vel=60)],
  [AS("c03", 480, 900, 520, 425.5, ent="pop", z=M), AS("a08", 280, 1400, 300, W("prender", 427.0), ent="queda")])
# "Dá." — carimbo
S(427.85, None, [], [TX("Dá.", 220, 960, 540, 427.9, rot=-4, ent="carimbo")], socos=[(427.95, 0.07)], cam=(0, 0, 0, 0))
# "Só que não do jeito que eu tentei." — a sala vazia, o joinha pra baixo
S(428.7, IMG("sala-vazia", 820, 680, (900, 520, -1.4, (0, 1100))),
  [Pc("c01", 300, 1600, 760, de=W("tentei", 429.4), entrada="carimbo")], [])
# "O Storr fecha o livro falando da velhice. Do Beethoven," — o livro; o Beethoven
S(430.35, IMG("beethoven", 700, 820, (1080, 520, 1.6, (1500, 0))), [],
  [LIVRO(420, 440, 540, 430.4, ent="pop", rot=-6), TX("velhice", 84, 440, 900, W("velhice", 431.9), rot=-5)])
# "surdo, isolado, escrevendo no fim da vida as músicas mais íntimas que ele já fez." — a partitura; o disco gira
S(433.95, IMG("beethoven-partitura", 720, 800, (880, 520, -1.4, (0, -1100))),
  [Pc("b06", 380, 1560, 760, de=W("musicas", 436.5), entrada="pop", vel=60, amp=2, gira=0.2)],
  [TX("surdo.", 90, 1500, 260, W("surdo", 434.0), rot=6), AS("a09", 420, 1300, 560, W("escrevendo", 435.2), ent="sobe")])
# "Não porque abandonaram ele. Porque ele voltou pra dentro." — o rosto dele, o cérebro atrás
S(439.25, IMG("beethoven", 1000, 660, (960, 500, -1.2, None), (0.15, 0.0, 0.85, 0.5)),
  [Pc("c06", 300, 1640, 300, de=W("dentro", 441.4), entrada="pop", pulsa=(0.04, 2.0))], [], zoom=ZI)
# "Um retorno a si mesmo." — o subtítulo da capa de novo (voz com eco)
S(442.05, IMG("storr-capa", 560, 860, (960, 520, 1.2, "pulo")), [], [TX("um retorno a si mesmo", 84, 1500, 900, 442.2, rot=-4)], zoom=(1.0, 1.12))
# "Então, se eu pudesse mandar uma encomenda pra mim mesmo, naquele apartamento, ia ser assim:" — o Sam com a carga
S(444.55, VID("chuva-b", 310.0, pos=(940, 500, -1.4, (0, 1100))), [], [AS("a05", 380, 1600, 780, W("encomenda", 446.0), ent="queda", rot=8)])
# "Destinatário: você, três semanas sem falar. Conteúdo: frágil." — a etiqueta da encomenda
ETQ = etiqueta([("DESTINATÁRIO:", "você, três semanas sem falar"), ("CONTEÚDO:", "")], seed=71)
S(449.75, None, [Fd("b13", 520, 1640, 820)],
  [Camada(ETQ, 940, 520, rot=-3, de=V(449.8), amp=3, gira=0.4, sombra=18, seed=_s(), entrada=(0, 1100), z=M),
   TX("FRÁGIL", 120, 1080, 700, W("flash", 453.8), rot=-10, ent="carimbo")], socos=[(W("flash", 453.8), 0.06)])
# "O silêncio não é o problema. Ele só tá sem ninguém no sofá." — o sofá vazio (Hammershøi)
S(454.85, IMG("sofa-vazio", 900, 760, (940, 520, -1.2, (0, -1100))), [], [], zoom=(1.0, 1.08))
# "Responde o meme." — o celular
S(459.55, None, [], [VIVO(CEL, 700, 560, 459.6, {"q": ciclo(459.6, 460.5, 6, 0.2)}, rot=-4, ent="pop", z=M),
                     RC("is-this-a-pigeon", 320, 1400, 360, 459.8, ent="carimbo", rot=6)])
# "Deixa alguém sentar perto." — os dois lendo juntos
S(460.55, IMG("silencio-junto", 820, 760, (940, 520, 1.4, "pulo")), [], [])
# "Guarda umas coisas boas aí dentro: um poema, uma música, uma cidade." — o cérebro; as três coisas entram
S(461.75, None, [Fd("b13", 520, 1640, 820)],
  [AS("c06", 520, 900, 560, 461.8, ent="pop", z=M, pulsa=(0.03, 1.5)),
   AS("a09", 300, 500, 300, W("musica", 463.7) - 0.4, ent="carimbo"), AS("b06", 280, 1340, 300, W("musica", 463.7), ent="carimbo", vel=40),
   RC("budapeste", 320, 1380, 820, W("cidade", 464.2), ent="carimbo", rot=5)])
# "Depois, quando ficar quieto, você vai ver que dá pra ficar." — o Sam andando em paz
S(464.85, VID("chuva-a", 100.0, pos=(960, 500, -1.2, (0, -1100))), [], [], zoom=(1.0, 1.08))
# "E um dia, vai ser você no sofá. Do lado de alguém que tá aprendendo." — o sofá + o BB pequeno do lado
S(470.55, IMG("mae-lendo", 700, 800, (1120, 520, 1.6, (1500, 0))), [],
  [com_video(os.path.join(P, "gameplay", "bb-fofo.mp4"), 42.0, 5.0, 560, 420, 520, 560, -2.4, V(472.4), _s(), GQ,
             vcrop=CROP["bb-fofo"], entrada="pulo")])
# "Remetente: você, daqui um tempo." — a etiqueta, agora com o remetente
ETQ2 = etiqueta([("REMETENTE:", "você, daqui um tempo")], seed=72)
S(475.15, None, [Fd("b13", 520, 1640, 820)],
  [Camada(ETQ2, 940, 520, rot=3, de=V(475.2), amp=3, gira=0.4, sombra=18, seed=_s(), entrada="pop", z=M)])
# "O meu amigo achava que era jogo de gente triste." — o amigo
S(477.35, None, [Fd("b09", 400, 1640, 300)],
  [VIVO(AMIGO, 820, 600, 477.4, {"q": fala_e_pisca([], 477.4, 480.0, seed=13)}, ent="sobe", z=M),
   TX("jogo de gente triste", 72, 1460, 880, W("jogo", 479.5), rot=-4)])
# "Mas é jogo de gente aprendendo a ficar sozinha." — o Sam com a Lou, arco-íris
S(479.95, VID("arcoiris", 780.0, pos=(940, 500, -1.2, "pulo")), [Fd("b05", 240, 1680, 280, vel=20)],
  [TX("aprendendo", 90, 1500, 900, W("aprendendo", 481.8), rot=-5)], zoom=ZI)
# "E ninguém aprende isso sozinho." — o abraço
S(483.25, VID("abraco", 702.0, pos=(960, 500, 1.2, None)), [], [], zoom=ZI)
# "Sempre tem alguém... por perto." — a mãozinha da Lou segura o dedo
S(484.85, VID("mao-lou", 816.0, pos=(960, 500, -1.2, None)), [], [], zoom=(1.0, 1.1))
# ===== CTA =====
# "Bom, e se você quiser alguém por perto enquanto estuda, joga, ou só existe," — estudar, jogar, existir
S(490.25, None, [Fd("b13", 520, 1640, 820)],
  [AS("b10", 360, 500, 400, W("estuda", 493.3) - 0.1, ent="carimbo"), RC("estudante", 120, 472, 320, W("estuda", 493.3), ent="pop", rot=0),
   com_video(os.path.join(P, "gameplay", "chuva-a.mp4"), 20.0, 3.0, 420, 260, 1060, 380, 3.0, V(W("joga", 493.9) - 0.1), _s(), GQ,
             vcrop=None, entrada="pulo"),
   AS("a01", 300, 1520, 760, W("existe", 494.5), ent="carimbo", vel=30),
   TX("estuda", 64, 500, 640, W("estuda", 493.3)), TX("joga", 64, 1060, 600, W("joga", 493.9)), TX("existe", 64, 1520, 960, W("existe", 494.5))])
# "esse canal tá aqui. Se inscreve, deixa um vídeo tocando." — o megafone; o disco tocando
S(495.65, None, [Fd("a01", 420, 1640, 820)],
  [AS("a06", 560, 760, 540, 495.7, ent="carimbo", z=M, balanca=(4, 1.4)), AS("b06", 400, 1400, 600, W("tocando", 497.8) - 0.4, ent="pop", vel=90),
   TX("se inscreve", 96, 1400, 260, W("inscreve", 496.8), rot=6, ent="carimbo")])
# "Eu fico quietinho." — o balão perde os pontos (a mesma piada da introdução)
S(498.55, None, [],
  [VIVO(BALAO, 900, 520, 498.6, {"q": [(498.6, 0), (498.75, 1), (498.9, 2), (499.1, 3)]}, ent="pop", z=M),
   TX("(quietinho)", 84, 1450, 880, W("quietinho", 498.9), rot=-4)])
# "O livro do Storr eu deixo na descrição." — a capa; a seta pra baixo
S(500.05, None, [Fd("b13", 520, 1640, 820)],
  [LIVRO(520, 860, 480, 500.1, ent="pulo", rot=-4, z=M), AS("c13", 300, 1400, 760, W("descricao", 501.3), ent="carimbo", rot=160),
   TX("na descrição", 84, 1400, 300, W("descricao", 501.3), rot=6)])
# "Tchau, meus queridos." — o Sam e a Fragile
S(503.05, VID("dupla", 598.0, pos=(940, 500, -1.2, "pulo")), [Pc("b05", 220, 1680, 280, vel=60), Pc("b08", 160, 300, 820, vel=-60)],
  [TX("tchau!", 110, 1500, 880, 503.2, rot=-6)])


# ---------- legendas: falas difíceis (vozes de personagem) e frases fortes ----------
def LEG(a, b, txt, topo=False):
    ws = [t for t, w in PALAVRAS if a - 0.05 <= t <= b + 0.05]
    pal = txt.split()
    if len(ws) == len(pal):
        ts = ws
    elif ws:
        ts = [ws[0] + (ws[-1] - ws[0]) * k / max(1, len(pal) - 1) for k in range(len(pal))]
    else:
        ts = [a + (b - a) * k / len(pal) for k in range(len(pal))]
    out = [(V(t), V(ts[k + 1]) if k + 1 < len(ts) else V(b), p) for k, (t, p) in enumerate(zip(ts, pal))]
    return dict(palavras=out, topo=topo)


LEGENDAS = [
    LEG(15.0, 17.15, "Cara, isso é jogo de gente triste.", topo=True),
    LEG(57.9, 59.41, "Filho, você não sai não?"),
    LEG(215.1, 219.61, "Peraí. Então pra ficar sozinho eu preciso de alguém? Isso não faz o menor sentido."),
    LEG(315.2, 317.27, "Ela tava sozinha. Mas não tava vazia."),
    LEG(407.6, 408.63, "Ele tava sentado no sofá."),
    LEG(420.0, 423.26, "É conseguir ficar sozinho... porque você sabe que tem alguém."),
    LEG(484.9, 485.79, "Sempre tem alguém por perto."),
]


def _legendas_papel(linhas, saida):
    """Legenda no tema de papel: creme com contorno vermelho-escuro; a palavra dita acende."""
    _legendas_ass_orig(linhas, saida)
    t = open(saida, encoding="utf-8-sig").read()
    t = re.sub(r"Style: Leg,.*", "Style: Leg,Georgia,60,&H00D8EAF0,&H70D8EAF0,&H0021247A,&H00000000,-1,0,0,0,100,100,0,0,1,5,0,2,160,160,64,1", t)
    open(saida, "w", encoding="utf-8-sig").write(t)


_legendas_ass_orig = rn.legendas_ass
rn.legendas_ass = _legendas_papel


# ---------- montar ----------
def montar():
    cenas = []
    SPECS.sort(key=lambda sp: sp["t"])
    for k, sp in enumerate(SPECS):
        t = V(sp["t"]) if k else 0.0
        ate = V(SPECS[k + 1]["t"]) if k + 1 < len(SPECS) else FIM
        for q in QUEBRAS:
            vb = V(q) - VIN
            if t < vb < ate:
                ate = vb
        pos = POS[k % len(POS)]
        pr = sp["pr"]
        seed = 300 + k
        if isinstance(pr, tuple) and pr[0] == "img":
            _, nome, w, h, ps, caixa, ent = pr
            x, y, rot, e = ps or pos
            pr = com_imagem(net(nome), w, h, x, y, rot, t, seed, caixa, entrada=e if ent == "padrao" else ent)
        elif isinstance(pr, tuple) and pr[0] == "vid":
            _, nome, t_orig, w, h, ps, ent, vcrop = pr
            x, y, rot, e = ps or pos
            vc = CROP.get(nome, SEM_LEGENDA) if vcrop == "padrao" else vcrop
            arq = os.path.join(P, "gameplay", nome + ".mp4")
            pr = com_video(arq, max(0.0, t_orig - GP_INI[nome]), round(ate - t + ADIANTA + 0.3, 2), w, h, x, y, rot, t, seed, GQ,
                           vcrop=vc, entrada=e if ent == "padrao" else ent)
        for pc in sp["pecas"]:
            if pc["de"] is None or pc["de"] < t:
                pc["de"] = t
        ce = cena(t, ate, pr, sp["pecas"], sp["ex"], cam=sp["cam"] or CAMS[k % len(CAMS)], socos=sp["socos"], tremor=sp["tremor"])
        ce["zoom"] = sp.get("zoom")
        ce["orig"] = sp["t"]
        cenas.append(ce)
    for q, (num, titulo, tema) in zip(QUEBRAS, VINHETAS):
        cenas.append(vinheta(V(q) - VIN, num, titulo, tema))
    cenas.sort(key=lambda ce: ce["t"])
    for ce in cenas:  # tudo chega JUNTO com a palavra
        if ce.get("vinheta"):
            continue
        ce["t"], ce["ate"] = max(0.0, ce["t"] - ADIANTA), ce["ate"] - ADIANTA
        ce["socos"] = [(a - ADIANTA, f) for a, f in ce["socos"]]
        ce["tremor"] = [(a - ADIANTA, d, f) for a, d, f in ce["tremor"]]
        for cm in ce["camadas"]:
            cm.de = max(ce["t"], cm.de - ADIANTA)
            if cm.caminho:
                cm.caminho = [(a - ADIANTA, x, y) for a, x, y in cm.caminho]
            if cm.chaves:
                cm.chaves = {kk: [(a - ADIANTA, v) for a, v in pts] for kk, pts in cm.chaves.items()}
    for a, b in zip(cenas, cenas[1:]):
        a["ate"] = b["t"]
    cenas[-1]["ate"] = FIM + 0.01
    for ce in cenas:  # momento pesado: fundo preto, tudo em P&B, letra branca
        if not ce.get("vinheta") and PES_A - 0.1 <= ce.get("orig", -1) < PES_B:
            pesado(ce)
    return cenas


# ---------- vinhetas de capítulo (3,6s, sem narração; cada uma com motion e sons próprios) ----------
#   I   "foto":    flash de câmera — a festa lotada entra como foto, a faixa com o título; a interrogação gira no fim
#   II  "colher":  o BB acenando ao fundo, a colher cai girando e assenta na faixa; título em duas linhas sobe
#   III "noite":   a janela de noite, a porta fecha devagar, o título cai letra por letra bem devagar (já é o relato pessoal)
VINHETAS = [("CAPI'TULO I", "FICAR SOZINHO E' ERRADO", "foto"),
            ("CAPI'TULO II", "COMO SE APRENDE|A FICAR SOZINHO", "colher"),
            ("CAPI'TULO III", "QUANDO EU ME ISOLEI", "noite")]
BATE = 3.0


def _faixa(w, h, seed):
    return c.rasgar(c.amassado(w, h, (0xF0, 0xEA, 0xD8), seed, forca=0.14), "tblr", amp=18, fibra=10, seed=seed)


FLASH = Image.new("RGBA", (c.W, c.H), (255, 252, 244, 255))


def vinheta(t0, num, titulo, tema):
    if tema == "foto":
        foto = com_imagem(net("festa-multidao"), 1100, 600, 960, 380, -2.0, t0 + 0.25, 901, entrada="pulo")
        ce = cena(t0, t0 + VIN, foto, [
            peca("b05", 220, 1700, 200, rot=8, de=t0 + 0.25, seed=902, vel=60, z=1.3),
            peca("b08", 160, 240, 220, rot=-8, de=t0 + 0.3, seed=903, vel=-60, z=1.3)],
            [Camada(FLASH, 960, 540, de=t0 + 0.2, ate=t0 + 0.3, amp=0, gira=0, sombra=0, seed=904, z=0.0),
             Camada(FLASH, 960, 540, de=t0 + 1.0, ate=t0 + 1.07, amp=0, gira=0, sombra=0, seed=905, z=0.0),
             Camada(_faixa(1760, 300, 33), 960, 850, rot=-1.0, de=t0 + 0.35, amp=4, gira=0.3, sombra=20, seed=906, entrada=(0, 700), z=0.5),
             Camada(abrir("interrogacao", 300), 1740, 760, rot=10, de=t0 + BATE - 0.2, amp=4, gira=0.6, sombra=14, seed=907, entrada="carimbo", z=1.3,
                    balanca=(12, 1.4))]
            + palavra(num, 960, 770, t0 + 0.55, alt=78, passo=0.05, seed=31, entrada="pop")
            + palavra(titulo, 900, 905, t0 + 1.1, alt=100, passo=0.06, seed=32, entrada="pop"),
            cam=(-10, 0, 10, 0), socos=[(t0 + 0.2, 0.06), (t0 + BATE - 0.2, 0.06)])
    elif tema == "colher":
        bb = com_video(os.path.join(P, "gameplay", "bb-fofo.mp4"), 44.0, VIN + 0.3, 1000, 560, 960, 360, 1.4, t0 + 0.1, 911, GQ,
                       vcrop=CROP["bb-fofo"], entrada=(0, -1100))
        l1, l2 = titulo.split("|")
        col = _recorte(net("bebe-colher"), 520, (0.28, 0.55, 0.72, 0.85))
        colher = Camada(col, 1640, 640, rot=-30, de=t0 + 0.4, amp=3, gira=0.4, sombra=20, seed=912, z=1.3,
                        caminho=[(t0 + 0.4, 1640, -300), (t0 + 1.0, 1640, 640)])
        colher.chaves = {"rot": [(t0 + 0.4, 0), (t0 + 1.0, 340), (t0 + 1.2, 320)]}
        ce = cena(t0, t0 + VIN, bb, [],
                  [colher, Camada(_faixa(1760, 360, 34), 960, 850, rot=1.0, de=t0 + 0.3, amp=4, gira=0.3, sombra=20, seed=913, entrada="sobe", z=0.5)]
                  + palavra(num, 960, 720, t0 + 0.6, alt=72, passo=0.03, seed=38, entrada="sobe")
                  + palavra(l1, 960, 820, t0 + 0.9, alt=92, passo=0.04, seed=39, entrada="sobe")
                  + palavra(l2, 960, 940, t0 + 1.4, alt=92, passo=0.04, seed=40, entrada="sobe"),
                  cam=(0, 10, 0, -10), socos=[(t0 + 1.0, 0.05)])
    else:  # noite
        jan = com_imagem(net("noite-janela"), 1200, 620, 960, 380, -0.8, t0 + 0.1, 921, entrada="pulo")
        porta = _recorte(net("porta-fechada"), 700, (0.12, 0.0, 0.88, 1.0))
        ce = cena(t0, t0 + VIN, jan, [peca("a13", 300, 300, 240, rot=-6, de=t0 + 0.4, seed=922, entrada="queda", balanca=(10, 0.8), z=1.3)],
                  [Camada(porta, 1480, 420, rot=1.5, de=t0 + 0.2, amp=3, gira=0.3, sombra=26, seed=923, z=0.5,
                          caminho=[(t0 + 0.2, 2500, 420), (t0 + BATE, 1480, 420)]),
                   Camada(_faixa(1700, 300, 39), 960, 850, rot=-0.8, de=t0 + 0.3, amp=3, gira=0.3, sombra=20, seed=924, entrada=(0, 700), z=0.5)]
                  + palavra(num, 960, 770, t0 + 0.5, alt=78, passo=0.05, seed=41, entrada="queda")
                  + palavra(titulo, 960, 905, t0 + 0.9, alt=110, passo=0.11, seed=42, entrada="queda"),
                  cam=(0, 6, 0, -6), socos=[(t0 + BATE, 0.05)], tremor=[(t0 + BATE, 0.3, 6)])
    ce["vinheta"] = True
    return ce


# ---------- transições (3 na intro; depois só na virada de assunto e nos capítulos) ----------
FOLHA = c.rasgar(c.amassado(2000, 1500, DETALHE, 7, dobras=60, forca=0.3), "tb", amp=70, fibra=24, seed=8)
JORNAL = c.rasgar(c.jornal(2300, 1400, 12), "lr", amp=60, fibra=20, seed=12)
ESTRELA = c.textura(c.W, c.H, DETALHE, 41, forca=0.06).convert("RGB")
PONTOS = c.explosao_pontos(41)


def _tr(t, tipo):
    return (t, "estrela", ESTRELA, PONTOS) if tipo == "estrela" else \
        (t, "cruza", FOLHA, (0, 1)) if tipo == "folha" else (t, "cruza", JORNAL, (1, 0))


def transicoes():
    tr = [_tr(V(8.35) - ADIANTA, "folha"), _tr(V(W("achei", 28.1) - 0.05) - ADIANTA, "estrela"), _tr(V(32.85) - ADIANTA, "jornal")]
    for q, (ent, sai) in zip(QUEBRAS, [("jornal", "estrela"), ("folha", "jornal"), ("jornal", "folha")]):
        tr += [_tr(V(q) - VIN, ent), _tr(V(q), sai)]
    for o, tipo in [(63.65, "jornal"), (116.75, "folha"), (171.85, "folha"), (215.0, "jornal"), (273.95, "folha"),
                    (391.9, "folha"), (425.45, "jornal"), (490.25, "folha")]:
        tr.append(_tr(V(o) - ADIANTA, tipo))
    return sorted(tr, key=lambda x: x[0])


# ---------- áudio ----------
VOZES = [(15.0, 17.2, "grave"),      # o amigo
         (57.75, 59.45, "aguda"),    # a mãe
         (215.0, 219.65, "radio"),   # quem assiste reclamando
         (361.95, 362.75, "telefone")]  # a moça do caixa


def narracao_final():
    """narração cortada -> vozes de personagem -> silêncio das vinhetas inserido"""
    cort = os.path.join(P, "narracao2_cortada.wav")
    vz = rn.vozes_personagem(cort, [(CUT(a), CUT(b) if CUT(b) > CUT(a) else CUT(a) + (b - a), t) for a, b, t in VOZES],
                             os.path.join(TMP, "narr2_vozes.wav"))
    out = os.path.join(TMP, "narr2_final.wav")
    pts = [0.0] + [CUT(q) for q in QUEBRAS] + [NARR_TOTAL + 0.5]
    n = len(pts) - 1
    fil, ins = ["[0:a]asplit=" + str(n) + "".join(f"[a{k}]" for k in range(n))], []
    for k in range(n):
        pad = f",apad=pad_dur={VIN}" if k < len(QUEBRAS) else ""
        fil.append(f"[a{k}]atrim={pts[k]}:{pts[k + 1]},asetpts=PTS-STARTPTS{pad}[p{k}]")
        ins.append(f"[p{k}]")
    grafo = ";".join(fil) + ";" + "".join(ins) + f"concat=n={n}:v=0:a=1[s]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vz, "-filter_complex", grafo, "-map", "[s]", "-c:a", "pcm_s16le", out], check=True)
    return out


CL = os.path.join(A, "musicas", "classica")


def mus(n):
    return os.path.join(CL, n)


def musica():
    v1, v2, v3 = V(QUEBRAS[0]), V(QUEBRAS[1]), V(QUEBRAS[2])
    return [(f, off, vol * 1.5, de, ate) for f, off, vol, de, ate in [
        (mus("bach-brandenburgo3-allegro-ritmo.mp3"), 1.8, 0.42, 0.0, v1 + 0.3),            # intro: com pulso, até o fim da vinheta
        (mus("bach-suite1-preludio-leve.mp3"), 2.6, 0.55, v1, V(63.65) + 0.3),              # gente rodeada de gente, a mãe: leve
        (mus("schumann-traumerei-reflexiva.mp3"), 0.5, 0.55, V(63.65), V(128.25) + 0.3),     # o livro, o Kant
        (mus("satie-gnossienne1-pesada.mp3"), 0.5, 0.55, V(128.25), v2 + 0.3),               # a pegadinha, "castigo?"
        (mus("debussy-clair-de-lune-reflexiva.mp3"), 2.4, 0.5, v2 - 0.4, V(215.0) + 0.3),   # Winnicott, o bebê da colher, a tese
        (mus("beethoven-luar-allegretto-leve.mp3"), 0.0, 0.45, V(215.0), V(273.95) + 0.3),   # quem assiste, study with me, o teste
        (mus("chopin-noturno20-pesada.mp3"), 1.0, 0.5, V(273.95), v3 + 0.3),                 # Edith Bone
        (mus("satie-gymnopedie1-reflexiva.mp3"), 0.0, 0.55, v3 - 0.4, V(PES_A) + 0.3),       # a mudança
        (mus("grieg-morte-de-aase-pesada.mp3"), 1.1, 0.5, V(PES_A), V(391.9) + 0.3),         # o momento pesado
        (mus("bach-air-reflexiva.mp3"), 4.3, 0.5, V(391.9), V(425.45) + 0.3),                # o amigo, os memes, o sofá
        (mus("grieg-manha-final.mp3"), 0.0, 0.55, V(425.45), V(490.25) + 0.3),               # Beethoven, a encomenda, o final
        (mus("bach-brandenburgo3-allegro-ritmo.mp3"), 30.0, 0.45, V(490.25), FIM),           # CTA: o Bach da introdução volta
    ]]


def efeitos():
    PAPEL, CLIQUE, CLIQUE2 = som("papel-virar-pagina.mp3"), som("camera-clique-holga.mp3"), som("camera-clique-filme-canon.mp3")
    DING, TIQUE = som("notificacao-ding.wav"), som("relogio-tique-taque.mp3")
    sfx = []
    for k, sp in enumerate([s for s in SPECS if s["t"] < QUEBRAS[0]]):  # abertura: papel e clique nos cortes
        sfx.append(((CLIQUE if k % 3 == 0 else CLIQUE2 if k % 3 == 1 else PAPEL), max(0.0, V(sp["t"]) - ADIANTA), 0.22, 0.4))

    def depois(o, arq, vol, dur=None):
        sfx.append((arq, FIM_FALA(o), vol, dur) if dur else (arq, FIM_FALA(o), vol))
    depois(4.9, TIQUE, 0.18, 0.5)                        # 30 horas
    depois(16.7, som("../../sfx_gerados/buzina.wav"), 0.12)  # "jogo de gente triste." (buzina de erro)
    depois(45.3, CLIQUE2, 0.3, 0.4)                      # foto do niver
    depois(47.4, DING, 0.16)                             # grupo da família apitando
    sfx.append((DING, FIM_FALA(47.4) + 0.18, 0.13))
    depois(62.0, som("../../sfx_gerados/ding.wav"), 0.1)  # "pro mercado."
    depois(107.3, TIQUE, 0.2, 0.7)                       # o Kant no horário
    depois(113.1, TIQUE, 0.16, 0.5)
    depois(127.1, PAPEL, 0.2, 0.4)                        # CAPACIDADE
    depois(137.3, som("bater-porta.mp3"), 0.12, 0.3)     # a tachinha (toc)
    depois(139.3, som("whoosh.wav"), 0.12, 0.35)          # caí direitinho
    depois(145.3, som("bater-porta.mp3"), 0.16, 0.6)     # castigo
    depois(162.6, PAPEL, 0.2, 0.4)                        # a prova
    depois(174.4, som("agua.mp3"), 0.12, 0.8)            # o pote do BB
    depois(194.0, som("bater-porta.mp3"), 0.14, 0.6)     # a mãe sai da sala
    depois(203.3, som("sino-igreja.mp3"), 0.1, 1.0)       # a tese (sino baixinho no silêncio)
    depois(219.2, som("../../sfx_gerados/buzina.wav"), 0.1)  # "não faz o menor sentido"
    depois(234.6, som("grilos.wav"), 0.2, 0.5)           # em silêncio, 3 horas
    depois(266.5, som("relogio-tique-taque.mp3"), 0.1, 1.6)  # o teste: o silêncio pensando
    depois(281.4, som("bater-porta.mp3"), 0.22, 0.8)     # não escolhe: a porta fecha
    depois(295.5, som("bater-porta.mp3"), 0.18, 0.6)     # solitária
    depois(297.1, TIQUE, 0.18, 0.6)                       # sete anos
    depois(310.0, PAPEL, 0.14, 0.3)
    depois(346.0, som("vento-forte.mp3"), 0.08, 1.0)     # a montanha
    depois(355.0, DING, 0.1)                              # mensagens sem resposta
    depois(363.2, som("micro-ondas-bip.mp3"), 0.12, 0.25)  # a maquininha (débito)
    depois(366.6, TIQUE, 0.12, 1.1)                       # três semanas (pesado)
    depois(396.6, DING, 0.15)                             # um meme por dia
    sfx += [(DING, FIM_FALA(397.9) + 0.02 + 0.16 * k, 0.11) for k in range(3)]   # todo santo dia
    depois(400.3, DING, 0.12)                             # continuava mandando
    depois(410.1, som("teclado-digitando.mp3"), 0.14, 0.5)  # kkkk
    depois(419.9, som("choque-zap.wav"), 0.18)            # "Não é."
    depois(427.9, PAPEL, 0.22, 0.4)                        # Dá.
    depois(436.5, som("papel-livro-antigo.mp3"), 0.14, 0.6)
    depois(453.8, som("bater-porta.mp3"), 0.14, 0.4)     # carimbo FRÁGIL
    depois(477.0, PAPEL, 0.18, 0.4)                        # remetente
    depois(498.9, som("grilos.wav"), 0.16, 0.6)           # quietinho
    # vinhetas
    t0 = V(QUEBRAS[0]) - VIN  # I: cliques e flash da foto, papel da faixa
    sfx += [(som("camera-cliques-sequencia.mp3"), t0 + 0.15, 0.22, 1.1), (PAPEL, t0 + 0.35, 0.25, 0.4),
            (som("whoosh.wav"), t0 + BATE - 0.25, 0.12, 0.3)]
    t0 = V(QUEBRAS[1]) - VIN  # II: água do pote, a colher cai (tlim), papel
    sfx += [(som("agua.mp3"), t0 + 0.1, 0.14, 1.4), (som("whoosh.wav"), t0 + 0.45, 0.1, 0.3),
            (som("../../sfx_gerados/ding.wav"), t0 + 1.0, 0.14), (PAPEL, t0 + 0.3, 0.22, 0.4)]
    t0 = V(QUEBRAS[2]) - VIN  # III: tique-taque de noite, a porta fecha na batida
    sfx += [(TIQUE, t0 + 0.2, 0.2, 2.6), (PAPEL, t0 + 0.3, 0.18, 0.4), (som("bater-porta.mp3"), t0 + BATE - 0.04, 0.3, 0.9)]
    return sfx


def render_bloco(cenas, a, b, saida, trs, fundo):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{c.W}x{c.H}", "-r", str(c.FPS),
           "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv", "-colorspace", "bt709", "-color_primaries", "bt709",
           "-color_trc", "bt709", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-threads", "4", "-pix_fmt", "yuv420p", "-an", saida + ".tmp.mp4"]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE, creationflags=c.LOW)
    q0, q1 = round(a * c.FPS), round(b * c.FPS)
    for q in range(q0, q1):
        ff.stdin.write(c.desenhar_quadro(cenas, q, fundo, trs).tobytes())
        if (q - q0) % 300 == 0:
            print(f"  quadro {q - q0}/{q1 - q0}", flush=True)
    ff.stdin.close()
    if ff.wait():
        raise RuntimeError("ffmpeg falhou")
    os.replace(saida + ".tmp.mp4", saida)


if __name__ == "__main__":
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    cenas = montar()
    trs = transicoes()
    c.preparar(cenas)
    fundo = c.textura(c.W, c.H, c.FUNDO, 5).convert("RGB")
    print(f"{len(cenas)} cenas, {FIM:.1f}s", flush=True)
    if arg == "quadros":
        pasta = os.path.join(P, "render", f"quadros_{VERSAO}")
        os.makedirs(pasta, exist_ok=True)
        ims = []
        for ce in cenas:
            q = round((ce["t"] + (3.3 if ce.get("vinheta") else min(1.2, (ce["ate"] - ce["t"]) * 0.7))) * c.FPS)
            ims.append((ce["t"], ce.get("orig", -1), c.desenhar_quadro(cenas, q, fundo, trs).resize((480, 270))))
        for f in range(0, len(ims), 20):
            folha = Image.new("RGB", (480 * 4, 290 * 5), (30, 30, 30))
            d = ImageDraw.Draw(folha)
            for k, (t, o, im) in enumerate(ims[f:f + 20]):
                x, y = (k % 4) * 480, (k // 4) * 290
                folha.paste(im, (x, y))
                d.text((x + 6, y + 272), f"{f + k}  {int(t // 60)}:{t % 60:05.2f}  (orig {o:.1f})", fill=(255, 255, 0))
            folha.save(os.path.join(pasta, f"folha_{f // 20:02d}.jpg"), quality=85)
        print("folhas em", pasta)
        sys.exit(0)

    cortes = [0.0] + [float(x) for x in range(60, int(FIM), 60)] + [FIM]
    if arg == "refaz":
        for n in sys.argv[2:]:
            arq = os.path.join(BLOCOS, f"{VERSAO}_{int(n):02d}.mp4")
            if os.path.exists(arq):
                os.remove(arq)
    if arg != "audio":
        partes = []
        for k in range(len(cortes) - 1):
            arq = os.path.join(BLOCOS, f"{VERSAO}_{k:02d}.mp4")
            partes.append(arq)
            if os.path.exists(arq):
                continue
            print(f"bloco {k}: {cortes[k]:.1f}-{cortes[k + 1]:.1f}s", flush=True)
            render_bloco(cenas, cortes[k], cortes[k + 1], arq, trs, fundo)
        lista = os.path.join(BLOCOS, f"{VERSAO}_lista.txt")
        open(lista, "w", encoding="utf-8").writelines(f"file '{p}'\n" for p in partes)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy",
                        os.path.join(TMP, f"mudo_{VERSAO}.mp4")], check=True)
        if arg in ("mudo", "refaz"):
            sys.exit(0)
    MUDO = os.path.join(TMP, f"mudo_{VERSAO}.mp4")
    NARR = narracao_final()
    planos = [dict(t=0.0, clip=(MUDO, 0.0), versao=os.path.getmtime(MUDO), sfx=efeitos())]
    voz = [(V(76.0) - 0.05, V(77.6) + 0.05), (V(442.1) - 0.05, V(443.43) + 0.05)]  # "um retorno a si mesmo" (as 2 vezes)
    rn.render(NARR, 0.0, NARR_TOTAL + VIN * len(QUEBRAS) + 0.5, EM, planos, musica(), FIM, SAIDA, qualidade="final", voz_fx=voz,
              legendas=LEGENDAS)

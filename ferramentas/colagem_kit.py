"""Peças prontas para montar cenas do tema de papel (usa colagem.py e os assets do usuário em imagens/colagem).
Exemplo: projetos/zelda-majoras-mask/teste_ritmo.py
"""
import os
import random

from PIL import Image, ImageDraw, ImageFont

import colagem as c
from colagem import Camada, DETALHE

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # pasta do projeto (acima de ferramentas/)
A = os.path.join(RAIZ, "assets", "jogos-narrado")
I = os.path.join(A, "imagens")
K = os.path.join(I, "colagem")
S = os.path.join(A, "sons")
FUNDO_Z, MEIO_Z, FRENTE_Z = 0.15, 0.5, 1.3  # profundidade: o quanto cada plano acompanha a câmera


def som(n):
    return os.path.join(S, n)


def abrir(nome, lado):
    im = Image.open(os.path.join(K, nome + ".png")).convert("RGBA")
    e = lado / max(im.size)
    return im.resize((round(im.width * e), round(im.height * e)), Image.LANCZOS)


def peca(nome, lado, x, y, rot=0, de=None, entrada="pop", saida=None, amp=6, gira=1.3, sombra=10, seed=0, z=MEIO_Z, **kw):
    """Asset de fora: por padrão chega num pulinho; de=None entra junto com a cena."""
    return dict(nome=nome, lado=lado, x=x, y=y, rot=rot, de=de, entrada=entrada, saida=saida, amp=amp, gira=gira,
                sombra=sombra, seed=seed, z=z, kw=kw)


def fundo_peca(nome, lado, x, y, rot=0, seed=0, **kw):
    """Peça lá atrás: fora de foco, sem sombra, quase não acompanha a câmera."""
    return peca(nome, lado, x, y, rot=rot, amp=3, gira=0.3, sombra=0, seed=seed, z=FUNDO_Z, foco=5, **kw)


def frente_peca(nome, lado, x, y, rot=0, seed=0, **kw):
    """Peça colada na lente: grande, passa por cima da borda da imagem."""
    return peca(nome, lado, x, y, rot=rot, sombra=22, seed=seed, z=FRENTE_Z, **kw)


def fazer(p, t0):
    kw = dict(p["kw"])
    foco = kw.pop("foco", 0)
    im = abrir(p["nome"], p["lado"])
    if foco:
        im = c.desfocar(im, foco)
    return Camada(im, p["x"], p["y"], rot=p["rot"], de=t0 if p["de"] is None else p["de"], entrada=p["entrada"], saida=p["saida"],
                  amp=p["amp"], gira=p["gira"], sombra=p["sombra"], seed=p["seed"], z=p["z"], **kw)


def com_imagem(arq, w, h, x, y, rot, de, seed, caixa=None, entrada=None):
    pap, cx = c.folha((w, h), seed=seed)
    return Camada(c.colar(pap, c.cobrir(arq, w, h, caixa), cx, seed=seed), x, y, rot=rot, de=de, amp=5, gira=0.55, seed=seed,
                  entrada=entrada, z=MEIO_Z, sombra=16)


def com_video(arq, ini, dur, w, h, x, y, rot, de, seed, pasta, vcrop="1440:810:0:135", entrada=None):
    pap, cx = c.folha((w, h), seed=seed)
    quadros, fps = c.quadros_video(arq, ini, dur, w, h, pasta, vcrop=vcrop)
    return Camada(pap, x, y, rot=rot, de=de, amp=5, gira=0.55, seed=seed, video=(quadros, fps, cx, seed), entrada=entrada, z=MEIO_Z, sombra=16)


def texto(txt, fs, x, y, de, rot=-4, seed=0):
    """Comentário à mão, em DETALHE, direto no papel."""
    cm = Camada(c.nota(txt, fs), x, y, rot=rot, de=de, amp=3, gira=0.5, sombra=0, seed=seed, entrada="pop", z=FRENTE_Z)
    cm.nota = True
    return cm


_FUNDO_PRETO = {}


def pesado(ce, seed=5):
    """Momento pesado (decisão do usuário, 03/11/2026): fundo preto, detalhes em branco, todas as imagens/vídeos em P&B.
    Aplica numa cena já montada (cena()/vinheta). Os cantos fixos (sol vermelho, jornal) também ficam em P&B."""
    import numpy as np
    if seed not in _FUNDO_PRETO:
        _FUNDO_PRETO[seed] = c.textura(c.W, c.H, (18, 17, 16), seed, forca=0.08).convert("RGB")
    ce["fundo"] = _FUNDO_PRETO[seed]

    def cinza(im):
        if im is None:
            return im
        a = np.asarray(im.convert("RGBA")).copy()
        if getattr(cm, "nota", False):  # letra à mão: vira branca
            a[..., :3] = 240
        else:
            g = (a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114).astype(np.uint8)
            a[..., 0] = a[..., 1] = a[..., 2] = g
        return Image.fromarray(a, "RGBA")

    for cm in ce["camadas"]:
        if getattr(cm, "_pb_feito", False):
            continue
        cm.img = cinza(cm.img)
        if cm.sprites:
            cm.sprites = [cinza(s) for s in cm.sprites]
        cm.pb, cm._pb_feito, cm.cache = True, True, {}
    return ce


def acento(letra, marca, seed):
    """O alfabeto não tem acento: cola um pedacinho de papel com o acento em cima da letra."""
    fonte = ImageFont.truetype(c.F + "ariblk.ttf", int(letra.height * 0.62))
    tira = c.textura(int(letra.width * 0.56), int(letra.height * 0.3), c.FUNDO, seed)
    w, h = tira.size
    d = ImageDraw.Draw(tira)
    if marca == "/":  # acento agudo desenhado: o da fonte fica fino demais
        d.polygon([(w * 0.30, h * 0.86), (w * 0.50, h * 0.86), (w * 0.76, h * 0.14), (w * 0.50, h * 0.14)], fill=DETALHE + (255,))
    else:
        x0, y0, x1, y1 = d.textbbox((0, 0), marca, font=fonte)
        d.text(((w - x1 - x0) / 2, (h - y1 - y0) / 2), marca, font=fonte, fill=DETALHE + (255,))
    tira = c.recorte_mal(tira, "ret", borda=3, seed=seed, torto=0.05, pontas=8)
    out = Image.new("RGBA", (letra.width, letra.height + int(tira.height * 0.72)), (0, 0, 0, 0))
    out.alpha_composite(letra, (0, out.height - letra.height))
    out.alpha_composite(tira, ((letra.width - tira.width) // 2, 0))
    return out


def palavra(txt, x, y, de, alt=128, passo=0.03, seed=1, entrada="queda"):
    """Palavra com as letras do alfabeto do usuário, uma a uma. Acento: ~ ^ ' depois da letra."""
    r = random.Random(seed)
    letras = []
    for k, ch in enumerate(txt):
        if ch in "~^'":
            letras[-1] = acento(letras[-1], {"~": "~", "^": "^", "'": "/"}[ch], seed + k)
            continue
        if ch == " ":
            letras.append(Image.new("RGBA", (int(alt * 0.4), alt), (0, 0, 0, 0)))
            continue
        im = Image.open(os.path.join(K, f"letra_{ch}.png")).convert("RGBA")
        e = alt / im.height
        letras.append(im.resize((round(im.width * e), alt), Image.LANCZOS))
    total = sum(p.width - 6 for p in letras)
    cx, out = x - total / 2, []
    for k, p in enumerate(letras):
        out.append(Camada(p, cx + p.width / 2, y - (p.height - alt) / 2 + r.uniform(-9, 9), rot=r.uniform(-6, 6), de=de + k * passo,
                          amp=3, gira=1.0, sombra=7, seed=seed + k, entrada=entrada, z=FRENTE_Z))
        cx += p.width - 6
    return out


def fixos():
    """Os dois pedaços grandes de papel do usuário: fundo da colagem, sempre nos mesmos cantos."""
    return [Camada(abrir("b00", 680), 1680, 300, amp=3, gira=0.25, sombra=8, z=FUNDO_Z),
            Camada(abrir("b13", 640), 215, 790, amp=3, gira=0.25, sombra=8, z=FUNDO_Z)]


def cena(t, ate, principal, pecas, extras=(), cam=(0, 0, 0, 0), socos=(), tremor=()):
    """Monta a cena na ordem de profundidade: fixos, peças de fundo, meio, principal, frente, extras."""
    atras = [fazer(p, t) for p in pecas if p["z"] == FUNDO_Z]
    meio = [fazer(p, t) for p in pecas if p["z"] == MEIO_Z]
    frente = [fazer(p, t) for p in pecas if p["z"] == FRENTE_Z]
    pr = [principal] if principal else []
    return dict(t=t, ate=ate, cam=cam, socos=list(socos), tremor=list(tremor), camadas=fixos() + atras + meio + pr + frente + list(extras))


# ---------- dar vida aos assets (pedido do usuário: piscar olho, mexer mão, misturar assets) ----------
# Cada gerador devolve uma lista de quadros (sprites) do asset; a Camada troca de quadro com chaves={"q": [(t, i), ...]}.

def _regiao(arr, semente, tol):
    """Máscara da região contínua com a cor da semente (flood fill), para achar tela, branco do olho etc."""
    from collections import deque
    import numpy as np
    h, w = arr.shape[:2]
    cor = arr[semente[1], semente[0], :3].astype(int)
    ok = (np.abs(arr[..., :3].astype(int) - cor).max(2) <= tol) & (arr[..., 3] > 200)
    m = np.zeros((h, w), bool)
    q = deque([(semente[1], semente[0])])
    m[semente[1], semente[0]] = True
    while q:
        y, x = q.popleft()
        for a, b in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= a < h and 0 <= b < w and ok[a, b] and not m[a, b]:
                m[a, b] = True
                q.append((a, b))
    return m


def olho_piscando(lado, semente=(0.5, 0.55)):
    """olho.png: [aberto, meio fechado, fechado, olhando p/ esquerda, olhando p/ direita] — íris desenhada no branco do olho;
    a pálpebra (cor da pele) desce sobre ele."""
    import numpy as np
    from PIL import ImageDraw as D
    im = abrir("olho", lado)
    arr0 = np.asarray(im).copy()
    h, w = arr0.shape[:2]
    m = _regiao(arr0, (int(w * semente[0]), int(h * semente[1])), 40)
    ys, xs = np.nonzero(m)
    claros = arr0[..., :3].mean(2)
    pele_px = arr0[(claros > 120) & (claros < 215) & ~m & (arr0[..., 3] > 200)][:, :3]
    pele = np.median(pele_px, axis=0).astype(np.uint8) if len(pele_px) else np.array([165, 160, 155], np.uint8)
    cx, cy, alt = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2, ys.max() - ys.min()

    def com_iris(dx):
        iris = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = D.Draw(iris)
        r = alt * 0.42
        x, y = cx + dx * (xs.max() - xs.min()) * 0.22, cy + alt * 0.05
        d.ellipse((x - r, y - r, x + r, y + r), fill=(70, 62, 58, 255))
        d.ellipse((x - r * 0.75, y - r * 0.75, x + r * 0.75, y + r * 0.75), fill=(105, 92, 84, 255))
        d.ellipse((x - r * 0.42, y - r * 0.42, x + r * 0.42, y + r * 0.42), fill=(18, 16, 15, 255))
        d.ellipse((x + r * 0.15, y - r * 0.45, x + r * 0.38, y - r * 0.22), fill=(250, 250, 250, 255))
        a = arr0.copy()
        ia = np.asarray(iris)
        sel = m & (ia[..., 3] > 0)
        a[sel, :3] = ia[sel][:, :3]
        return a

    arr = com_iris(0)
    im = Image.fromarray(arr)
    out = [im]
    for frac in (0.55, 1.0):
        a = arr.copy()
        for x in range(xs.min(), xs.max() + 1):
            col = ys[xs == x]
            if not len(col):
                continue
            y0, y1 = col.min(), col.max()
            yc = int(y0 + (y1 - y0) * frac)
            a[y0:yc + 1, x, :3] = pele
            a[max(y0, yc - 2):yc + 2, x, :3] = (35, 30, 28)  # cílios na beira da pálpebra
        out.append(Image.fromarray(a))
    out += [Image.fromarray(com_iris(-1)), Image.fromarray(com_iris(1))]
    return out


def pontos_sumindo(lado):
    """a03.png (balão "..."): [3 pontos, 2, 1, 0] — os pontos somem um a um."""
    import numpy as np
    from PIL import ImageFilter
    im = abrir("a03", lado)
    arr = np.asarray(im).copy()
    escuro = (arr[..., :3].max(2) < 110) & (arr[..., 3] > 200)
    h, w = escuro.shape
    escuro[: int(h * 0.15)] = False
    escuro[int(h * 0.75):] = False
    escuro[:, : int(w * 0.12)] = False
    escuro[:, int(w * 0.92):] = False
    claro = (arr[..., :3].min(2) > 200) & (arr[..., 3] > 200)
    fundo_balao = np.median(arr[claro][:, :3], axis=0).astype(np.uint8)
    xs = np.nonzero(escuro)[1]
    x0, x1 = xs.min(), xs.max() + 1
    cortes = [x0 + (x1 - x0) * k // 3 for k in range(4)]
    out = [im]
    a = arr.copy()
    for k in (2, 1, 0):  # some da direita pra esquerda
        faixa = np.zeros_like(escuro)
        faixa[:, cortes[k] - 3:cortes[k + 1] + 3] = True
        sel = faixa & (np.asarray(Image.fromarray(np.uint8(escuro * 255)).filter(ImageFilter.MaxFilter(7))) > 0)
        a[sel, :3] = fundo_balao
        out.append(Image.fromarray(a.copy()))
    return out


def tela_chiando(nome, lado, caixa, n=4, seed=1, tirar=()):
    """TV/monitor: a tela vira chiado (ruído + faixas) em n quadros. caixa = (x0, y0, x1, y1) em fração da peça;
    só os pixels claros da tela mudam (rachaduras e moldura ficam); 'tirar' = caixas que ficam de fora (mãos na frente).
    Conferir a caixa num QUADRO RENDERIZADO, não numa grade a olho."""
    import numpy as np
    im = abrir(nome, lado)
    arr = np.asarray(im)
    h, w = arr.shape[:2]
    m = np.zeros((h, w), bool)
    m[int(caixa[1] * h):int(caixa[3] * h), int(caixa[0] * w):int(caixa[2] * w)] = True
    for x0, y0, x1, y1 in tirar:
        m[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = False
    m &= (arr[..., :3].mean(2) > 125) & (arr[..., 3] > 200)
    r = np.random.default_rng(seed)
    out = [im]
    for k in range(n):
        a = arr.copy()
        ruido = r.integers(40, 235, (h, w // 3 + 1)).repeat(3, 1)[:, :w]
        faixa = (np.arange(h)[:, None] + k * 9) % 23 < 4
        v = np.where(faixa, np.minimum(ruido + 50, 255), ruido)
        for c in range(3):
            a[..., c] = np.where(m, v, a[..., c])
        out.append(Image.fromarray(a))
    return out


def tela_rolando(nome, lado, semente, n=6, tol=14, seed=2):
    """Celular: mensagens subindo na tela (balões claros e vermelhos), n quadros em loop."""
    import numpy as np
    from PIL import ImageDraw as D
    im = abrir(nome, lado)
    arr = np.asarray(im)
    h, w = arr.shape[:2]
    m = _regiao(arr, (int(w * semente[0]), int(h * semente[1])), tol)
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    r = random.Random(seed)
    baloes = []
    y = 0
    while y < (y1 - y0) * 2:
        lado_dir = r.random() < 0.5
        bw = int((x1 - x0) * r.uniform(0.35, 0.6))
        bh = int((y1 - y0) * 0.07)
        baloes.append((lado_dir, bw, bh, y))
        y += bh + int((y1 - y0) * 0.05)
    altura = y
    out = []
    for k in range(n):
        tela = Image.new("RGBA", (w, h), tuple(int(v) for v in arr[int(h * semente[1]), int(w * semente[0]), :3]) + (255,))
        d = D.Draw(tela)
        desl = altura * k / n
        for lado_dir, bw, bh, yb in baloes:
            for rep in (0, altura):
                yy = y0 + yb + rep - desl
                if y0 - bh < yy < y1:
                    xx = x1 - bw - 12 if lado_dir else x0 + 12
                    cor = DETALHE + (255,) if lado_dir else (245, 242, 235, 255)
                    d.rounded_rectangle((xx, yy, xx + bw, yy + bh), radius=bh // 2, fill=cor)
        a = arr.copy()
        t = np.asarray(tela)
        a[m] = t[m]
        out.append(Image.fromarray(a))
    return out


def foto_viva(nome, lado, boca=None, olhos=(), abre=0.018):
    """Pessoa em foto (P&B) que FALA e PISCA (pedido do usuário: dar vida às fotos de gente, conforme o contexto).
    boca = (x0, y_labio, x1, y_queixo) em fração: o queixo (abaixo da linha dos lábios) desce e abre um vão escuro.
    olhos = [(x0, y0, x1, y1), ...]: a pálpebra cobre o olho (repete a pele de cima) e desenha a linha dos cílios.
    Quadros: índice = boca (0 fechada, 1 meio, 2 aberta) + 3 * piscando (0/1)."""
    import numpy as np
    from PIL import ImageDraw as D, ImageFilter
    im = abrir(nome, lado)
    base = np.asarray(im).copy()
    h, w = base.shape[:2]

    def mascara(desenho, borrao):
        m = Image.new("L", (w, h), 0)
        desenho(D.Draw(m))
        return np.asarray(m.filter(ImageFilter.GaussianBlur(borrao))).astype(np.float32)[..., None] / 255

    def com_boca(arr, k):
        """o queixo desce (máscara esfumada) e abre um vão escuro em forma de lente entre os cantos da boca"""
        if not boca or k == 0:
            return arr
        x0, yl, x1, yq = boca[0] * w, boca[1] * h, boca[2] * w, boca[3] * h
        d = max(2, round(abre * h * (0.55 if k == 1 else 1.0)))
        desce = np.zeros_like(arr)
        desce[d:] = arr[:-d]
        larg = (x1 - x0) * 0.62
        m = mascara(lambda g: g.ellipse((x0 - larg * 0.15, yl - (yq - yl) * 0.9, x1 + larg * 0.15, yq), fill=255), d * 1.2)
        m[: int(yl)] = 0  # só o que está abaixo da linha dos lábios desce
        a = (arr * (1 - m) + desce * m).astype(np.uint8)
        a[..., 3] = arr[..., 3]
        cm, lx = (x0 + x1) / 2, (x1 - x0) * 0.42
        vao = mascara(lambda g: g.ellipse((cm - lx, yl - d * 0.15, cm + lx, yl + d * 1.15), fill=255), 1.2)
        escuro = np.array([34, 24, 24, 255], np.float32)
        return (a * (1 - vao) + escuro * vao).astype(np.uint8)

    def piscando(arr):
        """pálpebra: oval esfumado da cor da pele de cima do olho + linha dos cílios"""
        a = arr.astype(np.float32)
        for x0, y0, x1, y1 in olhos:
            X0, Y0, X1, Y1 = x0 * w, y0 * h, x1 * w, y1 * h
            alt = Y1 - Y0
            d = max(2, int(alt * 0.9))
            desce = arr.astype(np.float32).copy()  # a pele de cima do olho desce sobre ele (mantém textura e sombra da foto)
            desce[d:] = arr[:-d]
            m = mascara(lambda g: g.ellipse((X0, Y0 - alt * 0.05, X1, Y1), fill=255), max(1.0, alt * 0.18))
            a = a * (1 - m) + desce * m
            cil = mascara(lambda g: g.arc((X0 + alt * 0.1, Y0 - alt * 0.4, X1 - alt * 0.1, Y1 - alt * 0.05), 20, 160, fill=255,
                                          width=max(1, int(alt * 0.08))), 0.8)
            a = a * (1 - cil * 0.45) + np.array([40, 34, 30, 255], np.float32) * cil * 0.45
        out = a.astype(np.uint8)
        out[..., 3] = arr[..., 3]
        return out

    out = []
    for p in (False, True):
        for k in (0, 1, 2):
            a = com_boca(base, k)
            out.append(Image.fromarray(piscando(a) if p and olhos else a))
    return out


def fala_e_pisca(falas, t0, t1, seed=5, pisca=True):
    """chaves "q" para foto_viva: boca mexendo nas falas [(ini, fim), ...] (troca a cada 0,1s) e piscadas de vez em quando."""
    r = random.Random(seed)
    piscs = []
    t = t0 + r.uniform(0.4, 1.0)
    while pisca and t < t1:
        piscs.append((t, t + 0.16))
        t += r.uniform(1.6, 2.6)
    ch, t = [], t0
    while t < t1:
        boca = r.choice((1, 2, 2, 1, 0)) if any(a <= t < b for a, b in falas) else 0
        olho = 3 if any(a <= t < b for a, b in piscs) else 0
        ch.append((round(t, 3), boca + olho))
        t += 0.1
    return ch


def piscadas(t0, t1, cada=1.7, seed=3):
    """chaves de piscar: olho aberto, de vez em quando fecha (meio, fechado, meio, aberto) em ~0,3s."""
    r = random.Random(seed)
    ch, t = [(t0, 0)], t0 + r.uniform(0.3, 0.8)
    while t < t1:
        ch += [(t, 1), (t + 0.07, 2), (t + 0.17, 1), (t + 0.24, 0)]
        t += cada * r.uniform(0.7, 1.3)
    return ch


def ciclo(t0, t1, n, passo):
    """chaves de quadro em loop: 0, 1, ..., n-1, 0, ... a cada 'passo' segundos."""
    ch, t, k = [], t0, 0
    while t < t1:
        ch.append((t, k % n))
        t += passo
        k += 1
    return ch


def adiantar(cenas, seg, fim):
    """Tudo chega JUNTO com a palavra: a entrada começa antes dela, não depois."""
    for ce in cenas:
        ce["t"], ce["ate"] = max(0.0, ce["t"] - seg), ce["ate"] - seg
        ce["socos"] = [(a - seg, f) for a, f in ce["socos"]]
        ce["tremor"] = [(a - seg, d, f) for a, d, f in ce["tremor"]]
        for cam in ce["camadas"]:
            cam.de = max(ce["t"], cam.de - seg)
            if cam.caminho:
                cam.caminho = [(a - seg, x, y) for a, x, y in cam.caminho]
    cenas[-1]["ate"] = fim + 0.01

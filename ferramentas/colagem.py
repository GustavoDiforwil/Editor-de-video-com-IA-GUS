"""Colagem de papel do estilo Jogos Narrado: gera as peças (papel amassado, rasgo, recorte mal feito, pontilhado,
letras recortadas) e renderiza as cenas com movimento travado, tipo stop-motion (vídeo sem áudio).
A mistura de áudio continua no render_narrado: passe o vídeo mudo como clip de um plano só.

Cena: dict(t, ate, camadas=[Camada(...)]). A ordem da lista é a ordem de empilhar.
Camada: peça RGBA + centro (x, y) em pixels + de/ate em segundos do vídeo. Por padrão a peça só aparece no lugar; a imagem/vídeo principal usa entrada=(dx, dy) (desliza rápido) ou entrada="pulo" (pulinho vindo do meio).
Vídeo dentro da folha: Camada(folha, video=(quadros, (x, y, w, h)), ...), com os quadros vindos de quadros_video().
"""
import math
import os
import random
import subprocess

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from render_shots import LOW

W, H, FPS = 1920, 1080, 30
FUNDO = (0xE6, 0xDE, 0xC7)
DETALHE = (0x7A, 0x24, 0x21)
FOLHA = (0xD4, 0xCC, 0xB6)
QUADROS_POR_POSE = 8  # 30/8 = 3,75 poses por segundo: travado, mas sem agitar (pedido do usuário)
METADE_T = 0.17  # meia transição, em segundos
RITMO_ANIM = 0.5  # as animações contínuas andam na metade: rápido demais parece vídeo em 2x (pedido do usuário)
DESLIZA = 9  # quadros da entrada deslizando (0,3s)
PULO = ((0.45, 0), (0.6, -18), (0.76, -32), (0.9, -42), (1.02, -44), (1.07, -34), (1.07, -20), (1.04, -8), (1.01, 0), (1.0, 0))  # (escala, altura) por quadro
F = "C:/Windows/Fonts/"
FONTES_RECORTE = ["impact.ttf", "ariblk.ttf", "georgiab.ttf", "timesbd.ttf", "courbd.ttf"]


def ruido(w, h, escala, seed):
    g = np.random.default_rng(seed)
    pq = g.random((max(2, h // escala + 2), max(2, w // escala + 2)), dtype=np.float32)
    return np.asarray(Image.fromarray(pq).resize((w, h), Image.BICUBIC))


def textura(w, h, cor, seed, forca=0.03):
    """Papel liso: grão fino sobre a cor, com a média na cor pedida."""
    n = sum(p * (ruido(w, h, e, seed + e) - 0.5) for e, p in ((2, 0.7), (7, 0.5), (90, 0.25)))
    n = (n - n.mean()) * forca * 2
    return Image.fromarray(np.uint8(np.clip(np.array(cor, np.float32) * (1 + n)[..., None], 0, 255))).convert("RGBA")


def amassado(w, h, cor, seed, dobras=46, forca=0.2):
    """Papel amassado: dobras retas somadas viram facetas com vinco, iluminadas de lado."""
    g = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    alt = np.zeros((h, w), np.float32)
    for _ in range(dobras):
        ang, px, py = g.uniform(0, math.pi), g.uniform(0, w), g.uniform(0, h)
        d = (xx - px) * math.cos(ang) + (yy - py) * math.sin(ang)
        alt += g.uniform(0.15, 1.0) * np.abs(d) * g.choice([-1, 1])
    gy, gx = np.gradient(alt)
    luz = gx * 0.7 + gy * 0.7
    luz = (luz - luz.mean()) / (luz.std() + 1e-6)
    luz = np.clip(luz, -2.2, 2.2) * forca / 2
    grao = (ruido(w, h, 2, seed + 1) - 0.5) * 0.05
    return Image.fromarray(np.uint8(np.clip(np.array(cor, np.float32) * (1 + luz + grao)[..., None], 0, 255))).convert("RGBA")


def _perfil(n, amp, seed):
    """Linha irregular do rasgo: ondas largas + serrilhado fino."""
    g = np.random.default_rng(seed)
    p = np.zeros(n)
    for passo, peso in ((n // 5 + 2, 1.0), (45, 0.5), (11, 0.22), (3, 0.09)):
        pts = g.random(n // passo + 3)
        p += peso * np.interp(np.arange(n) / passo, np.arange(len(pts)), pts)
    return (p - p.min()) / (p.max() - p.min() + 1e-6) * amp


def rasgar(img, lados="tblr", amp=24, fibra=11, seed=1):
    """Rasga as bordas pedidas (t, b, l, r) com a faixa branca de fibra que o papel de verdade mostra."""
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w]
    dentro = np.ones((h, w), bool)
    miolo = np.ones((h, w), bool)
    for k, lado in enumerate("tblr"):
        if lado not in lados:
            continue
        n = w if lado in "tb" else h
        p = _perfil(n, amp, seed + k * 7)
        extra = fibra * (0.35 + 1.1 * _perfil(n, 1, seed + k * 11))
        lin = {"t": yy, "b": h - 1 - yy, "l": xx, "r": w - 1 - xx}[lado]
        q = xx if lado in "tb" else yy
        dentro &= lin >= p[q]
        miolo &= lin >= (p + extra)[q]
    arr = np.array(img.convert("RGBA"))
    arr[dentro & ~miolo, :3] = (245, 241, 230)
    arr[..., 3] = np.where(dentro, arr[..., 3], 0)
    return Image.fromarray(arr)


def pontilhado(img, passo=7, escuro=(22, 20, 18), claro=(238, 233, 220), contraste=1.25):
    """P&B de jornal: pontos a 45 graus, como os recortes das referências."""
    a = img.convert("RGBA")
    g = np.asarray(a.convert("L"), np.float32) / 255
    g = np.clip((g - 0.5) * contraste + 0.5, 0, 1)
    yy, xx = np.mgrid[0:a.height, 0:a.width].astype(np.float32)
    k = math.pi / passo
    t = 0.5 + 0.25 * (np.cos((xx + yy) * k) + np.cos((xx - yy) * k))
    borda = np.clip((g - t) * 7 + 0.5, 0, 1)[..., None]
    rgb = np.array(escuro, np.float32) * (1 - borda) + np.array(claro, np.float32) * borda
    out = np.dstack([rgb, np.asarray(a.getchannel("A"), np.float32)])
    return Image.fromarray(np.uint8(out))


def recorte_mal(img, forma="ret", borda=11, seed=1, torto=0.035, pontas=15):
    """Tesourada ruim: polígono de cortes retos e tortos, com contorno branco tipo adesivo."""
    r = random.Random(seed)
    im = img.convert("RGBA")
    w, h = im.size
    pts = []
    if forma == "ret":
        por_lado = max(1, pontas // 4)
        cantos = [(0, 0), (1, 0), (1, 1), (0, 1)]
        for k, (x0, y0) in enumerate(cantos):
            x1, y1 = cantos[(k + 1) % 4]
            for j in range(por_lado):
                f = j / por_lado + (r.uniform(0.15, 0.85) / por_lado if j else 0)
                pts.append(((x0 + (x1 - x0) * f) * w + (r.uniform(0, torto) if x0 + (x1 - x0) * f < 0.5 else -r.uniform(0, torto)) * w,
                            (y0 + (y1 - y0) * f) * h + (r.uniform(0, torto) if y0 + (y1 - y0) * f < 0.5 else -r.uniform(0, torto)) * h))
    else:
        for k in range(pontas):
            a = 2 * math.pi * k / pontas
            pts.append(((0.5 + 0.5 * (1 - 2 * torto) * math.cos(a) + r.uniform(-torto, torto)) * w,
                        (0.5 + 0.5 * (1 - 2 * torto) * math.sin(a) + r.uniform(-torto, torto)) * h))
    pad = borda + 2
    s = 2  # desenha maior e reduz: o corte fica sem serrilhado
    ms = Image.new("L", ((w + 2 * pad) * s, (h + 2 * pad) * s), 0)
    d = ImageDraw.Draw(ms)
    pp = [((x + pad) * s, (y + pad) * s) for x, y in pts]
    d.polygon(pp, fill=255)
    mi = ms.resize((w + 2 * pad, h + 2 * pad), Image.LANCZOS)
    if borda:
        d.line(pp + pp[:1], fill=255, width=2 * borda * s, joint="curve")
    mo = ms.resize(mi.size, Image.LANCZOS)
    out = Image.new("RGBA", mi.size, (248, 245, 236, 255))
    out.paste(im, (pad, pad), mi.crop((pad, pad, pad + w, pad + h)))
    out.putalpha(mo)
    return out


def cobrir(caminho, w, h, caixa=None):
    """Abre a imagem (caixa = recorte em fração x0,y0,x1,y1) e preenche w x h, cortando o que sobrar."""
    im = caminho if isinstance(caminho, Image.Image) else Image.open(caminho)
    im = im.convert("RGB")
    if caixa:
        im = im.crop((int(caixa[0] * im.width), int(caixa[1] * im.height), int(caixa[2] * im.width), int(caixa[3] * im.height)))
    e = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * e)), max(h, round(im.height * e))), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def folha(conteudo_wh, seed=1, margem=(64, 56), cor=FOLHA):
    """Pedaço de papel amassado em que a imagem/vídeo é colada. Devolve (peça, caixa do conteúdo)."""
    cw, ch = conteudo_wh
    mx, my = margem
    w, h = cw + 2 * mx, ch + 2 * my
    pap = rasgar(amassado(w, h, cor, seed), "tblr", amp=15, fibra=8, seed=seed)
    return pap, (mx, my, cw, ch)


def colar(pap, img, caixa, seed=1, borda=0):
    """Cola a imagem na folha com corte levemente torto."""
    x, y, w, h = caixa
    rec = recorte_mal(img.convert("RGBA").resize((w, h)), "ret", borda=borda, seed=seed, torto=0.016, pontas=20)
    p = pap.copy()
    p.alpha_composite(rec, (x - (rec.width - w) // 2, y - (rec.height - h) // 2))
    return p


def _estrelado(raio, seed, pontas, interno, irregular):
    r = random.Random(seed)
    pts = []
    n = pontas * 2
    for k in range(n):
        a = 2 * math.pi * k / n + r.uniform(-irregular, irregular) * 0.25
        q = raio if k % 2 == 0 else raio * interno
        q *= 1 + r.uniform(-irregular, irregular)
        pts.append((raio * 1.35 + q * math.cos(a), raio * 1.35 + q * math.sin(a)))
    return pts


def estrela(raio, cor=DETALHE, seed=1, pontas=5, interno=0.45, irregular=0.08):
    return _forma(raio, cor, seed, _estrelado(raio, seed, pontas, interno, irregular))


def explosao(raio, cor=DETALHE, seed=1):
    return _forma(raio, cor, seed, _estrelado(raio, seed, 11, 0.5, 0.3), sticker=False)


def _forma(raio, cor, seed, pts, sticker=True):
    s = 2
    lado = int(raio * 2.7)
    m = Image.new("L", (lado * s, lado * s), 0)
    d = ImageDraw.Draw(m)
    pp = [(x * s, y * s) for x, y in pts]
    d.polygon(pp, fill=255)
    interno = m.resize((lado, lado), Image.LANCZOS)
    pap = textura(lado, lado, cor, seed, forca=0.06)
    if not sticker:
        pap.putalpha(interno)
        return pap
    d.line(pp + pp[:1], fill=255, width=9 * s, joint="curve")
    out = Image.new("RGBA", (lado, lado), (248, 245, 236, 255))
    out.paste(pap, (0, 0), interno)
    out.putalpha(m.resize((lado, lado), Image.LANCZOS))
    return out


def nota(txt, fs=64, cor=DETALHE):
    """Letra de mão, direto no papel."""
    fonte = ImageFont.truetype(F + "segoepr.ttf", fs)
    x0, y0, x1, y1 = ImageDraw.Draw(Image.new("L", (4, 4))).multiline_textbbox((0, 0), txt, font=fonte)
    im = Image.new("RGBA", (x1 - x0 + 12, y1 - y0 + 12), (0, 0, 0, 0))
    ImageDraw.Draw(im).multiline_text((6 - x0, 6 - y0), txt, font=fonte, fill=cor + (255,), spacing=2)
    return im


def letra_recortada(ch, fs, seed):
    """Uma letra num pedacinho de papel, tipo bilhete de sequestro."""
    r = random.Random(seed)
    fundo, tinta = r.choice([(DETALHE, FUNDO), (FUNDO, (24, 22, 20)), ((24, 22, 20), FUNDO), ((247, 244, 235), DETALHE)])
    fonte = ImageFont.truetype(F + r.choice(FONTES_RECORTE), int(fs * r.uniform(0.9, 1.1)))
    x0, y0, x1, y1 = ImageDraw.Draw(Image.new("L", (4, 4))).textbbox((0, 0), ch, font=fonte)
    pw, ph = r.randint(14, 24), r.randint(12, 20)
    im = textura(x1 - x0 + 2 * pw, y1 - y0 + 2 * ph, fundo, seed)
    ImageDraw.Draw(im).text((pw - x0, ph - y0), ch, font=fonte, fill=tinta + (255,))
    return recorte_mal(im, "ret", borda=4, seed=seed, torto=0.05, pontas=9)


def palavra_recortada(txt, x, y, de, ate=None, fs=112, seed=1, passo=0.05, gira=7):
    """Camadas das letras, entrando uma a uma, centradas em (x, y)."""
    r = random.Random(seed)
    pecas = [letra_recortada(c, fs, seed * 100 + k) for k, c in enumerate(txt)]
    total = sum(p.width - 8 for p in pecas)
    cx = x - total / 2
    out = []
    for k, p in enumerate(pecas):
        out.append(Camada(p, cx + p.width / 2, y + r.uniform(-12, 12), rot=r.uniform(-gira, gira), de=de + k * passo, ate=ate,
                          amp=4, gira=1.6, sombra=7, seed=seed + k))
        cx += p.width - 8
    return out


def jornal(w, h, seed=1):
    """Página de jornal velho composta aqui (sem marca nem anúncio de ninguém): manchetes + colunas de texto."""
    r = random.Random(seed)
    corpo = ("Uma noite destas, vindo da cidade para o Engenho Novo, encontrei no trem da Central um rapaz aqui do bairro, "
             "que eu conheço de vista e de chapéu. Cumprimentou-me, sentou-se ao pé de mim, falou da lua e dos ministros, "
             "e acabou recitando-me versos. A viagem era curta, e os versos pode ser que não fossem inteiramente maus. ").split()
    manchetes = ["A LUA CONTINUA CAINDO", "Prazo adiado outra vez", "SEGUNDA EU COMEÇO", "Cidade decide fazer festa", "RELÓGIO ADIANTADO"]
    s = 2
    pag = Image.new("L", (w * s, h * s), 232)
    d = ImageDraw.Draw(pag)
    tx = ImageFont.truetype(F + "times.ttf", 19 * s)
    cols = max(2, w // 270)
    cw = w * s // cols
    for k in range(cols):
        x0, y = k * cw + 14 * s, r.randint(6, 40) * s
        while y < h * s:
            if r.random() < 0.3:
                m = ImageFont.truetype(F + r.choice(("timesbd.ttf", "georgiab.ttf", "impact.ttf")), r.randint(30, 44) * s)
                tit = r.choice(manchetes)
                while d.textlength(tit, font=m) > cw - 28 * s:
                    m = ImageFont.truetype(m.path, m.size - 2 * s)
                d.text((x0, y), tit, font=m, fill=18)
                y += m.size + 14 * s
            for _ in range(r.randint(5, 11)):
                lin, i = "", r.randrange(len(corpo))
                while d.textlength(lin + corpo[i % len(corpo)], font=tx) < cw - 30 * s:
                    lin += corpo[i % len(corpo)] + " "
                    i += 1
                d.text((x0, y), lin, font=tx, fill=35)
                y += 23 * s
            y += 16 * s
        d.line([(k * cw + cw - 3 * s, 0), (k * cw + cw - 3 * s, h * s)], fill=60, width=s)
    pag = pag.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.5))
    a = np.asarray(pag, np.float32) + (ruido(w, h, 2, seed) - 0.5) * 22 + (ruido(w, h, 60, seed + 1) - 0.5) * 22
    return Image.fromarray(np.uint8(np.clip(a, 0, 255))).convert("RGBA")


def megafone(lado=760, seed=3):
    """Megafone em recorte: corpo pontilhado, boca e borda em DETALHE, contorno branco."""
    s = 2
    L = lado * s
    def pol(pts):
        return [(px * L, py * L) for px, py in pts]
    corpo = Image.new("RGB", (L, L), (205, 200, 186))
    d = ImageDraw.Draw(corpo)
    for k in range(120):  # sombra de um lado pro outro do cone, que o pontilhado transforma em volume
        v = int(245 - k * 1.3)
        d.line([(0, L * (0.2 + k * 0.0055)), (L, L * (0.2 + k * 0.0055))], fill=(v, v, v), width=int(L * 0.0065))
    cone = pol([(0.10, 0.42), (0.20, 0.36), (0.70, 0.10), (0.80, 0.70), (0.25, 0.60), (0.11, 0.58)])
    pega = pol([(0.25, 0.58), (0.38, 0.60), (0.33, 0.92), (0.20, 0.90)])
    boca = (0.56 * L, 0.06 * L, 0.90 * L, 0.74 * L)
    alfa = Image.new("L", (L, L), 0)
    da = ImageDraw.Draw(alfa)
    da.polygon(cone, fill=255)
    da.polygon(pega, fill=255)
    da.ellipse(boca, fill=255)
    pont = pontilhado(corpo.resize((lado, lado)), passo=7).resize((L, L), Image.NEAREST).convert("RGB")
    im = Image.new("RGB", (L, L), (0, 0, 0))
    im.paste(pont, (0, 0))
    d = ImageDraw.Draw(im)
    d.polygon(pega, fill=DETALHE)
    d.ellipse(boca, fill=DETALHE)
    d.ellipse((boca[0] + 0.03 * L, boca[1] + 0.05 * L, boca[2] - 0.03 * L, boca[3] - 0.05 * L), fill=(232, 226, 208))
    d.ellipse((boca[0] + 0.09 * L, boca[1] + 0.21 * L, boca[2] - 0.13 * L, boca[3] - 0.21 * L), fill=(24, 22, 20))
    grossa = alfa.filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.MaxFilter(21))
    out = Image.new("RGBA", (L, L), (248, 245, 236, 255))
    out.paste(im, (0, 0), alfa)
    out.putalpha(grossa)
    return out.resize((lado, lado), Image.LANCZOS)


def quadros_video(arq, ini, dur, w, h, pasta, vcrop=None, fps=15):
    """Extrai o trecho em poucos quadros por segundo: o vídeo também fica travado, junto com o papel."""
    os.makedirs(pasta, exist_ok=True)
    nome = f"{os.path.splitext(os.path.basename(arq))[0]}_{ini:.2f}_{dur:.2f}_{w}x{h}"
    if vcrop:  # recorte diferente = quadros diferentes (antes o cache ignorava o vcrop)
        import hashlib
        nome += "_" + hashlib.md5(vcrop.encode()).hexdigest()[:6]
    dest = os.path.join(pasta, nome)
    if not os.path.isdir(dest) or not os.listdir(dest):
        os.makedirs(dest, exist_ok=True)
        vf = f"fps={fps}," + (f"crop={vcrop}," if vcrop else "") + f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-threads", "2", "-ss", f"{ini:.3f}", "-t", f"{dur:.3f}",
                        "-i", arq, "-vf", vf, "-q:v", "2", os.path.join(dest, "q%04d.jpg")], check=True, creationflags=LOW)
    return [os.path.join(dest, n) for n in sorted(os.listdir(dest))], fps


def _interp(pts, t):
    """valor das chaves [(t, v), ...] no instante t (linear, segura nas pontas)"""
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            return v0 + (v1 - v0) * (t - t0) / max(1e-6, t1 - t0)
    return pts[-1][1]


def _escala(im, e):
    return im if e == 1.0 else im.resize((max(1, round(im.width * e)), max(1, round(im.height * e))), Image.BILINEAR)


def _quique(rel, seq):
    return seq[min(rel, len(seq) - 1)]


POP = (0.2, 0.45, 0.72, 0.95, 1.1, 1.13, 1.09, 1.03, 0.99, 1.0)  # pulinho no lugar: nasce pequeno, passa do ponto e assenta
SAIDA = (1.0, 1.1, 0.7, 0.25)  # pop de saída nos últimos quadros da cena


class Camada:
    """Peça da colagem. Só peça e posição são obrigatórias; o resto é a animação dela.
    entrada: (dx, dy) desliza | "pulo" vem do meio da tela | "pop" pulinho no lugar | "queda" cai quicando | "sobe" sobe da borda quicando
    saida: "pop" some num pulinho no fim da cena (ate_cena é preenchido pelo render)
    vel: graus/s | balanca: (graus, hz) | flutua: (px, hz) | pulsa: (fração, hz) | pisca: hz
    caminho: [(t, x, y), ...] percorre os pontos (tempo do vídeo) | z: profundidade (paralaxe da câmera; 0 = fundo, 1 = frente)
    """

    def __init__(self, img, x, y, rot=0.0, de=0.0, ate=None, amp=5, gira=0.8, sombra=12, seed=0, video=None, entrada=None, saida=None,
                 vel=0.0, balanca=None, flutua=None, pulsa=None, pisca=None, caminho=None, z=0.5, sprites=None, chaves=None):
        # sprites: lista de quadros do asset (dar vida: olho piscando, tela chiando); chaves: {"q": [(t, i)], "rot": [(t, graus)],
        # "esc": [(t, escala)], "sy": [(t, achatamento vertical)]} em tempo do vídeo — q troca seco, o resto interpola
        self.sprites, self.chaves = sprites, chaves
        self.img, self.x, self.y, self.rot, self.de, self.ate = img if img is not None or not sprites else sprites[0], x, y, rot, de, ate
        self.sombra, self.video, self.entrada, self.saida = sombra, video, entrada, saida
        self.vel, self.balanca, self.flutua, self.pulsa, self.pisca, self.caminho, self.z = vel, balanca, flutua, pulsa, pisca, caminho, z
        self.ate_cena = None
        self.pb = False  # momento pesado: quadros do vídeo em preto e branco (colagem_kit.pesado)
        r = random.Random(seed)
        # as poses alternam um lado e o outro; o sorteio só evita que a alternância fique mecânica
        lado = r.choice([-1, 1])
        self.fase = r.uniform(0, 6.28)
        self.poses = [(lado * s * amp * r.uniform(0.6, 1.1), r.uniform(-amp, amp) * 0.55, -lado * s * gira * r.uniform(0.3, 1.0))
                      for s in (1, -1, 1, -1)]
        self.cache = {}

    def _pronta(self, ang, base):
        """Gira a peça e põe a sombra (cacheado: girar é o que mais custa)."""
        im = base.convert("RGBa").rotate(ang, Image.BICUBIC, expand=True).convert("RGBA")
        if not self.sombra:
            return im
        s = self.sombra
        pad = s * 3
        out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
        a = Image.new("L", out.size, 0)
        a.paste(im.getchannel("A"), (pad + s // 2, pad + s))
        a = a.filter(ImageFilter.GaussianBlur(s)).point(lambda v: int(v * 0.42))
        out.putalpha(a)
        out.alpha_composite(im, (pad, pad))
        return out

    def desenha(self, tela, t, quadro, cam=(0, 0)):
        rel = quadro - round(self.de * FPS)
        pose = (quadro // QUADROS_POR_POSE) % 4
        dx, dy, da = self.poses[pose]
        esc = 1.0
        x, y = self.x, self.y
        tq = (quadro // 3) * 3 / FPS  # as animações contínuas também andam travadas (10 passos por segundo)
        if self.caminho:
            pts = self.caminho
            if tq <= pts[0][0]:
                x, y = pts[0][1:]
            elif tq >= pts[-1][0]:
                x, y = pts[-1][1:]
            else:
                for (t0, x0, y0), (t1, x1, y1) in zip(pts, pts[1:]):
                    if t0 <= tq <= t1:
                        k = (tq - t0) / (t1 - t0)
                        x, y = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
                        break
        quadro_sp, sy = 0, 1.0
        if self.chaves:
            for nome, pts in self.chaves.items():
                if nome == "q":
                    quadro_sp = [i for t0, i in pts if t0 <= tq][-1] if pts and pts[0][0] <= tq else pts[0][1]
                    continue
                v = _interp(pts, tq)
                if nome == "rot":
                    da += v
                elif nome == "esc":
                    esc *= v
                elif nome == "sy":
                    sy = v
        ta = tq * RITMO_ANIM
        if self.vel:
            da += self.vel * ta
        if self.balanca:
            da += self.balanca[0] * math.sin(2 * math.pi * self.balanca[1] * ta + self.fase)
        if self.flutua:
            dy += self.flutua[0] * math.sin(2 * math.pi * self.flutua[1] * ta + self.fase)
        if self.pulsa:
            esc *= 1 + self.pulsa[0] * math.sin(2 * math.pi * self.pulsa[1] * ta + self.fase)
        if self.pisca and int(ta * self.pisca * 2) % 2 and rel > 8:
            return
        e = self.entrada
        if e == "pulo" and rel < len(PULO):  # cresce a partir do meio da tela, passa do ponto e assenta
            k, hop = PULO[rel]
            f = 1 - k if k < 1 else 0
            esc, dx, dy = esc * k, dx + (W / 2 - x) * f, dy + (H / 2 - y) * f + hop
        elif e == "pop" and rel < len(POP):
            esc *= POP[rel]
        elif e == "queda" and rel < 13:
            dy += _quique(rel, (-900, -680, -480, -310, -170, -70, 0, -30, -48, -52, -40, -20, 0))
        elif e == "sobe" and rel < 13:
            dy += _quique(rel, (900, 680, 480, 310, 170, 70, 0, 30, 48, 52, 40, 20, 0))
        elif e == "gira" and rel < 10:  # entra girando e crescendo (motion de intro)
            k = (1 - rel / 10) ** 2
            esc, da = esc * (1 - 0.85 * k), da + 260 * k
        elif e == "carimbo" and rel < 8:  # bate grande vindo da câmera e assenta (carimbo)
            esc *= (2.4, 1.9, 1.45, 1.12, 0.94, 0.98, 1.02, 1.0)[rel]
        elif isinstance(e, tuple) and rel < DESLIZA:  # desliza rápido, freando
            k = (1 - rel / DESLIZA) ** 2
            dx, dy = dx + e[0] * k, dy + e[1] * k
        if self.saida == "pop" and self.ate_cena is not None:
            falta = round(self.ate_cena * FPS) - quadro - 1
            if falta < len(SAIDA):
                esc *= SAIDA[falta]
        ang = -(self.rot + da)
        ang_q, esc_q = round(ang * 2) / 2, round(esc * 60) / 60
        if self.video:
            quadros, fps, caixa, rec_seed = self.video
            n = min(len(quadros) - 1, int(max(0.0, t - self.de) * fps))
            chave = (n, ang_q, esc_q)
            if chave not in self.cache:
                self.cache = {}
                fr = Image.open(quadros[n])
                if self.pb:
                    fr = fr.convert("L").convert("RGB")
                base = colar(self.img, fr, caixa, seed=rec_seed)
                self.cache[chave] = self._pronta(ang_q, _escala(base, esc_q))
        else:
            sy_q = round(sy * 30) / 30
            chave = (ang_q, esc_q, quadro_sp, sy_q)
            if chave not in self.cache:
                base = self.sprites[quadro_sp] if self.sprites else self.img
                base = _escala(base, esc_q)
                if sy_q != 1.0:
                    base = base.resize((base.width, max(1, round(base.height * sy_q))), Image.LANCZOS)
                self.cache[chave] = self._pronta(ang_q, base)
        p = self.cache[chave]
        tela.paste(p, (round(x + dx + cam[0] * self.z - p.width / 2), round(y + dy + cam[1] * self.z - p.height / 2)), p)


def desfocar(im, raio):
    """Profundidade: peça lá no fundo fica fora de foco (o alfa borra junto)."""
    pm = im.convert("RGBa").filter(ImageFilter.GaussianBlur(raio))
    return pm.convert("RGBA")


def _camera(cena, t):
    """Deslocamento da câmera na cena: drift lento de (x0, y0) até (x1, y1), somado aos sustos de 'tremor'."""
    x0, y0, x1, y1 = cena.get("cam", (0, 0, 0, 0))
    k = (t - cena["t"]) / max(0.01, cena["ate"] - cena["t"])
    cx, cy = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    for t0, dur, forca in cena.get("tremor", ()):
        if t0 <= t < t0 + dur:
            s = 1 if int((t - t0) * 8) % 2 else -1
            cx, cy = cx + s * forca, cy - s * forca * 0.6
    return cx, cy


def _soco(cena, tela, t):
    """Zoom direto na palavra: a tela toda dá um soco e volta. cena["zoom"] = (z0, z1): zoom contínuo na cena (>= 1)."""
    base = 1.0
    if cena.get("zoom"):
        z0, z1 = cena["zoom"]
        k = min(1.0, max(0.0, (t - cena["t"]) / max(0.01, cena["ate"] - cena["t"])))
        base = z0 + (z1 - z0) * k
    e = 1.0
    for t0, forca in cena.get("socos", ()):
        if 0 <= t - t0 < 0.5:
            e = max(e, 1 + forca * (1 - (t - t0) / 0.5) ** 2)
    e *= base
    if abs(e - 1.0) < 1e-4:
        return tela
    w, h = round(W / e), round(H / e)
    x, y = (W - w) // 2, (H - h) // 2
    return tela.resize((W, H), Image.BILINEAR, box=(x, y, x + w, y + h))


def _transicoes(tela, t, transicoes):
    """Transição centrada no instante do corte: a cobertura esconde o corte (dura 2 * METADE_T)."""
    for tc, tipo, peca, sent in transicoes:
        k = (t - tc + METADE_T) / (2 * METADE_T)
        if not 0 <= k <= 1:
            continue
        if tipo == "cruza":  # folha enorme atravessa a tela
            horiz = sent[0] != 0
            cheio = (W + peca.width) if horiz else (H + peca.height)
            desl = -(peca.width if horiz else peca.height) + cheio * (k if (sent[0] + sent[1]) > 0 else 1 - k)
            xy = (round(desl), (H - peca.height) // 2) if horiz else ((W - peca.width) // 2, round(desl))
            tela.paste(peca, xy, peca)
        elif tipo == "estrela":  # explosão cresce até cobrir e abre já na cena nova
            r = 2600 * (1 - abs(2 * k - 1)) ** 1.4 + 1  # o papel é da tela toda: só a máscara da explosão muda de tamanho
            pts = [(W / 2 + r * px, H / 2 + r * py) for px, py in sent]
            m = Image.new("L", (W, H), 0)
            ImageDraw.Draw(m).polygon(pts, fill=255)
            tela.paste(peca, (0, 0), m)
    return tela


def explosao_pontos(seed=1, pontas=11):
    """Contorno da explosão (raio 1) para a transição "estrela"."""
    r = random.Random(seed)
    n = pontas * 2
    return [(((1 if k % 2 == 0 else 0.5) * r.uniform(0.75, 1.1)) * math.cos(2 * math.pi * k / n),
             ((1 if k % 2 == 0 else 0.5) * r.uniform(0.75, 1.1)) * math.sin(2 * math.pi * k / n)) for k in range(n)]


def preparar(cenas):
    for c in cenas:
        for cam in c["camadas"]:
            cam.ate_cena = c["ate"] if cam.ate is None else cam.ate


def desenhar_quadro(cenas, q, fundo, transicoes=()):
    t = q / FPS
    proprio = [c["fundo"] for c in cenas if c.get("fundo") is not None and c["t"] <= t < c["ate"]]
    tela = (proprio[0] if proprio else fundo).copy()  # cena com fundo próprio (momento pesado: preto)
    for c in cenas:
        if not c["t"] <= t < c["ate"]:
            for cam in c["camadas"]:
                cam.cache = {}
            continue
        cx = _camera(c, t)
        for cam in c["camadas"]:
            ate = c["ate"] if cam.ate is None else cam.ate
            if cam.de <= t < ate:
                cam.desenha(tela, t, q, cx)
        tela = _soco(c, tela, t)
    return _transicoes(tela, t, transicoes)


def render_cenas(cenas, fim, saida, fundo_seed=5, transicoes=()):
    """Escreve o vídeo mudo: fundo de papel fixo + camadas ativas + câmera + transições."""
    preparar(cenas)
    fundo = textura(W, H, FUNDO, fundo_seed).convert("RGB")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-threads", "4", "-pix_fmt", "yuv420p", "-an", saida]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE, creationflags=LOW)
    total = round(fim * FPS)
    for q in range(total):
        ff.stdin.write(desenhar_quadro(cenas, q, fundo, transicoes).tobytes())
        if q % 60 == 0:
            print(f"quadro {q}/{total}", flush=True)
    ff.stdin.close()
    if ff.wait():
        raise RuntimeError("ffmpeg falhou")

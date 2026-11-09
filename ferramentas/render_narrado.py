"""Editor do estilo Jogos Narrado: imagens/clipes sobre a narração (a narração é o motor).

Linha do tempo em segundos do VÍDEO FINAL. Cada plano (dict) vai de 't' até o 't' do próximo (o último até 'fim').
  img    : caminho da imagem (jpg/png)  — ou —  clip=(arquivo, inicio) trecho de vídeo (sem áudio)  — ou —  color='black'
           clip aceita vcrop='w:h:x:y' (tirar barra preta), z/cx/cy (zoom direto fixo) e lento (câmera lenta, ex. 2)
  fit    : 'cover' (tela cheia, padrão) | 'contain' (inteira, sobre fundo desfocado e escuro — memes, prints)
  z, z2  : zoom inicial/final (movimento lento; padrão 1.0 -> 1.06), cx/cy: centro do zoom 0..1
  bw, dark, grain : preto e branco / escurecer / grão de filme
  fin, fout : fade do preto / pro preto (segundos)
  text   : legenda discreta embaixo (ty, fs) | card : texto centralizado (várias linhas com \n; cfs, cy_txt)
  nota   : dict(txt, x, y, de, cor, fs) — comentário escrito à mão (estilo Ludoviajante), só às vezes
  sobre  : [dict(img, x, y, w, de, ate, borda=8, rot)] — imagens menores POR CIMA do fundo (recorte com borda
           branca e sombra, entra com fade rápido em 'de'); borda=0 para PNG recortado.
           Animação: x2/y2 + mov (s) = desliza de (x,y) até (x2,y2) freando (entrar pela borda, cair, espiar)
  contador: dict(s=300, vel=1, fs, cor, y) — cronômetro mm:ss descendo (vel = quão rápido corre)
  spin   : dict(img, x, y, w, de, vel) — imagem girando por cima (x,y = centro 0..1; 'de' = começa a girar em s)
  sfx    : [(arquivo, atraso_no_plano, volume, dur_opcional, inicio_no_arquivo_opcional)] — sutil, abaixo da voz
Música: musica=[(arquivo, inicio_no_arquivo, volume, de, ate)] — abaixa sozinha sob a narração.
Legendas: render(..., legendas=[dict(palavras=[(ini, fim, palavra)], topo=False)]) — frases da fala queimadas no vídeo,
  a palavra dita acende (karaokê). topo=True quando embaixo tem caixa de texto do jogo / texto do plano.
"""
import json
import os
import subprocess

from render_shots import gain, esc, LOW

W, H, FPS = 1280, 720, 30
K, CRF, PRESET = 1.0, "21", "veryfast"
FONTE = "C\\:/Windows/Fonts/segoeuib.ttf"
FONTE_CARD = "C\\:/Windows/Fonts/georgia.ttf"
FONTE_NOTA = "C\\:/Windows/Fonts/segoepr.ttf"
VERSAO_PLANO = 2  # mude ao alterar render_plano(): invalida o cache dos planos


def set_quality(q):
    global W, H, K, CRF, PRESET
    W, H, K, CRF, PRESET = (1920, 1080, 1.5, "17", "medium") if q == "final" else (1280, 720, 1.0, "21", "veryfast")


def run(cmd):
    subprocess.run(cmd, check=True, creationflags=LOW)


def render_plano(i, s, dur, tmp):
    out = os.path.join(tmp, f"p{i:03d}.mkv")
    # cache: plano igual (mesmas opções, duração e qualidade) não é renderizado de novo
    assin = json.dumps([{k: v for k, v in s.items() if k not in ("t", "sfx")}, round(dur, 3), W, CRF, VERSAO_PLANO], sort_keys=True, default=str)
    marca = out + ".json"
    if os.path.exists(out) and os.path.exists(marca) and open(marca, encoding="utf-8").read() == assin:
        return out
    PW, PH = int(W * 1.5), int(H * 1.5)  # pré-escala maior: o zoompan não serrilha
    inputs = []
    if "clip" in s:
        f, a = s["clip"]
        inputs += ["-ss", f"{a:.3f}", "-t", f"{dur + 0.5:.3f}", "-i", f]  # sobra; o corte exato é por nº de quadros
        base = f"[0:v]fps={FPS},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1"
        if s.get("vcrop"):  # tira barra preta (trailer 4:3): 'w:h:x:y'
            base += f",crop={s['vcrop']}"
        if s.get("z", 1.0) > 1.0:  # zoom direto no vídeo (fixo)
            z, cx, cy = s["z"], s.get("cx", 0.5), s.get("cy", 0.5)
            base += f",crop=iw/{z}:ih/{z}:(iw-iw/{z})*{cx}:(ih-ih/{z})*{cy}"
        if s.get("lento"):  # câmera lenta (fator)
            base += f",setpts={s['lento']}*PTS"
        base += f",scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    elif "color" in s:
        inputs += ["-f", "lavfi", "-t", f"{dur + 0.2:.3f}", "-i", f"color=c={s['color']}:s={W}x{H}:r={FPS}"]
        base = "[0:v]setsar=1"
    else:
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur + 0.2:.3f}", "-i", s["img"]]
        if s.get("fit") == "contain":
            pre = (f"[0:v]format=rgb24,split[a][b];[a]scale={PW}:{PH}:force_original_aspect_ratio=increase,crop={PW}:{PH},"
                   f"boxblur=30:2,eq=brightness=-0.25[fundo];[b]scale={int(PW * 0.86)}:{int(PH * 0.86)}:force_original_aspect_ratio=decrease[fr];"
                   f"[fundo][fr]overlay=(W-w)/2:(H-h)/2")
        else:
            pre = f"[0:v]format=rgb24,scale={PW}:{PH}:force_original_aspect_ratio=increase,crop={PW}:{PH}"
        z, z2 = s.get("z", 1.0), s.get("z2", s.get("z", 1.0) + 0.06)
        n = max(1, int(round(dur * FPS)))
        cx, cy = s.get("cx", 0.5), s.get("cy", 0.5)
        base = (f"{pre},zoompan=z='{z}+({z2 - z})*on/{n}':d=1:s={W}x{H}:fps={FPS}:"
                f"x='(iw-iw/zoom)*{cx}':y='(ih-ih/zoom)*{cy}',setsar=1")
    v = base
    if s.get("bw"):
        v += ",hue=s=0"
    if s.get("dark"):
        v += ",eq=brightness=-0.15:contrast=0.95"
    if s.get("grain"):
        v += ",noise=alls=10:allf=t"
    if s.get("spin"):
        sp = s["spin"]
        n_in = sum(1 for x in inputs if x == "-i")
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", sp["img"]]
        de, vel = round(sp.get("de", 0), 2), sp.get("vel", 6)
        v += (f"[bs];[{n_in}:v]format=rgba,scale={int(sp.get('w', 200) * K)}:-1,"
              # c=black@0 (transparente): com c=none o fundo não é limpo e o giro deixa rastro dos quadros anteriores
              f"rotate=a='if(gt(t,{de}),(t-{de})*{vel},0)':c=black@0:ow='hypot(iw,ih)':oh=ow[gi];"
              f"[bs][gi]overlay=x={W}*{sp.get('x', 0.5)}-w/2:y={H}*{sp.get('y', 0.2)}-h/2")
    for k, o in enumerate(s.get("sobre", [])):  # imagens por cima do fundo (recorte com borda e sombra)
        n_in = sum(1 for x in inputs if x == "-i")
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", o["img"]]
        de, ate = o.get("de", 0), o.get("ate", dur)
        ch = f"[{n_in}:v]format=rgba,scale={int(o.get('w', 360) * K)}:-1"
        if o.get("borda", 8):
            b = int(o.get("borda", 8) * K)
            ch += f",pad=iw+{2 * b}:ih+{2 * b}:{b}:{b}:color=white"
        if o.get("rot"):
            ch += f",rotate={o['rot']}*PI/180:c=black@0:ow='rotw({o['rot']}*PI/180)':oh='roth({o['rot']}*PI/180)'"
        ch += f",fade=t=in:st={de}:d=0.15:alpha=1,split[o{k}][q{k}];[q{k}]colorchannelmixer=rr=0:gg=0:bb=0:aa=0.55,boxblur={int(8 * K)}[h{k}]"
        x, y = o.get("x", 0.7), o.get("y", 0.5)
        # movimento ("animação" simples): vai de (x,y) até (x2,y2) em 'mov' s a partir de 'de', freando no fim
        x2, y2, mov = o.get("x2", x), o.get("y2", y), max(0.05, o.get("mov", 0.5))
        e = f"(1-pow(1-min(1\\,max(0\\,(t-{de})/{mov}))\\,2))"
        X = f"{W}*({x}+({x2 - x})*{e})-w/2"
        Y = f"{H}*({y}+({y2 - y})*{e})-h/2"
        sh = int(10 * K)
        v += (f"[b{k}];{ch};[b{k}][h{k}]overlay=x={X}+{sh}:y={Y}+{sh}:enable='between(t,{de},{ate})'[c{k}];"
              f"[c{k}][o{k}]overlay=x={X}:y={Y}:enable='between(t,{de},{ate})'")
    if s.get("contador"):  # cronômetro descendo (mm:ss), 'vel' = segundos do relógio por segundo de vídeo
        ct = s["contador"]
        tf = os.path.join(tmp, f"k{i:03d}.txt")
        S, vel = ct.get("s", 300), ct.get("vel", 1)
        open(tf, "w", encoding="utf-8").write(
            f"%{{eif:floor(max(0,{S}-t*{vel})/60):d:2}}:%{{eif:mod(floor(max(0,{S}-t*{vel})),60):d:2}}")
        v += (f",drawtext=fontfile='{FONTE}':textfile='{esc(tf)}':fontsize={int(ct.get('fs', 170) * K)}:"
              f"fontcolor={ct.get('cor', '0xff3b30')}:borderw={int(4 * K)}:bordercolor=black:"
              f"x=(w-text_w)/2:y=h*{ct.get('y', 0.5)}-text_h/2")
    if s.get("text"):
        tf = os.path.join(tmp, f"t{i:03d}.txt")
        open(tf, "w", encoding="utf-8").write(s["text"])
        a = s.get("text_de", 0)
        v += (f",drawtext=fontfile='{FONTE}':textfile='{esc(tf)}':fontsize={int(s.get('fs', 40) * K)}:fontcolor=white:"
              f"box=1:boxcolor=black@0.55:boxborderw={int(12 * K)}:x=(w-text_w)/2:y=h*{s.get('ty', 0.84)}-text_h/2:"
              f"enable='gte(t,{a})'")
    if s.get("nota"):  # comentário escrito à mão, pequeno e colorido (às vezes, não sempre)
        nt = s["nota"]
        tf = os.path.join(tmp, f"n{i:03d}.txt")
        open(tf, "w", encoding="utf-8").write(nt["txt"])
        v += (f",drawtext=fontfile='{FONTE_NOTA}':textfile='{esc(tf)}':fontsize={int(nt.get('fs', 52) * K)}:"
              f"fontcolor={nt.get('cor', '0xffd84d')}:borderw={int(3 * K)}:bordercolor=black@0.85:"
              f"x=w*{nt.get('x', 0.75)}-text_w/2:y=h*{nt.get('y', 0.2)}-text_h/2:enable='gte(t,{nt.get('de', 0)})'")
    if s.get("card"):
        lines = s["card"].split("\n")
        fs = int(s.get("cfs", 54) * K)
        for k, line in enumerate(lines):
            tf = os.path.join(tmp, f"c{i:03d}_{k}.txt")
            open(tf, "w", encoding="utf-8").write(line)
            off = (k - (len(lines) - 1) / 2) * fs * 1.25
            v += (f",drawtext=fontfile='{FONTE_CARD}':textfile='{esc(tf)}':fontsize={fs}:fontcolor=white:"
                  f"x=(w-text_w)/2:y=h*{s.get('cy_txt', 0.5)}+{off:.0f}-text_h/2")
    if s.get("fin"):
        v += f",fade=t=in:st=0:d={s['fin']}"
    if s.get("fout"):
        v += f",fade=t=out:st={max(0, dur - s['fout']):.3f}:d={s['fout']}"
    v += ",format=yuv420p[v]"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-threads", "4", *inputs, "-filter_complex", v,
         "-map", "[v]", "-frames:v", str(max(1, round(dur * FPS))), "-c:v", "libx264", "-preset", PRESET, "-crf", CRF, "-r", str(FPS), "-an", out])
    open(marca, "w", encoding="utf-8").write(assin)
    return out


def cortar_narracao(src, ilhas, saida, pausa=0.28, pausas=None, pre=0.05, pos=0.09):
    """Monta a narração só com as ilhas de FALA (sem respiração) e pausas controladas.
    ilhas: [(ini, fim)] no arquivo original (de ilhas_fala.py; ilhas próximas podem vir juntas).
    pausas: {indice_da_ilha: segundos de silêncio DEPOIS dela} — o silêncio que é piada/respiro;
    o resto usa 'pausa' (ou a pausa natural, se já for menor).
    Devolve f(t_original) -> t_na_narracao_cortada, para posicionar planos pelas palavras."""
    pausas = pausas or {}
    partes, mapa, t = [], [], 0.0
    for k, (a, b) in enumerate(ilhas):
        a0 = max(0.0, a - pre) if k == 0 else max(ilhas[k - 1][1] + 0.01, a - pre)
        b0 = min(ilhas[k + 1][0] - 0.01, b + pos) if k + 1 < len(ilhas) else b + pos
        mapa.append((a0, b0, t))
        partes.append(("s", a0, b0))
        t += b0 - a0
        if k + 1 < len(ilhas):
            natural = ilhas[k + 1][0] - b - pre - pos
            gap = pausas.get(k, min(pausa, max(0.0, natural)))
            partes.append(("g", gap))
            t += gap
    fil, ins = [], []
    for j, p in enumerate(partes):
        if p[0] == "s":
            d = p[2] - p[1]
            fil.append(f"[0:a]atrim={p[1]:.3f}:{p[2]:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,"
                       f"afade=t=out:st={max(0, d - 0.02):.3f}:d=0.02[x{j}]")
        else:
            fil.append(f"anullsrc=r=48000:cl=mono,atrim=0:{p[1]:.3f}[x{j}]")
        ins.append(f"[x{j}]")
    fil.append(f"{''.join(ins)}concat=n={len(ins)}:v=0:a=1[a]")
    grafo = ("[0:a]aresample=48000,aformat=channel_layouts=mono,asplit=" + str(sum(1 for p in partes if p[0] == "s"))
             + "".join(f"[s{j}]" for j, p in enumerate(partes) if p[0] == "s") + ";"
             + ";".join(f.replace("[0:a]", f"[s{j}]", 1) for j, f in enumerate(fil[:-1])) + ";" + fil[-1])
    gf = os.path.splitext(saida)[0] + "_filtro.txt"  # narração longa: o filtro não cabe na linha de comando
    open(gf, "w", encoding="utf-8").write(grafo)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-/filter_complex", gf,
         "-map", "[a]", "-c:a", "pcm_s16le", saida])

    def f(x):
        for a0, b0, novo in mapa:
            if x < b0:
                return round(novo + max(0.0, x - a0), 2)
        return round(t, 2)
    f.total = round(t, 2)
    return f


TIMBRES = {  # personagem = voz modificada (pedido do usuário, 03/11/2026); cada personagem mantém o seu no vídeo inteiro
    "grave": "asetrate=48000*0.84,aresample=48000,atempo=1.19,lowpass=f=5200",          # o amigo
    "aguda": "asetrate=48000*1.2,aresample=48000,atempo=0.8333,highpass=f=180",          # a mãe
    "radio": "highpass=f=480,lowpass=f=2900,acompressor=threshold=-24dB:ratio=6:makeup=4,volume=1.2",  # quem assiste (alto-falante)
    "telefone": "highpass=f=700,lowpass=f=3400,asetrate=48000*1.08,aresample=48000,atempo=0.926,volume=1.3",  # voz de fora
    "robo": "asetrate=48000*0.92,aresample=48000,atempo=1.087,aecho=0.8:0.6:12:0.5,flanger=delay=2:depth=3:speed=0.8",  # voz do sistema
}


def vozes_personagem(src, trechos, saida):
    """Aplica o timbre de cada personagem só nos trechos dele. trechos: [(de, ate, timbre)] em segundos DO ARQUIVO src
    (timbre = chave de TIMBRES ou um filtro ffmpeg). O tempo não muda (atempo compensa o asetrate). Devolve saida."""
    trechos = sorted(trechos)
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                                 capture_output=True, text=True).stdout)
    pedacos, t = [], 0.0
    for a, b, tim in trechos:
        if a > t:
            pedacos.append((t, a, None))
        pedacos.append((a, b, TIMBRES.get(tim, tim)))
        t = b
    if t < total:
        pedacos.append((t, total, None))
    fil = [f"[0:a]aresample=48000,aformat=channel_layouts=mono,asplit={len(pedacos)}" + "".join(f"[s{k}]" for k in range(len(pedacos)))]
    for k, (a, b, f) in enumerate(pedacos):
        d = b - a
        fx = f",{f},apad,atrim=0:{d:.3f}" if f else ""  # o filtro pode encurtar/alongar uns ms: força a mesma duração
        fil.append(f"[s{k}]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS{fx},aformat=channel_layouts=mono[p{k}]")
    fil.append("".join(f"[p{k}]" for k in range(len(pedacos))) + f"concat=n={len(pedacos)}:v=0:a=1[a]")
    gf = os.path.splitext(saida)[0] + "_vozes.txt"
    open(gf, "w", encoding="utf-8").write(";".join(fil))
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-/filter_complex", gf, "-map", "[a]", "-c:a", "pcm_s16le", saida])
    return saida


def legendas_ass(linhas, saida):
    """Escreve o .ass das legendas (tela de referência 1920x1080; o libass escala pro rascunho).
    Cada linha: palavras [(ini, fim, palavra)] no tempo do vídeo; a palavra acende (\\kf) quando é dita."""
    def ts(t):
        t = max(0.0, t)
        return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
    rx, ry = (1920, 1080) if W >= H else (1080, 1920)  # tela em pé (short): referência 1080x1920
    cab = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {rx}\nPlayResY: {ry}\nWrapStyle: 0\n\n"
           "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
           "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
           "Alignment, MarginL, MarginR, MarginV, Encoding\n"
           # dita = amarelo claro, ainda não dita = branco; contorno preto e sombra leve
           "Style: Leg,Segoe UI,58,&H0066E0FF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,4,2,2,160,160,70,1\n\n"
           "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    ev = []
    linhas = sorted(linhas, key=lambda l: l["palavras"][0][0])
    for k, l in enumerate(linhas):
        pw = l["palavras"]
        ini = pw[0][0] - 0.12
        fim = pw[-1][1] + 0.45
        if k + 1 < len(linhas):
            fim = min(fim, linhas[k + 1]["palavras"][0][0] - 0.14)
        fim = max(pw[-1][1], min(fim, l.get("ate", fim)))
        txt, t = "{\\fad(100,140)" + ("\\an8" if l.get("topo") else "") + "}", ini
        for j, (a, b, w) in enumerate(pw):
            if a > t + 0.01:  # espera até a palavra começar
                txt += f"{{\\k{round((a - t) * 100)}}}"
                t = a
            prox = pw[j + 1][0] if j + 1 < len(pw) else b
            txt += f"{{\\kf{max(1, round((max(prox, b) - t) * 100))}}}{w}" + (" " if j + 1 < len(pw) else "")
            t = max(prox, b)
        ev.append(f"Dialogue: 0,{ts(ini)},{ts(fim)},Leg,,0,0,0,,{txt}")
    open(saida, "w", encoding="utf-8-sig").write(cab + "\n".join(ev) + "\n")


def render(narracao, narr_de, narr_ate, narr_em, planos, musica, fim, saida, qualidade="rascunho", voz_fx=None,
           legendas=None, tela=None):
    """narracao: arquivo; usa o trecho narr_de..narr_ate do arquivo, colocado no instante narr_em do vídeo.
    tela=(1080, 1920): vídeo em pé (shorts); por padrão a tela é a da qualidade (16:9).
    voz_fx: [(de, ate)] no tempo do vídeo — reverb de salão na voz só nesses trechos (1–2x por vídeo, quando faz sentido:
    nome de conquista, coral, voz 'na cabeça'). O eco continua um pouco depois de 'ate'."""
    set_quality(qualidade)
    if tela:
        global W, H
        W, H = tela
    work = os.path.dirname(os.path.abspath(saida))
    tmp = os.path.join(work, "_planos_final" if qualidade == "final" else "_planos")
    os.makedirs(tmp, exist_ok=True)
    partes, sfx = [], []
    for i, s in enumerate(planos):
        ate = planos[i + 1]["t"] if i + 1 < len(planos) else fim
        dur = (round(ate * FPS) - round(s["t"] * FPS)) / FPS  # em quadros inteiros da linha do tempo: não acumula atraso
        partes.append(render_plano(i, s, dur, tmp))
        for item in s.get("sfx", []):
            sfx.append((item[0], s["t"] + item[1], item[2], item[3] if len(item) > 3 else None,
                        item[4] if len(item) > 4 else 0.0))  # 5º: de onde começar no arquivo do som
        print(f"plano {i + 1}/{len(planos)}  {dur:.2f}s", flush=True)
    lst = os.path.join(tmp, "lista.txt")
    open(lst, "w").writelines(f"file '{p}'\n" for p in partes)
    video = os.path.join(tmp, "video.mkv")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])

    # narração: limpa o chiado de fundo, nivela e entra no instante narr_em
    ms = int(narr_em * 1000)
    inputs = ["-i", video, "-ss", f"{narr_de:.3f}", "-t", f"{narr_ate - narr_de:.3f}", "-i", narracao]
    # a voz é nivelada SOZINHA antes da mistura (gravação mais baixa não pode ficar abaixo da música)
    fil = [f"[1:a]aresample=48000,aformat=channel_layouts=stereo,afftdn=nf=-40,highpass=f=70,apad=pad_dur=4,"  # apad: o fim do loudnorm atrasa os últimos ~3s; o fim passa a cair no silêncio
           f"loudnorm=I=-16:LRA=7:TP=-2,aresample=48000,"
           f"acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2,adelay={ms}|{ms},apad=whole_dur={fim}[vz]"]
    n = 2
    mus = []
    for f, off, vol, de, ate in musica:
        d = ate - de
        inputs += ["-ss", f"{off:.2f}", "-i", f]
        m = int(de * 1000)
        fil.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{d:.3f},afade=t=in:d=0.3,"
                   f"afade=t=out:st={max(0, d - 0.8):.3f}:d=0.8,volume={vol * gain(f) * 0.75:.3f},adelay={m}|{m}[m{n}]")
        mus.append(f"[m{n}]")
        n += 1
    efe = []
    for f, at, vol, dur, ini in sfx:
        inputs += (["-ss", f"{ini:.2f}"] if ini else []) + ["-i", f]
        m = int(at * 1000)
        corte = f"atrim=0:{dur},afade=t=out:st={max(0, dur - 0.05)}:d=0.05," if dur else ""
        fil.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,"
                   f"silenceremove=start_periods=1:start_threshold=-45dB:start_duration=0.01,asetpts=PTS-STARTPTS,"
                   f"{corte}volume={vol * gain(f) * 0.6:.3f},adelay={m}|{m}[e{n}]")
        efe.append(f"[e{n}]")
        n += 1
    if voz_fx:
        dentro = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in voz_fx)
        fil.append("[vz]asplit=3[v1][v2][vw]")
        fil.append(f"[vw]volume=0:enable='not({dentro})',aecho=0.8:0.85:110|230|370:0.4|0.28|0.18,volume=0.9[rv]")
        efe.append("[rv]")
    else:
        fil.append("[vz]asplit[v1][v2]")
    if mus:
        fil.append(f"{''.join(mus)}amix=inputs={len(mus)}:normalize=0,apad[mu]")
        fil.append("[mu][v2]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=600[md]")  # música bem abaixo da voz
    else:
        fil.append("[v2]anullsink")
        fil.append("anullsrc=r=48000:cl=stereo[md]")
    fil.append(f"[v1][md]{''.join(efe)}amix=inputs={2 + len(efe)}:duration=first:normalize=0,"
               f"atrim=0:{fim},loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000:first_pts=0[a]")  # áudio começa no 0 junto com o vídeo
    gf = os.path.join(tmp, "mix_filtro.txt")
    open(gf, "w", encoding="utf-8").write(";".join(fil))
    mix = os.path.join(tmp, "sem_legenda.mp4") if legendas else saida
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs, "-/filter_complex", gf,
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", mix])
    if legendas:  # queima as legendas num passo separado (no mesmo grafo da mistura de áudio o ffmpeg trava)
        legendas_ass(legendas, os.path.join(tmp, "legendas.ass"))
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-threads", "4", "-i", mix,
                        "-vf", "subtitles=legendas.ass:fontsdir='C\\:/Windows/Fonts'",
                        "-c:v", "libx264", "-preset", PRESET, "-crf", CRF, "-pix_fmt", "yuv420p", "-c:a", "copy",
                        "-movflags", "+faststart", saida],
                       check=True, creationflags=LOW, cwd=tmp)  # cwd: acha o .ass sem caminho com ':'
    json.dump([{"i": i, "inicio": s["t"], "origem": s.get("img") or s.get("clip") or s.get("color")} for i, s in enumerate(planos)],
              open(os.path.splitext(saida)[0] + "_planos.json", "w", encoding="utf-8"), indent=0)
    print(f"PRONTO: {saida}  ({fim:.1f}s, {len(planos)} planos, {W}x{H} {qualidade})")

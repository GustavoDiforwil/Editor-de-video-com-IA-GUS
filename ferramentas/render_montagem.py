"""Renderer do estilo MONTAGEM (kills na batida da música, sem fala, sem som do jogo).

A linha do tempo é a da MÚSICA. Cada plano diz em que instante do vídeo final ele começa ('em')
e qual instante da gameplay deve cair num instante do vídeo final ('ancora'): assim o tiro cai
exatamente na batida, qualquer que seja o corte.

Plano (dict):
  video   : arquivo da gameplay
  em      : início do plano no vídeo final (s). O plano vai até o 'em' do próximo (ou 'fim').
  ancora  : (t_gameplay, t_final) -> o instante t_gameplay aparece em t_final. Padrão: começa em src0.
  src0    : alternativa à âncora: o plano começa nesse instante da gameplay.
  speed   : velocidade (1 normal, 0.4 câmera lenta). A âncora continua valendo.
  z, z2, cx, cy : zoom (inicial/final) e centro 0..1.
  punch   : [(t_final, força)] zoom-soco na batida (sobe e volta em ~0,25 s).
  flash   : [t_final] flash da cor do vídeo (ou [(t, força)]).
  shake   : [t_final] tremida curta.
  bw, dark: preto e branco / escurecido.
  palavras: [(texto, t_ini_final, t_fim_final)] título palavra por batida (grande, centro).
  texto   : [(texto, t_ini, t_fim, y)] texto pequeno.
  tiro    : [t_final] instantes do SFX de tiro (o som de tiro de fora). Ou [(t, nome_sfx, vol)].
  blur_fim: True -> borrão de movimento nos últimos ~0,15 s (transição rápida).
Global (render): cor do flash/grade, letterbox, música, sfx padrão, fade final.
"""
import json
import os
import subprocess

LOW = 0x00004000
FONTE = "C\\:/Windows/Fonts/impact.ttf"


class Q:
    W, H, FPS, CRF, PRESET = 1280, 720, 30, "21", "veryfast"


def set_q(q):
    if q == "final":
        Q.W, Q.H, Q.FPS, Q.CRF, Q.PRESET = 1920, 1080, 60, "17", "medium"
    else:
        Q.W, Q.H, Q.FPS, Q.CRF, Q.PRESET = 1280, 720, 30, "21", "veryfast"


def run(cmd):
    subprocess.run(cmd, check=True, creationflags=LOW)


def esc(p):
    return p.replace("\\", "/").replace(":", "\\:")


def hex_rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def plano(i, s, ini, fim, G, tmp):
    out = os.path.join(tmp, f"m{i:03d}.mkv")
    # quadros inteiros contados do tempo ABSOLUTO (sem deriva acumulada entre planos)
    f0, f1 = round(ini * Q.FPS), round(fim * Q.FPS)
    nfr = f1 - f0
    ini = f0 / Q.FPS
    dur = nfr / Q.FPS
    sp = s.get("speed", 1.0)
    if "ancora" in s:
        tg, tf = s["ancora"]
        a = tg - (tf - ini) * sp
    else:
        a = s["src0"]
    a = max(0.0, a)
    W, H, FPS = Q.W, Q.H, Q.FPS
    rel = lambda t: t - ini  # tempo do vídeo final -> tempo dentro do plano
    v = f"[0:v]setpts=(PTS-STARTPTS)/{sp},fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1"
    # grade única do vídeo (cor do clima da música)
    v += "," + G["grade"]
    # zoom + punch + tremida (zoompan com tempo = on/FPS)
    z, z2 = s.get("z", 1.0), s.get("z2")
    zexp = f"({z}+({(z2 or z) - z})*on/{max(1, int(dur * FPS))})"
    for t, f in s.get("punch", []):
        r = rel(t)
        zexp += f"+{f}*if(gte(on/{FPS},{r:.3f}),exp(-(on/{FPS}-{r:.3f})/0.09),0)"
    sx = sy = ""
    for t in s.get("shake", []):
        r = rel(t)
        env = f"if(gte(on/{FPS},{r:.3f}),exp(-(on/{FPS}-{r:.3f})/0.12),0)"
        sx += f"+{int(0.018 * W)}*{env}*sin(on*2.7)"
        sy += f"+{int(0.018 * H)}*{env}*cos(on*2.1)"
    if z2 is not None or z != 1.0 or s.get("punch") or s.get("shake"):
        if s.get("shake"):
            zexp = f"max({zexp},1.06)"
        cx, cy = s.get("cx", 0.5), s.get("cy", 0.5)
        v += (f",scale={int(W * 1.5)}:{int(H * 1.5)}:flags=bicubic,zoompan=z='{zexp}':d=1:s={W}x{H}:fps={FPS}:"
              f"x='clip((iw-iw/zoom)*{cx}{sx},0,iw-iw/zoom)':y='clip((ih-ih/zoom)*{cy}{sy},0,ih-ih/zoom)'")
    if s.get("bw"):
        v += ",hue=s=0"
    if s.get("dark"):
        v += ",eq=brightness=-0.15:contrast=0.95"
    if s.get("blur_fim"):
        b0 = max(0, dur - 0.15)
        v += f",split[bA][bB];[bB]tmix=frames=5[bC];[bA][bC]overlay=enable='gte(t,{b0:.3f})'"
    v += "[base]"
    # flash na cor do vídeo
    inputs = ["-ss", f"{a:.3f}", "-t", f"{dur * sp + 0.5:.3f}", "-an", "-i", s["video"]]
    fl = s.get("flash", [])
    if fl:
        r_, g_, b_ = hex_rgb(G["cor"])
        inputs += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"color=c=0x{G['cor'].lstrip('#')}:s={W}x{H}:r={FPS}"]
        ks = []
        for x in fl:
            t, f = (x, 0.5) if not isinstance(x, (tuple, list)) else x
            r = rel(t)
            ks.append(f"{f}*if(gte(T,{r:.3f}),exp(-(T-{r:.3f})/0.10),0)")
        k = "min(1," + "+".join(ks) + ")"
        v += f";[1:v]format=yuv420p,setsar=1[cor];[base][cor]blend=all_expr='A+(B-A)*{k}'[base]"
    # letterbox
    if G.get("letterbox"):
        lb = int(H * G["letterbox"])
        v += f";[base]drawbox=x=0:y=0:w=iw:h={lb}:c=black:t=fill,drawbox=x=0:y=ih-{lb}:w=iw:h={lb}:c=black:t=fill[base]"
    # textos
    chain = "[base]null"
    for k, (txt, t0, t1) in enumerate(s.get("palavras", [])):
        tf = os.path.join(tmp, f"w{i:03d}_{k}.txt")
        open(tf, "w", encoding="utf-8").write(txt)
        a0, a1 = rel(t0), rel(t1)
        fs = int(H * 0.16)
        chain += (f",drawtext=fontfile='{FONTE}':textfile='{esc(tf)}':fontsize={fs}:fontcolor=white:"
                  f"shadowcolor=0x{G['cor'].lstrip('#')}@0.9:shadowx={int(H*0.006)}:shadowy={int(H*0.006)}:"
                  f"x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,{a0:.3f},{a1:.3f})'")
    for k, (txt, t0, t1, y) in enumerate(s.get("texto", [])):
        tf = os.path.join(tmp, f"t{i:03d}_{k}.txt")
        open(tf, "w", encoding="utf-8").write(txt)
        a0, a1 = rel(t0), rel(t1)
        fs = int(H * 0.05)
        chain += (f",drawtext=fontfile='{FONTE}':textfile='{esc(tf)}':fontsize={fs}:fontcolor=white@0.95:"
                  f"x=(w-text_w)/2:y=h*{y}-text_h/2:enable='between(t,{a0:.3f},{a1:.3f})'")
    v += ";" + chain + f",trim=end_frame={nfr},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop={nfr}[v]"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-threads", "4", *inputs,
         "-filter_complex", v, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", Q.PRESET, "-crf", Q.CRF,
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-frames:v", str(nfr), out])
    return out


def render(planos, G, workdir, saida, qualidade="rascunho", so=None):
    """G: {cor, grade, letterbox, musica, musica_ini, fim, sfx_dir, sfx, sfx_vol, fade_fim}
    so: lista de índices para renderizar só alguns planos (teste rápido; reaproveita os outros)."""
    set_q(qualidade)
    tmp = os.path.join(workdir, "_mont_final" if qualidade == "final" else "_mont")
    os.makedirs(tmp, exist_ok=True)
    fim_total = G["fim"]
    partes = []
    for i, s in enumerate(planos):
        ini = s["em"]
        fim = planos[i + 1]["em"] if i + 1 < len(planos) else fim_total
        assert fim > ini, f"plano {i}: fim <= início"
        p = os.path.join(tmp, f"m{i:03d}.mkv")
        if so is None or i in so or not os.path.exists(p):
            plano(i, s, ini, fim, G, tmp)
        partes.append(p)
        print(f"plano {i + 1}/{len(planos)}  {ini:.2f}-{fim:.2f}", flush=True)
    lst = os.path.join(tmp, "lista.txt")
    open(lst, "w").writelines(f"file '{p}'\n" for p in partes)
    video = os.path.join(tmp, "video.mkv")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])

    # áudio: música inteira + SFX de tiro de fora (nada do som do jogo)
    tiros = []
    for s in planos:
        for x in s.get("tiro", []):
            t, nome, vol = (x, G["sfx"], G.get("sfx_vol", 0.8)) if not isinstance(x, (tuple, list)) else x
            tiros.append((t, nome, vol))
    inputs = ["-i", video, "-ss", f"{G.get('musica_ini', 0):.3f}", "-i", G["musica"]]
    fil = [f"[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{fim_total:.3f},volume={G.get('musica_vol', 1.0)}"
           + (f",afade=t=out:st={fim_total - G['fade_fim']:.3f}:d={G['fade_fim']:.3f}" if G.get("fade_fim") else "") + "[mus]"]
    mix = "[mus]"
    for k, (t, nome, vol) in enumerate(tiros):
        inputs += ["-i", os.path.join(G["sfx_dir"], nome + ".wav")]
        ms = max(0, int(round(t * 1000)))
        fil.append(f"[{k + 2}:a]aresample=48000,aformat=channel_layouts=stereo,"
                   f"silenceremove=start_periods=1:start_threshold=-40dB:start_duration=0.005,"
                   f"volume={vol},adelay={ms}|{ms}[s{k}]")
        mix += f"[s{k}]"
    fil.append(f"{mix}amix=inputs={len(tiros) + 1}:duration=first:normalize=0,"
               f"alimiter=limit=0.95,loudnorm=I=-14:TP=-1:LRA=11,aresample=48000[a]")
    vf = []
    if G.get("fade_fim"):
        vf = ["-vf", f"fade=t=out:st={fim_total - G['fade_fim']:.3f}:d={G['fade_fim']:.3f}"]
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(fil),
         "-map", "0:v", "-map", "[a]", *vf,
         *(["-c:v", "libx264", "-preset", Q.PRESET, "-crf", Q.CRF, "-pix_fmt", "yuv420p"] if vf else ["-c:v", "copy"]),
         "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", saida])
    json.dump([{"i": i, "inicio": s["em"], "video": os.path.basename(s["video"]),
                "origem": s.get("ancora") or s.get("src0")} for i, s in enumerate(planos)],
              open(os.path.splitext(saida)[0] + "_planos.json", "w"), indent=0)
    print(f"PRONTO: {saida}  ({fim_total:.1f}s, {len(planos)} planos, {len(tiros)} tiros, {Q.W}x{Q.H}@{Q.FPS} {qualidade})")

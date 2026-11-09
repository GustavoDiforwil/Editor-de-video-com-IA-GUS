"""Editor por planos curtos (estilo Rik: 1 corte a cada ~1-2s).

Cada plano (dict):
  src    : (a, b) trecho do vídeo original em segundos absolutos
  video  : (opcional) outro arquivo de origem para este plano (vários vídeos num só projeto)
  freeze : (t, dur) congela o quadro t por dur segundos (sem áudio original)
  vfreeze: t — junto com src: usa o ÁUDIO de src sobre a IMAGEM congelada do instante t
           (ex.: fala que aconteceu numa tela de loading, posta sobre o frame da explosão)
  img    : nome do PNG em IMAGENS (insert em tela cheia com fundo 'bg'), com 'dur'
Opções de visual:
  z (zoom, 1=normal), z2 (zoom final, para zoom lento), cx/cy (centro do zoom 0..1),
  bw (preto e branco), shake (tremida), text (figurinha pequena), tx/ty (posição 0..1),
  png / px / py / ps (emoji/imagem por cima: posição 0..1 e largura em px)
Áudio: sfx=[(nome, atraso, volume)], vol (volume do áudio original)
Música (camada separada): music=(arquivo, inicio_no_arquivo, volume) começa neste plano;
  music_stop=True corta a música no início deste plano.
"""
import json
import os
import re
import subprocess

LOW = 0x00004000
FONT = next(f for f in ("C\\:/Windows/Fonts/ariblk.ttf", "C\\:/Windows/Fonts/impact.ttf")
            if os.path.exists(f.replace("\\:", ":")))
W, H, FPS = 1280, 720, 30
# qualidade: "rascunho" (rápido, p/ revisar) ou "final" (1080p, p/ entregar). Tamanhos em px são para 720p × K.
K, CRF, PRESET, PRE = 1.0, "21", "veryfast", (1920, 1080)


def set_quality(q):
    global W, H, K, CRF, PRESET, PRE
    if q == "final":
        W, H, K, CRF, PRESET, PRE = 1920, 1080, 1.5, "17", "medium", (2880, 1620)
    else:
        W, H, K, CRF, PRESET, PRE = 1280, 720, 1.0, "21", "veryfast", (1920, 1080)
CHAT_FONT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts", "BebasNeue-Regular.ttf").replace("\\", "/").replace(":", "\\:")  # fonte condensada parecida com a do R.E.P.O.


def run(cmd):
    subprocess.run(cmd, check=True, creationflags=LOW)


_LEVELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "niveis.json")
_cache = json.load(open(_LEVELS)) if os.path.exists(_LEVELS) else {}


def gain(path, target=-20.0):
    """Fator que leva o volume médio do arquivo a 'target' dB (cache em niveis.json)."""
    if path not in _cache:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                           capture_output=True, text=True, creationflags=LOW)
        m = re.search(r"mean_volume: (-?[\d.]+) dB", r.stderr)
        _cache[path] = float(m.group(1)) if m else target
        json.dump(_cache, open(_LEVELS, "w"), indent=0)
    db = max(-15.0, min(15.0, target - _cache[path]))
    return round(10 ** (db / 20), 3)


def esc(p):
    return p.replace("\\", "/").replace(":", "\\:")


def render_shot(i, s, src, sons, imagens, tmp):
    # .mkv com áudio PCM: emendar 100+ planos sem o atraso acumulado do AAC (priming de ~21ms por arquivo)
    out = os.path.join(tmp, f"p{i:03d}.mkv")
    src = s.get("video", src)
    inputs, vchain, achain = [], "", ""
    if "src" in s and s.get("speed"):  # time-lapse: acelera o vídeo, áudio original some
        a, b = s["src"]
        sp = s["speed"]
        dur = (b - a) / sp
        inputs += ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", src,
                   "-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        vchain = f"[0:v]setpts=PTS/{sp},fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1"
        achain = "[1:a]anull[a0]"
    elif "src" in s and s.get("vfreeze") is not None:  # áudio do trecho src sobre a IMAGEM congelada do instante vfreeze
        a, b = s["src"]
        dur = b - a
        inputs += ["-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", src,
                   "-ss", f"{s['vfreeze']:.3f}", "-t", "0.1", "-i", src]
        vchain = (f"[1:v]fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,trim=end_frame=1,"
                  f"tpad=stop_mode=clone:stop_duration={dur:.3f}")
        achain = (f"[0:a]aresample=48000,volume={s.get('vol', 1.0)},"
                  f"afade=t=in:d=0.015,afade=t=out:st={max(0, dur - 0.02):.3f}:d=0.02[a0]")
    elif "src" in s:
        a, b = s["src"]
        dur = b - a
        inputs += ["-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", src]
        vchain = f"[0:v]fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1"
        achain = (f"[0:a]aresample=48000,volume={s.get('vol', 1.0)},"
                  f"afade=t=in:d=0.015,afade=t=out:st={max(0, dur - 0.02):.3f}:d=0.02[a0]")
    elif "freeze" in s:
        t, dur = s["freeze"]
        inputs += ["-ss", f"{t:.3f}", "-t", "0.1", "-i", src,
                   "-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        vchain = (f"[0:v]fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,trim=end_frame=1,"
                  f"tpad=stop_mode=clone:stop_duration={dur:.3f}")
        achain = "[1:a]anull[a0]"
    elif "color" in s:  # vinheta de cor sólida (ex.: contador do Capiche)
        dur = s["dur"]
        inputs += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"color=c={s['color']}:s={W}x{H}:r={FPS}",
                   "-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        vchain = "[0:v]setsar=1"
        achain = "[1:a]anull[a0]"
    else:  # img
        dur = s["dur"]
        inputs += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"color=c={s.get('bg', 'white')}:s={W}x{H}:r={FPS}",
                   "-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
                   "-loop", "1", "-t", f"{dur:.3f}", "-i", os.path.join(imagens, s["img"] + ".png")]
        vchain = f"[2:v]scale={int(s.get('ps', 460) * K)}:-1[im];[0:v][im]overlay=(W-w)/2:(H-h)/2,setsar=1"
        achain = "[1:a]anull[a0]"

    # zoom / tremida / preto e branco
    z, z2 = s.get("z", 1.0), s.get("z2")
    cx, cy = s.get("cx", 0.5), s.get("cy", 0.5)
    if z2 is not None or z != 1.0 or s.get("shake"):
        # zoompan: zoom por quadro ('on' = nº do quadro de saída), centro em cx/cy, tremida opcional
        nfr = max(1, int(dur * FPS))
        z0 = max(z, 1.08) if s.get("shake") else z
        zexpr = f"{z0}+({(z2 or z0) - z0})*on/{nfr}" if z2 is not None else f"{z0}"
        sx = f"+{22 * K:.0f}*sin(on*2.1)" if s.get("shake") else ""
        sy = f"+{16 * K:.0f}*cos(on*1.7)" if s.get("shake") else ""
        vchain += (f",scale={PRE[0]}:{PRE[1]}:flags=lanczos,zoompan=z='{zexpr}':d=1:s={W}x{H}:fps={FPS}:"
                   f"x='clip((iw-iw/zoom)*{cx}{sx},0,iw-iw/zoom)':y='clip((ih-ih/zoom)*{cy}{sy},0,ih-ih/zoom)'")
    if s.get("lowfps"):  # estética "travadinha" (posterize time do Rik)
        vchain += f",fps={s['lowfps']},fps={FPS}"
    if s.get("bw"):
        vchain += ",hue=s=0"
    if s.get("dark"):
        vchain += ",eq=brightness=-0.22:contrast=0.9"

    n_in = len([x for x in inputs if x == "-i"])
    if s.get("png"):
        inputs += ["-loop", "1", "-t", f"{dur:.3f}", "-i", os.path.join(imagens, s["png"] + ".png")]
        ps = s.get("ps2", s.get("ps", 220)) if "img" in s else s.get("ps", 220)
        px, py = s.get("px", 0.78), s.get("py", 0.55)
        vchain += (f"[base];[{n_in}:v]scale={int(ps * K)}:-1[pg];[base][pg]overlay="
                   f"x='{W}*{px}-w/2':y='{H}*{py}-h/2'")
        n_in += 1
    if s.get("text"):
        tf = os.path.join(tmp, f"t{i:03d}.txt")
        open(tf, "w", encoding="utf-8").write(s["text"])
        tx, ty = s.get("tx", 0.5), s.get("ty", 0.82)
        vchain += (f",drawtext=fontfile='{FONT}':textfile='{esc(tf)}':fontsize={int(s.get('fs', 40) * K)}:"
                   f"fontcolor=white:borderw={int(4 * K)}:bordercolor=black:x=w*{tx}-text_w/2:y=h*{ty}-text_h/2")
    # falas estilo chat do jogo: palavras soltas que aparecem no instante em que são ditas
    base_t = s["src"][0] if "src" in s else 0.0
    words = s.get("words", [])
    for k, (txt, at) in enumerate(words):
        a_rel = max(0.0, at - base_t)
        b_rel = (words[k + 1][1] - base_t) if k + 1 < len(words) else dur
        tf = os.path.join(tmp, f"w{i:03d}_{k}.txt")
        open(tf, "w", encoding="utf-8").write(txt)
        vchain += (f",drawtext=fontfile='{CHAT_FONT}':textfile='{esc(tf)}':fontsize={int(s.get('wfs', 58) * K)}:"
                   f"fontcolor=white:borderw={int(2 * K)}:bordercolor=black@0.8:shadowx={int(3 * K)}:shadowy={int(3 * K)}:shadowcolor=black@0.6:"
                   f"x=w*{s.get('wx', 0.5)}-text_w/2:y=h*{s.get('wy', 0.42)}-text_h/2:"
                   f"enable='between(t,{a_rel:.2f},{b_rel:.2f})'")
    # cartela: texto grande centralizado (várias linhas)
    if s.get("card"):
        lines = s["card"].split("\n")
        fs = int(s.get("cfs", 92) * K)
        for k, line in enumerate(lines):
            tf = os.path.join(tmp, f"c{i:03d}_{k}.txt")
            open(tf, "w", encoding="utf-8").write(line)
            off = (k - (len(lines) - 1) / 2) * fs * 0.95  # linhas coladas, bloco centralizado
            vchain += (f",drawtext=fontfile='{CHAT_FONT}':textfile='{esc(tf)}':fontsize={fs}:"
                       f"fontcolor={s.get('ccolor', 'white')}:borderw={int(3 * K)}:bordercolor=black@0.7:"
                       f"x=(w-text_w)/2:y=h/2+{off:.0f}-{fs * 0.4:.0f}")
    vchain += "[v]"

    mix, n = "[a0]", 1
    for name, delay, vol in s.get("sfx", []):
        path = os.path.join(sons, name + ".mp3")
        inputs += ["-i", path]
        ms = int(delay * 1000)
        # corta o silêncio do começo do arquivo (sons do myinstants vêm com "respiro") p/ cair no tempo certo
        achain += (f";[{n_in}:a]aresample=48000,aformat=channel_layouts=stereo,"
                   f"silenceremove=start_periods=1:start_threshold=-45dB:start_duration=0.01,"
                   f"adelay={ms}|{ms},volume={vol * gain(path):.3f}[s{n}]")
        mix += f"[s{n}]"
        n += 1
        n_in += 1
    achain += (f";[a0]aformat=channel_layouts=stereo[a0s]" if n == 1 else "")
    if n == 1:
        achain += ";[a0s]alimiter=limit=0.9[a]"
    else:
        achain += f";{mix}amix=inputs={n}:duration=first:normalize=0,alimiter=limit=0.9[a]"

    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-threads", "4", *inputs,
         "-filter_complex", vchain + ";" + achain, "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", PRESET, "-crf", CRF, "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", out])
    return out, dur


def render(src, shots, sons, imagens, workdir, final, qualidade="rascunho"):
    """qualidade: "rascunho" (720p rápido, para revisar) ou "final" (1080p, lanczos, crf 17 — para entregar)."""
    set_quality(qualidade)
    tmp = os.path.join(workdir, "_shots_final" if qualidade == "final" else "_shots")
    os.makedirs(tmp, exist_ok=True)
    for old in os.listdir(tmp):  # não misturar planos de um render anterior
        if old.startswith("p") and old.endswith(".mkv"):
            os.remove(os.path.join(tmp, old))
    parts, starts, t = [], [], 0.0
    for i, s in enumerate(shots):
        p, d = render_shot(i, s, src, sons, imagens, tmp)
        parts.append(p)
        starts.append(t)
        t += d
        print(f"plano {i+1}/{len(shots)}  {d:.2f}s", flush=True)
    total = t
    lst = os.path.join(tmp, "lista.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    voz = os.path.join(tmp, "voz.mkv")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", voz])

    # camada de música: cada deixa vai até a próxima deixa ou um music_stop
    cues = []
    for i, s in enumerate(shots):
        if s.get("music_stop") and cues and cues[-1][4] is None:
            cues[-1][4] = starts[i]
        if s.get("music"):
            if cues and cues[-1][4] is None:
                cues[-1][4] = starts[i]
            f, off, vol = s["music"]
            cues.append([f, off, vol, starts[i], None])
    if cues and cues[-1][4] is None:
        cues[-1][4] = total
    # fala/jogo nivelada (gritos e falas baixas mais próximos); música abaixa sozinha sob a fala
    inputs = ["-i", voz]
    fil = ["[0:a]dynaudnorm=f=250:g=15:p=0.9:m=5:s=8,"
           "acompressor=threshold=-16dB:ratio=4:attack=5:release=150:makeup=1.5[vz]"]
    mus = ""
    for k, (f, off, vol, a, b) in enumerate(cues, start=1):
        d = b - a
        inputs += ["-ss", f"{off:.2f}", "-i", f]
        ms = int(a * 1000)
        fil.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{d:.3f},"
                   f"afade=t=out:st={max(0, d - 0.03):.3f}:d=0.03,volume={vol * gain(f):.3f},adelay={ms}|{ms}[m{k}]")
        mus += f"[m{k}]"
    if cues:
        fil.append(f"{mus}amix=inputs={len(cues)}:normalize=0,apad[mus]")
        fil.append("[vz]asplit[v1][v2]")
        fil.append("[mus][v2]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=350[md]")
        fil.append("[v1][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[a]")
    else:
        fil.append("[vz]loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[a]")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(fil),
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", final])
    # lista de planos (início/duração no vídeo final e origem) para a conferência em qualidade cheia
    planos = [{"i": i, "inicio": round(starts[i], 3), "dur": round((starts[i + 1] if i + 1 < len(starts) else total) - starts[i], 3),
               "origem": s.get("src") or s.get("freeze") or s.get("color") or s.get("img")} for i, s in enumerate(shots)]
    json.dump(planos, open(os.path.splitext(final)[0] + "_planos.json", "w", encoding="utf-8"), indent=0)
    print(f"PRONTO: {final}  ({total:.1f}s, {len(shots)} planos, {len(cues)} trilhas, {W}x{H} {qualidade})")

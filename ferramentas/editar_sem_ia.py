"""Modo SEM IA: edição automática básica, de graça e offline (não precisa de Claude nem de Gemini).

O que faz:
  1. transcreve o vídeo com o Whisper (tempo de cada palavra);
  2. mantém só os trechos com fala (com uma folga antes e depois) e corta as pausas longas e o tempo morto;
  3. renderiza com o render_shots.py: volume nivelado e, se você passar uma música, ela abaixa sozinha quando alguém fala;
  4. salva a transcrição em texto e um resumo do que foi cortado (e, se pedir, as folhas de frames), pra você terminar à mão.

O que NÃO faz: entender piada, montar história, zoom, efeitos. Pra isso, use o modo com IA.

uso: python editar_sem_ia.py VIDEO [--musica ARQ] [--pausa-max 1.5] [--antes 0.3] [--depois 0.5] [--final] [--folhas]
  --pausa-max : pausas maiores que isso (s) são cortadas (padrão 1.5)
  --antes/--depois : folga mantida antes/depois de cada fala (s)
  --final     : render 1080p (padrão: rascunho 720p, mais rápido)
  --folhas    : também gera folhas de frames (1 por segundo) pra revisar
Tudo vai pra projetos/<nome-do-video>/ (o vídeo original não é mexido).
"""
import argparse
import ctypes
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from render_shots import render  # noqa: E402

LOW = 0x00004000
if os.name == "nt":
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), LOW)


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, creationflags=LOW, **kw)


def duracao(arq):
    r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq], capture_output=True, text=True)
    return float(r.stdout.strip())


def tem_audio(arq):
    r = sh(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", arq],
           capture_output=True, text=True)
    return bool(r.stdout.strip())


def trechos_com_fala(palavras, total, pausa_max, antes, depois, minimo=1.2):
    """Agrupa as palavras em trechos: pausa entre palavras > pausa_max = corte."""
    if not palavras:
        return []
    grupos, ini, fim = [], palavras[0][0], palavras[0][1]
    for a, b in palavras[1:]:
        if a - fim > pausa_max:
            grupos.append((ini, fim))
            ini = a
        fim = max(fim, b)
    grupos.append((ini, fim))
    out = []
    for a, b in grupos:
        a, b = max(0.0, a - antes), min(total, b + depois)
        if b - a < minimo:  # fala muito curta: estica pra dar tempo de entender
            falta = minimo - (b - a)
            a, b = max(0.0, a - falta / 2), min(total, b + falta / 2)
        if out and a <= out[-1][1] + 0.05:  # encostou no anterior: junta
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def main():
    ap = argparse.ArgumentParser(description="Edição automática básica, sem IA.")
    ap.add_argument("video")
    ap.add_argument("--musica", default="")
    ap.add_argument("--pausa-max", type=float, default=1.5)
    ap.add_argument("--antes", type=float, default=0.3)
    ap.add_argument("--depois", type=float, default=0.5)
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--folhas", action="store_true")
    o = ap.parse_args()

    video = os.path.abspath(o.video.strip('"'))
    if not os.path.exists(video):
        sys.exit(f"Não achei o vídeo: {video}")
    if not tem_audio(video):
        sys.exit("Esse vídeo não tem áudio: o modo sem IA corta pelas falas, então precisa de som.")
    musica = os.path.abspath(o.musica.strip('"')) if o.musica.strip('"') else ""
    if musica and not os.path.exists(musica):
        sys.exit(f"Não achei a música: {musica}")

    nome = os.path.splitext(os.path.basename(video))[0]
    proj = os.path.join(RAIZ, "projetos", nome)
    os.makedirs(os.path.join(proj, "render"), exist_ok=True)
    total = duracao(video)
    print(f"Vídeo: {nome} ({total / 60:.1f} min) -> projetos/{nome}/")

    # 1. áudio 16 kHz + transcrição (retoma se cair)
    wav = os.path.join(proj, "audio16k.wav")
    if not os.path.exists(wav):
        print("[1/4] Extraindo o áudio...")
        sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-vn", "-ac", "1", "-ar", "16000", wav])
    tj = os.path.join(proj, "transcricao.jsonl")
    print("[2/4] Transcrevendo (na primeira vez o Whisper baixa o modelo, ~480 MB)...")
    sh([sys.executable, os.path.join(AQUI, "transcribe_range.py"), wav, tj, "0", f"{total:.2f}"])
    sh([sys.executable, os.path.join(AQUI, "dump_transcript.py"), tj, os.path.join(proj, "transcricao.txt")])

    palavras = []
    for linha in open(tj, encoding="utf-8"):
        if linha.strip():
            for s in json.loads(linha)["segs"]:
                palavras += [(w[0], w[1]) for w in s["words"]]
    palavras.sort()
    trechos = trechos_com_fala(palavras, total, o.pausa_max, o.antes, o.depois)
    if not trechos:
        sys.exit("Não achei fala nenhuma nesse vídeo. O modo sem IA corta pelas falas; pra vídeo sem fala, use o modo com IA.")
    mantido = sum(b - a for a, b in trechos)
    print(f"[3/4] {len(trechos)} trechos com fala: {total / 60:.1f} min -> {mantido / 60:.1f} min "
          f"(cortou {100 - mantido / total * 100:.0f}%)")

    # 2. planos (+ música que recomeça quando acaba)
    planos = [{"src": (round(a, 3), round(b, 3))} for a, b in trechos]
    if musica:
        dm, t, ini = duracao(musica), 0.0, 0.0
        for p in planos:
            if p is planos[0] or t - ini >= dm - 1:
                p["music"] = (musica, 0.0, 0.35)
                ini = t
            t += p["src"][1] - p["src"][0]

    qual = "final" if o.final else "rascunho"
    saida = os.path.join(proj, "render", f"{nome}_sem_ia_{qual}.mp4")
    print(f"[4/4] Renderizando ({'1080p' if o.final else '720p, rascunho'})...")
    render(video, planos, os.path.join(RAIZ, "assets", "sons"), os.path.join(RAIZ, "assets"), proj, saida, qualidade=qual)

    with open(os.path.join(proj, "resumo_sem_ia.txt"), "w", encoding="utf-8") as f:
        f.write(f"Vídeo original: {video}\nDuração: {total / 60:.1f} min -> {mantido / 60:.1f} min\n"
                f"Pausa máxima: {o.pausa_max}s | folga: {o.antes}s antes, {o.depois}s depois\n\nTrechos mantidos:\n")
        for i, (a, b) in enumerate(trechos, 1):
            f.write(f"{i:4d}  {int(a // 60):02d}:{a % 60:05.2f} -> {int(b // 60):02d}:{b % 60:05.2f}  ({b - a:.1f}s)\n")

    if o.folhas:
        pasta = os.path.join(proj, "folhas")
        os.makedirs(pasta, exist_ok=True)
        print("Gerando folhas de frames (1 por segundo)...")
        sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-threads", "2", "-i", video, "-an", "-vf",
            "fps=1,scale=320:-2,drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='%{pts\\:hms}':fontsize=18:"
            "fontcolor=yellow:box=1:boxcolor=black@0.6:x=4:y=4,tile=6x5", "-q:v", "4", os.path.join(pasta, "f%04d.jpg")])

    print(f"\nPRONTO: {saida}\nTranscrição: projetos/{nome}/transcricao.txt | resumo: projetos/{nome}/resumo_sem_ia.txt")


if __name__ == "__main__":
    main()

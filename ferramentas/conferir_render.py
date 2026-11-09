"""Conferência em qualidade cheia: 1 frame do MEIO de cada plano do vídeo renderizado, na resolução dele,
montados em folhas 2x2 (cada quadro com o nº do plano e o tempo). Serve para checar zoom no lugar certo,
texto legível e nada cortado — só dos trechos que de fato foram usados.

Uso: conferir_render.py video_final.mp4 [pasta_saida]
Precisa do arquivo video_final_planos.json (o render_shots.py gera automaticamente).
"""
import ctypes
import json
import os
import subprocess
import sys

if os.name == "nt":
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)

video = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(video)[0] + "_conferencia"
os.makedirs(out, exist_ok=True)
planos = json.load(open(os.path.splitext(video)[0] + "_planos.json", encoding="utf-8"))
FONT = "C\\:/Windows/Fonts/arial.ttf"

frames = []
for p in planos:
    t = p["inicio"] + p["dur"] / 2
    f = os.path.join(out, f"plano_{p['i']:03d}.png")
    label = f"plano {p['i']}  {int(t // 60)}\\:{t % 60:04.1f}"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", video,
                    "-frames:v", "1", "-vf",
                    f"drawtext=fontfile='{FONT}':text='{label}':fontsize=36:fontcolor=yellow:box=1:boxcolor=black@0.6:x=12:y=12",
                    f], check=True)
    frames.append(f)

# folhas 2x2 (4 planos por folha, mantendo a resolução de cada quadro)
for k in range(0, len(frames), 4):
    grupo = frames[k:k + 4]
    while len(grupo) < 4:
        grupo.append(grupo[-1])
    args = sum((["-i", g] for g in grupo), [])
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args, "-filter_complex",
                    "[0][1]hstack[a];[2][3]hstack[b];[a][b]vstack", "-q:v", "3",
                    os.path.join(out, f"folha_{k // 4 + 1:03d}.jpg")], check=True)
for f in frames:
    os.remove(f)
print(f"ok: {len(planos)} planos em {(len(planos) + 3) // 4} folhas -> {out}")

"""Gera uma folha de frames (1 a cada 2s, com timestamp) para cada janela candidata.

Uso: frames_windows.py video.mp4 cands.json pasta_saida PRE POST
"""
import json
import os
import subprocess
import sys

video, cands_path, out, pre, post = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
os.makedirs(out, exist_ok=True)
cands = sorted(json.load(open(cands_path, encoding="utf-8-sig")), key=lambda c: c["t"])
FONT = "C\\:/Windows/Fonts/arial.ttf"

for i, c in enumerate(cands):
    a = max(0.0, c["t"] - pre)
    dst = os.path.join(out, f"{int(c['t'])}.jpg")
    if os.path.exists(dst):
        continue
    # pts do clipe + início = tempo absoluto no vídeo original, desenhado em cada quadro
    vf = (f"fps=0.5,scale=320:-2,"
          f"drawtext=fontfile='{FONT}':text='%{{pts\\:hms\\:{a:.2f}}}':fontsize=18:fontcolor=yellow:"
          f"box=1:boxcolor=black@0.6:x=4:y=4,tile=5x4")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-threads", "2",
                    "-ss", f"{a:.2f}", "-t", str(pre + post), "-i", video,
                    "-vf", vf, "-frames:v", "1", "-q:v", "4", dst],
                   check=True, creationflags=0x4000)
    print(f"[{i+1}/{len(cands)}] {dst}", flush=True)
print("FIM")

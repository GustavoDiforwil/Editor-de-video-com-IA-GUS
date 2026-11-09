"""Tiras de conferência de kills (achar o quadro exato do disparo).

uso: python tiras_kill.py video.mp4 tempos.json pasta_saida [antes=1.0] [depois=0.2] [fps=15]
tempos.json: lista de instantes (ou dicts com 'pop'/'tiro'). Cada instante vira UMA linha: quadros de
t-antes até t+depois, recortando o centro-topo da tela (medalha + mira), com o tempo exato em cada quadro.
Folhas de 8 linhas: folha_XX.jpg. O tiro = 1 quadro antes da medalha/recuo aparecer.
"""
import json
import os
import subprocess
import sys

LOW = 0x00004000


def main():
    v, kp, out = sys.argv[1:4]
    antes = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    depois = float(sys.argv[5]) if len(sys.argv) > 5 else 0.2
    fps = int(sys.argv[6]) if len(sys.argv) > 6 else 15
    os.makedirs(out, exist_ok=True)
    L = json.load(open(kp))
    ts = [x if isinstance(x, (int, float)) else x.get("pop", x.get("tiro")) for x in L]
    n = int(round((antes + depois) * fps))
    rows = []
    for t in ts:
        p = os.path.join(out, f"r_{t:08.2f}.jpg")
        a = max(0, t - antes)
        if not os.path.exists(p):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-threads", "2", "-ss", f"{a:.3f}", "-i", v,
                            "-t", f"{antes + depois:.3f}",
                            "-vf", f"fps={fps},crop=iw*0.5:ih*0.62:iw*0.25:0,scale=190:-2,"
                                   f"drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='%{{pts\\:flt\\:{a:.3f}}}':"
                                   f"fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.8:x=2:y=2,tile={n}x1",
                            "-frames:v", "1", p], check=True, creationflags=LOW)
        rows.append(p)
    for k in range(0, len(rows), 8):
        g = rows[k:k + 8]
        args = sum((["-i", p] for p in g), [])
        f = "".join(f"[{i}:v]" for i in range(len(g))) + f"vstack=inputs={len(g)}" if len(g) > 1 else "null"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", f, "-q:v", "3",
                        os.path.join(out, f"folha_{k // 8 + 1:02d}.jpg")], check=True, creationflags=LOW)
    print(f"{len(rows)} linhas -> {(len(rows) + 7) // 8} folhas em {out}")


if __name__ == "__main__":
    main()

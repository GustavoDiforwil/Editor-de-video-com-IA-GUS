"""Conferência de uma montagem renderizada: para cada plano, 4 quadros (início, tiro-0,13, tiro+0,10, fim).
Sem tiro: início, 1/3, 2/3, fim. 8 planos por folha. Serve para ver: plano caindo em killcam/menu/webcam,
corte da fonte (compilação) no meio da mira, kill legível no tiro.

uso: python conferir_montagem.py edl.py video.mp4 pasta_saida
"""
import importlib.util
import os
import subprocess
import sys

LOW = 0x00004000


def main():
    edl, v, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    spec = importlib.util.spec_from_file_location("edl", edl)
    m = importlib.util.module_from_spec(spec)
    sys.argv = [edl]
    spec.loader.exec_module(m)
    S, fim = m.S, m.G["fim"]
    linhas = []
    for i, s in enumerate(S):
        a = s["em"]
        b = S[i + 1]["em"] if i + 1 < len(S) else fim
        tiros = [x if not isinstance(x, (list, tuple)) else x[0] for x in s.get("tiro", [])]
        if tiros:
            t = tiros[0]
            ts = [a + 0.04, max(a + 0.04, t - 0.13), min(b - 0.04, t + 0.10), b - 0.05]
        else:
            ts = [a + 0.04, a + (b - a) / 3, a + 2 * (b - a) / 3, b - 0.05]
        ts = [min(t, fim - 0.3) for t in ts]
        p = os.path.join(out, f"p{i:03d}.jpg")
        args, fil = [], []
        for k, t in enumerate(ts):
            args += ["-ss", f"{t:.3f}", "-i", v]
            fil.append(f"[{k}:v]scale=240:-2,drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='{i} {t:.2f}':"
                       f"fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.8:x=2:y=2[f{k}]")
        fil.append("".join(f"[f{k}]" for k in range(4)) + "hstack=inputs=4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", ";".join(fil), "-frames:v", "1", p],
                       check=True, creationflags=LOW)
        linhas.append(p)
    for k in range(0, len(linhas), 8):
        g = linhas[k:k + 8]
        args = sum((["-i", p] for p in g), [])
        f = "".join(f"[{i}:v]" for i in range(len(g))) + f"vstack=inputs={len(g)}" if len(g) > 1 else "null"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", f, "-q:v", "3",
                        os.path.join(out, f"folha_{k // 8 + 1:02d}.jpg")], check=True, creationflags=LOW)
    print(f"{len(linhas)} planos -> {(len(linhas) + 7) // 8} folhas em {out}")


if __name__ == "__main__":
    main()

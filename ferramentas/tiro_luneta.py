"""Acha automaticamente o QUADRO do tiro de sniper e as trocas de clipe em volta de cada kill candidata.

uso: python tiro_luneta.py video.mp4 pops.json saida.json [antes=1.6] [depois=1.4]
pops.json: instantes de kill candidatos (pop amarelo "+50"), ex. analise/pops_<video>.json filtrado.
Para cada pop, decodifica só a janela [pop-antes, pop+depois] a 30 fps (160x90) e calcula:
  luneta[k] : fração escura no aro em volta do centro (mirando)
  dif[k]    : diferença de cor entre quadros (troca de clipe = salto grande fora de entrada/saída de luneta)
tiro = último quadro com luneta antes dela sair (o quickscope atira e a luneta cai), precisa de >=3 quadros mirando.
Saída: [{pop, tiro, mira (s mirando antes do tiro), corte_antes, corte_depois}] (corte_* = troca de clipe mais
próxima antes/depois do tiro dentro da janela, ou null).
"""
import json
import subprocess
import sys

import numpy as np

W, H, FPS = 160, 90, 30
yy, xx = np.mgrid[0:H, 0:W]
R = np.hypot(xx - W / 2 + 0.5, yy - H / 2 + 0.5) / H
ANEIS = [(R >= a) & (R < a + 0.06) for a in np.arange(0.28, 0.58, 0.03)]
CANTOS = R > 0.62


def janela(v, a, dur):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-i", v, "-t", f"{dur:.3f}", "-an",
                        "-vf", f"fps={FPS},scale={W}:{H}:flags=area", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                       capture_output=True, creationflags=0x00004000).stdout
    n = len(r) // (W * H * 3)
    return np.frombuffer(r[:n * W * H * 3], np.uint8).reshape(n, H, W, 3)


def analisa(f):
    g = f.mean(3)
    esc = g < 45
    anel = np.stack([esc[:, m].mean(1) for m in ANEIS], 1).max(1)
    cantos = esc[:, CANTOS].mean(1)
    lun = np.maximum(anel, cantos * 0.9)
    peq = f.reshape(len(f), 18, 5, 32, 5, 3).mean((2, 4)).astype(np.float32)
    dif = np.r_[0, np.abs(np.diff(peq, axis=0)).mean((1, 2, 3))]
    return lun, dif


def main():
    v, pp, out = sys.argv[1:4]
    antes = float(sys.argv[4]) if len(sys.argv) > 4 else 1.6
    depois = float(sys.argv[5]) if len(sys.argv) > 5 else 1.4
    pops = json.load(open(pp))
    res = []
    for p in pops:
        a = max(0.0, p - antes)
        f = janela(v, a, antes + depois)
        if len(f) < 10:
            continue
        lun, dif = analisa(f)
        mira = lun > 0.55
        ip = int(round((p - a) * FPS))
        tiro = None
        # último quadro mirando, seguido de saída da luneta, entre pop-1,2s e pop+0,1s
        for k in range(min(len(f) - 2, ip + 3), max(2, ip - 36), -1):
            if mira[k] and not mira[k + 1] and not mira[min(len(f) - 1, k + 2)]:
                ini = k
                while ini > 0 and mira[ini - 1]:
                    ini -= 1
                if k - ini + 1 >= 3:
                    tiro = (k, k - ini + 1)
                break
        # trocas de clipe: salto de cor grande que NÃO é entrada/saída de luneta
        cortes = [k for k in range(1, len(f)) if dif[k] > 38 and mira[k] == mira[k - 1]]
        if tiro is None:
            res.append({"pop": p, "tiro": None})
            continue
        k, nm = tiro
        t = round(a + (k + 1) / FPS, 3)  # o disparo cai no quadro da saída da luneta
        ca = [c for c in cortes if c <= k]
        cd = [c for c in cortes if c > k + 1]
        res.append({"pop": p, "tiro": t, "mira": round(nm / FPS, 2),
                    "corte_antes": round(a + ca[-1] / FPS, 3) if ca else None,
                    "corte_depois": round(a + cd[0] / FPS, 3) if cd else None,
                    "ini_janela": round(a, 3), "fim_janela": round(a + len(f) / FPS, 3)})
        print(p, res[-1]["tiro"], res[-1]["mira"], res[-1]["corte_antes"], res[-1]["corte_depois"], flush=True)
    json.dump(res, open(out, "w"), indent=0)
    ok = [r for r in res if r["tiro"]]
    print(f"{len(ok)}/{len(res)} com tiro de luneta")


if __name__ == "__main__":
    main()

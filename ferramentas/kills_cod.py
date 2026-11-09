"""Confirma kills de COD (Cold War): tiro no áudio + "+50 Elimination" amarelo surgindo perto da mira.

uso: python kills_cod.py pop_<nome>.rgb tiros_<nome>.json saida.json [w=96 h=56 fps=10]
pop_*.rgb: região perto da mira (crop iw*0.24 x ih*0.22 a partir de 0.47,0.34) a 10 fps, 96x56 rgb24
           (gerado por projetos/<video>/analise/varrer.ps1).
kill = início de um "pop" amarelo (contagem de pixels amarelos sobe forte) até 0,8 s depois de um tiro.
Saída: [{tiro, pop, amarelo}] — tiro = instante do disparo (é ele que vai na batida).
"""
import json
import sys

import numpy as np


def main():
    rawp, tirosp, out = sys.argv[1:4]
    W, H, FPS = 96, 56, 10
    a = np.fromfile(rawp, np.uint8)
    n = len(a) // (W * H * 3)
    f = a[:n * W * H * 3].reshape(n, H, W, 3).astype(np.int16)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    am = ((r > 190) & (g > 160) & (b < 110) & (r - b > 110)).sum((1, 2))
    tiros = [t["t"] for t in json.load(open(tirosp))]
    pops = []
    for i in range(2, n):
        prev = am[max(0, i - 6):i - 1].min()
        if am[i] >= 25 and am[i] - prev >= 20 and (not pops or i / FPS - pops[-1][0] > 0.5):
            pops.append((i / FPS, int(am[i])))
    kills = []
    for tp, v in pops:
        cand = [t for t in tiros if 0 <= tp - t <= 0.8]
        if cand:
            kills.append({"tiro": cand[-1], "pop": round(tp, 1), "amarelo": v})
    json.dump(kills, open(out, "w"), indent=0)
    print(f"{n / FPS:.0f}s  pops {len(pops)}  kills {len(kills)}")
    print(" ".join(f"{k['tiro']:.1f}" for k in kills))
    sem = [round(tp, 1) for tp, v in pops if not any(0 <= tp - t <= 0.8 for t in tiros)]
    print("pops sem tiro:", sem)


if __name__ == "__main__":
    main()

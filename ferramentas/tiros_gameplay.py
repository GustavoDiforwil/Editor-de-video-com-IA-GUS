"""Acha os disparos (tiro de sniper) no áudio da gameplay — triagem para o estilo montagem.

uso: python tiros_gameplay.py video.mp4 saida.json [limiar_db=12]
Um disparo = subida brusca de energia (>= limiar dB acima da mediana dos 300 ms anteriores),
com nível absoluto alto e pelo menos 0,6 s depois do disparo anterior (sniper de ferrolho).
Só triagem: a kill tem que ser conferida nos frames (hitmarker, inimigo caindo, feed).
"""
import json
import subprocess
import sys

import numpy as np

SR = 16000


def main():
    v, out = sys.argv[1], sys.argv[2]
    lim = float(sys.argv[3]) if len(sys.argv) > 3 else 12.0
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", v, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True, creationflags=0x00004000).stdout
    x = np.frombuffer(raw, np.float32)
    w = SR // 100  # 10 ms
    n = len(x) // w
    e = 20 * np.log10(np.abs(x[:n * w]).reshape(n, w).max(1) + 1e-6)
    top = np.percentile(e, 99.5)
    tiros, last = [], -1000
    for i in range(30, n):
        base = np.median(e[i - 30:i])
        if e[i] - base >= lim and e[i] >= top - 12 and i - last >= 60:
            j = i + int(np.argmax(e[i:i + 3]))
            tiros.append({"t": round(j / 100, 2), "db": round(float(e[j]), 1), "subida": round(float(e[j] - base), 1)})
            last = i
    json.dump(tiros, open(out, "w"), indent=0)
    print(f"{len(tiros)} disparos em {n / 100:.0f}s (pico ref {top:.1f} dB)")
    print(" ".join(f"{t['t']:.1f}" for t in tiros))


if __name__ == "__main__":
    main()

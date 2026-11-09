"""Acha candidatos a momentos engraçados pela energia do áudio (gritos, risadas, explosões de reação)."""
import json
import sys
import wave

import numpy as np

wav, out = sys.argv[1], sys.argv[2]
with wave.open(wav) as w:
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

hop = sr // 4  # janelas de 0.25s
n = len(x) // hop
rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-10)
db = 20 * np.log10(rms)

# baseline local (mediana em ~2 min) para achar picos relativos ao contexto
k = 480
pad = np.pad(db, k // 2, mode="edge")
from numpy.lib.stride_tricks import sliding_window_view
base = np.median(sliding_window_view(pad, k + 1)[:: 1][:n], axis=1)
rel = db - base

# score por janela de 6s: picos fortes + densidade de fala alta (risada = sustentado)
win = 24
score = np.convolve(np.clip(rel, 0, None), np.ones(win), mode="same") + 2 * np.convolve((rel > 10).astype(float), np.ones(win), mode="same")

cands = []
order = np.argsort(score)[::-1]
taken = np.zeros(n, bool)
for i in order:
    if taken[max(0, i - 120): i + 120].any():
        continue
    taken[i] = True
    cands.append({"t": round(i * 0.25, 1), "score": round(float(score[i]), 1), "peak_db": round(float(db[max(0,i-12):i+12].max()), 1)})
    if len(cands) >= 40:
        break

json.dump(cands, open(out, "w"), indent=1)
for c in cands:
    h = c["t"]
    print(f"{int(h//3600)}:{int(h%3600//60):02d}:{int(h%60):02d}  score={c['score']}  peak={c['peak_db']}dB")

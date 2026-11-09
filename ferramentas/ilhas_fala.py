"""Acha as ilhas de som da narração e diz quais são FALA (têm palavra do whisper) e quais são respiração/ruído.

uso: ilhas_fala.py narracao.(mp3|wav) transcricao.jsonl [limiar_db=-36] [pausa_min=0.10]
Saída: uma linha por ilha (início, fim, pico dB, palavras). Ilha sem palavra = respiração/ruído -> cortar.
"""
import json
import subprocess
import sys

import numpy as np

SR = 16000
src, tj = sys.argv[1], sys.argv[2]
lim = float(sys.argv[3]) if len(sys.argv) > 3 else -36.0
pmin = float(sys.argv[4]) if len(sys.argv) > 4 else 0.10

y = np.frombuffer(subprocess.run(["ffmpeg", "-v", "quiet", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                 capture_output=True).stdout, np.float32)
hop = SR // 100  # 10 ms
n = len(y) // hop
rms = 20 * np.log10(np.sqrt((y[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
on = rms > lim

ilhas, i = [], 0
while i < n:
    if on[i]:
        j = i
        while j < n and (on[j] or (j + int(pmin * 100) < n and on[j:j + int(pmin * 100)].any())):
            j += 1
        ilhas.append((i / 100, j / 100, rms[i:j].max()))
        i = j
    else:
        i += 1

palavras = []
for line in open(tj, encoding="utf-8"):
    for s in json.loads(line)["segs"]:
        palavras += [(a, b, w) for a, b, w in s["words"]]

for a, b, pk in ilhas:
    ws = [w for wa, wb, w in palavras if wa < b and wb > a and min(b, wb) - max(a, wa) > 0.03]
    tag = " ".join(ws) if ws else "--- (sem palavra: respiração/ruído)"
    print(f"{a:6.2f} {b:6.2f}  {pk:5.1f}dB  {tag}")

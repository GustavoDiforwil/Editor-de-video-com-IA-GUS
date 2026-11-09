"""Análise de áudio de um vídeo de referência: fala (whisper), cortes secos de música/silêncios e picos (SFX).

Uso: audio_ref.py video INICIO DURACAO saida.txt
Gera uma linha do tempo de 0,25s com: volume, eventos (CORTE SECO / SILÊNCIO / PICO) e a fala.
"""
import ctypes
import os
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel

if os.name == "nt":
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)

video, ini, dur, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ini), "-t", str(dur), "-i", video,
                      "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
sr, hop = 16000, 4000
n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)

# fala
model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4,
                     download_root=os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"))
segs, _ = model.transcribe(x, language="pt", vad_filter=True, condition_on_previous_text=False)
segs = list(segs)

# picos curtos (transientes acima do contexto) e quedas bruscas (corte seco)
ev = {}
for i in range(2, n - 2):
    ctx = np.median(db[max(0, i - 8): i])
    if db[i] - ctx > 9 and db[i] > -30:
        ev.setdefault(i, []).append("PICO")
    if db[i - 1] > -28 and db[i] < db[i - 1] - 18:
        ev.setdefault(i, []).append("CORTE SECO")
    if db[i] < -45 and db[i - 1] >= -45:
        ev.setdefault(i, []).append("SILÊNCIO")

with open(out, "w", encoding="utf-8") as f:
    for i in range(n):
        t = i * 0.25
        fala = " | ".join(s.text.strip() for s in segs if s.start <= t < s.start + 0.25)
        tag = ",".join(ev.get(i, []))
        if tag or fala:
            ab = ini + t
            f.write(f"{int(ab // 60)}:{ab % 60:05.2f}  {db[i]:6.1f}dB  {tag:24s} {fala}\n")
print("ok", len(segs), "falas,", sum(len(v) for v in ev.values()), "eventos")

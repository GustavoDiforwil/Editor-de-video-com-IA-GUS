"""Mostra o volume (dB RMS) de cada meio segundo do vídeo final, para achar picos e buracos."""
import subprocess
import sys

import numpy as np

raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
h = 8000
db = 20 * np.log10(np.sqrt((x[: len(x) // h * h].reshape(-1, h) ** 2).mean(1)) + 1e-9)
peak = 20 * np.log10(np.abs(x).max() + 1e-9)
print(f"pico {peak:.1f} dB | média {np.median(db):.1f} dB | desvio {db.std():.1f} dB")
for i, v in enumerate(db):
    flag = "  <-- ALTO" if v > np.median(db) + 8 else ("  <-- baixo" if v < np.median(db) - 14 else "")
    print(f"{i*0.5:5.1f}s {v:6.1f} {'#' * int(max(0, v + 50) / 2)}{flag}")

"""Mapa de batidas de uma música (estilo montagem): ataques por spectral flux + energia por trecho.

uso: python batidas.py musica.wav saida.json
Gera:
  onsets  : [(t, força 0..1)] ataques detectados (picos do spectral flux, mín. 70 ms entre si)
  fortes  : só os ataques fortes (força >= 0.45) -> candidatos a tiro/corte
  energia : RMS em dB a cada 0,5 s (para achar intro/verso/refrão/pico)
  bpm     : tempo estimado por janelas de 10 s (autocorrelação do flux)
Imprime um resumo por segundo para ler e montar o mapa da música.
"""
import json
import subprocess
import sys

import numpy as np

SR = 22050
HOP = 256  # ~11,6 ms
NFFT = 2048


def carregar(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def flux(x):
    n = 1 + (len(x) - NFFT) // HOP
    win = np.hanning(NFFT).astype(np.float32)
    frames = np.lib.stride_tricks.as_strided(x, (n, NFFT), (x.strides[0] * HOP, x.strides[0]))
    S = np.abs(np.fft.rfft(frames * win, axis=1))
    S = np.log1p(100 * S)
    d = np.maximum(0, np.diff(S, axis=0)).sum(1)
    d = np.concatenate([[0], d])
    # tira a tendência (média móvel de ~0,5 s) e normaliza
    k = int(0.5 * SR / HOP)
    base = np.convolve(d, np.ones(k) / k, mode="same")
    o = np.maximum(0, d - base)
    return o / (np.percentile(o, 99.5) + 1e-9)


def picos(o, min_gap=0.07):
    g = int(min_gap * SR / HOP)
    res = []
    for i in range(1, len(o) - 1):
        if o[i] > 0.15 and o[i] >= o[i - 1] and o[i] >= o[i + 1] and o[i] == o[max(0, i - g):i + g + 1].max():
            res.append((round(i * HOP / SR, 3), round(float(min(1.0, o[i])), 2)))
    return res


def bpm_janela(o, a, b):
    s, e = int(a * SR / HOP), int(b * SR / HOP)
    seg = o[s:e] - o[s:e].mean()
    if len(seg) < 100:
        return None
    ac = np.correlate(seg, seg, "full")[len(seg) - 1:]
    fps = SR / HOP
    lo, hi = int(fps * 60 / 200), int(fps * 60 / 70)
    lag = lo + int(np.argmax(ac[lo:hi]))
    return round(60 * fps / lag, 1)


def main():
    p, out = sys.argv[1], sys.argv[2]
    x = carregar(p)
    dur = len(x) / SR
    o = flux(x)
    on = picos(o)
    hs = int(0.5 * SR)
    rms = [round(float(20 * np.log10(np.sqrt(np.mean(x[i:i + hs] ** 2)) + 1e-9)), 1) for i in range(0, len(x) - hs, hs)]
    bpm = [(a, bpm_janela(o, a, a + 10)) for a in range(0, int(dur) - 5, 5)]
    fortes = [t for t in on if t[1] >= 0.45]
    json.dump({"dur": dur, "onsets": on, "fortes": fortes, "energia": rms, "bpm": bpm}, open(out, "w"), indent=0)
    print(f"dur {dur:.1f}s  onsets {len(on)}  fortes {len(fortes)}")
    print("BPM por janela:", " ".join(f"{a}s:{b}" for a, b in bpm))
    for s in range(int(dur) + 1):
        e = rms[2 * s] if 2 * s < len(rms) else -99
        fs = [f"{t - s:.2f}{'*' if f >= 0.7 else ''}" for t, f in fortes if s <= t < s + 1]
        print(f"{s // 60}:{s % 60:02d}  {e:6.1f} dB  {'#' * max(0, int((e + 40) / 2)):<20} {' '.join(fs)}")


if __name__ == "__main__":
    main()

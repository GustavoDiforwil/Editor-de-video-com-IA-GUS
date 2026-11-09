"""Grade de batidas + fronteiras de seção de uma música (estilo montagem).

uso: python estrutura_musica.py musica.wav batidas.json saida.json [bpm] [t_ini_pulso]
- grade: ajusta a fase de uma grade de BPM fixo aos onsets (a partir de t_ini_pulso)
- novidade: troca de timbre (bandas log-mel, auto-similaridade em xadrez) por compasso -> fronteiras de seção
- brilho/grave por compasso: ajuda a ver solo de guitarra (brilho alto), parte só voz/piano (grave baixo)
"""
import json
import subprocess
import sys

import numpy as np

SR = 22050


def main():
    mus, bat, out = sys.argv[1:4]
    bpm = float(sys.argv[4]) if len(sys.argv) > 4 else None
    t0 = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
    B = json.load(open(bat))
    on = np.array([t for t, f in B["onsets"]])
    fo = np.array([f for t, f in B["onsets"]])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mus, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    dur = len(x) / SR
    # grade: varre a fase, pontua onsets perto das batidas (pesado pela força)
    per = 60 / bpm
    best = None
    for ph in np.arange(0, per, 0.002):
        g = t0 + ph + np.arange(0, (dur - t0) / per) * per
        idx = np.searchsorted(on, g)
        sc = 0
        for k, gi in zip(idx, g):
            for j in (k - 1, k):
                if 0 <= j < len(on) and abs(on[j] - gi) < 0.035:
                    sc += fo[j]
        if best is None or sc > best[0]:
            best = (sc, ph)
    fase = t0 + best[1]
    # ajuste fino do período (deriva)
    best2 = None
    for p2 in np.arange(per * 0.997, per * 1.003, per * 0.0001):
        g = fase + np.arange(0, (dur - fase) / p2) * p2
        idx = np.searchsorted(on, g)
        sc = sum(fo[j] for k, gi in zip(idx, g) for j in (k - 1, k) if 0 <= j < len(on) and abs(on[j] - gi) < 0.03)
        if best2 is None or sc > best2[0]:
            best2 = (sc, p2)
    per = best2[1]
    grade = list(np.round(fase + np.arange(0, (dur - fase) / per) * per, 3))
    # bandas log por ~1/4 de batida
    hop = int(SR * per / 4)
    n = len(x) // hop
    fr = x[:n * hop].reshape(n, hop) * np.hanning(hop)
    S = np.abs(np.fft.rfft(fr, axis=1)) ** 2
    f = np.fft.rfftfreq(hop, 1 / SR)
    edges = np.geomspace(40, 10000, 25)
    M = np.stack([S[:, (f >= a) & (f < b)].sum(1) for a, b in zip(edges[:-1], edges[1:])], 1)
    L = np.log10(M + 1e-9)
    # médias por compasso (4 batidas) a partir da fase
    comp = per * 4
    nb = int((dur - fase) / comp)
    feat, bri, gra = [], [], []
    for b in range(nb):
        a0 = int((fase + b * comp) * SR / hop)
        a1 = int((fase + (b + 1) * comp) * SR / hop)
        feat.append(L[a0:a1].mean(0))
        sb = S[a0:a1].sum(0)
        bri.append(float((sb * f).sum() / (sb.sum() + 1e-9)))
        gra.append(float(10 * np.log10(sb[(f > 40) & (f < 200)].sum() / (sb.sum() + 1e-9))))
    F = np.array(feat)
    F = (F - F.mean(0)) / (F.std(0) + 1e-9)
    C = F @ F.T / F.shape[1]
    w = 4
    nov = []
    for b in range(nb):
        s = 0
        for i in range(-w, w):
            for j in range(-w, w):
                if 0 <= b + i < nb and 0 <= b + j < nb:
                    s += C[b + i, b + j] * (1 if (i < 0) == (j < 0) else -1)
        nov.append(s)
    nov = np.array(nov) / (np.max(nov) + 1e-9)
    res = {"bpm": round(60 / per, 2), "periodo": per, "fase": fase, "grade": grade,
           "compassos": [{"n": b, "t": round(fase + b * comp, 2), "novidade": round(float(nov[b]), 2),
                          "brilho_hz": int(bri[b]), "grave_db": round(gra[b], 1)} for b in range(nb)]}
    json.dump(res, open(out, "w"), indent=0)
    print(f"BPM {res['bpm']}  fase {fase:.3f}s  periodo {per:.4f}s  compasso {comp:.3f}s")
    for c in res["compassos"]:
        t = c["t"]
        print(f"c{c['n']:3d} {int(t // 60)}:{t % 60:05.2f}  nov {c['novidade']:5.2f} {'#' * max(0, int(c['novidade'] * 20)):<20}"
              f" brilho {c['brilho_hz']:5d}  grave {c['grave_db']:6.1f}")


if __name__ == "__main__":
    main()

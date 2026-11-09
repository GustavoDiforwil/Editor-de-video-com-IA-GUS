"""Mede se a voz fica acima da música/efeitos na mistura final.
Compara o nível do vídeo nos trechos COM fala (narração ativa) e nas pausinhas entre frases (só música/efeitos).
uso: voz_vs_fundo.py video.mp4 narracao_cortada.wav [narr_em=0.5]
Diferença boa: 12 dB ou mais (a voz manda, a música só acompanha).
"""
import subprocess
import sys

import numpy as np

SR = 16000


def ler(f):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "quiet", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                        capture_output=True).stdout, np.float32)


def db(x, hop):
    n = len(x) // hop
    return 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)


video, narr = sys.argv[1], sys.argv[2]
em = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
hop = SR // 20  # 50 ms
mix = db(ler(video), hop)
v = db(np.concatenate([np.zeros(int(em * SR), np.float32), ler(narr)]), hop)
n = min(len(mix), len(v))
mix, v = mix[:n], v[:n]
fala = v > v.max() - 30
pausa = v < -70  # silêncio na narração (dentro do trecho narrado)
pausa[: int(em * 20) + 2] = False
fim_narr = np.nonzero(fala)[0].max()
pausa[fim_narr:] = False
p_fala = 10 * np.log10(np.mean(10 ** (mix[fala] / 10)))
p_fundo = 10 * np.log10(np.mean(10 ** (mix[pausa] / 10))) if pausa.any() else -99
print(f"com fala: {p_fala:.1f} dB | só fundo (pausas): {p_fundo:.1f} dB | diferença: {p_fala - p_fundo:.1f} dB")
# por minuto, para achar trecho onde a música sobe demais
for m0 in range(0, n // 1200 + 1):
    a, b = m0 * 1200, (m0 + 1) * 1200
    f_, p_ = fala[a:b], pausa[a:b]
    if f_.any() and p_.any():
        d = 10 * np.log10(np.mean(10 ** (mix[a:b][f_] / 10))) - 10 * np.log10(np.mean(10 ** (mix[a:b][p_] / 10)))
        print(f"  min {m0}: diferença {d:.1f} dB" + ("  <-- música alta" if d < 10 else ""))

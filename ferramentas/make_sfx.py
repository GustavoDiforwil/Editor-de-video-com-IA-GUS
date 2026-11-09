"""Gera o kit de efeitos sonoros do Estilo Rik (sintetizados, sem copyright)."""
import os
import wave

import numpy as np

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sfx_gerados")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, a=0.005, r=0.05):
    e = np.ones(n)
    na, nr = int(SR * a), int(SR * r)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def square(f, d):
    ph = np.cumsum(np.broadcast_to(f, t(d).shape) / SR)
    return np.sign(np.sin(2 * np.pi * ph))


def saw(f, d):
    ph = np.cumsum(np.broadcast_to(f, t(d).shape) / SR)
    return 2 * (ph % 1) - 1


def save(name, x, gain=0.8):
    x = x / (np.max(np.abs(x)) + 1e-9) * gain
    st = np.repeat((x * 32767).astype(np.int16)[:, None], 2, axis=1)
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


# Erro estilo "Windows": dois tons descendentes
a = np.sin(2 * np.pi * 880 * t(0.12)) * env(len(t(0.12)))
b = np.sin(2 * np.pi * 587 * t(0.25)) * env(len(t(0.25)), r=0.15)
save("erro.wav", np.concatenate([a, b]))

# Buzina de palhaço: duas buzinadas com pitch bend
def honk(d):
    n = len(t(d))
    f = np.linspace(420, 380, n)
    return lowpass(square(f, d) + 0.5 * saw(f * 1.5, d), 6) * env(n, 0.01, 0.04)
save("buzina.wav", np.concatenate([honk(0.18), np.zeros(int(SR * 0.06)), honk(0.32)]))

# Disco arranhando: ruído com varredura de pitch para frente e para trás
d = 0.45
n = len(t(d))
noise = rng.standard_normal(n)
sweep = np.abs(np.sin(np.linspace(0, 3 * np.pi, n)))
car = np.sin(2 * np.pi * np.cumsum(200 + 1800 * sweep) / SR)
save("scratch.wav", (noise * 0.6 + car) * sweep * env(n, 0.002, 0.08))

# Grilos (vácuo): chirps agudos modulados, 3s
d = 3.0
tt = t(d)
chirp = np.sin(2 * np.pi * 4700 * tt) * (np.sin(2 * np.pi * 30 * tt) > 0.3)
gate = ((tt % 0.75) < 0.22).astype(float)
save("grilos.wav", lowpass(chirp * gate, 3) * env(len(tt), 0.05, 0.3), gain=0.35)

# Trombone triste "wah wah wah waaah"
notes = [(311, 0.35), (294, 0.35), (277, 0.35), (262, 1.2)]
parts = []
for f, d in notes:
    n = len(t(d))
    vib = f * (1 + 0.012 * np.sin(2 * np.pi * 6 * t(d))) if d > 1 else f
    parts.append(lowpass(saw(vib, d), 10) * env(n, 0.03, 0.12))
save("triste.wav", np.concatenate(parts), gain=0.6)

# Whoosh de zoom
d = 0.3
n = len(t(d))
w = rng.standard_normal(n)
save("whoosh.wav", lowpass(w, 12) * np.hanning(n), gain=0.5)

# Boom grave (impacto de punch-in / vine boom)
d = 0.9
tt = t(d)
f = 110 * np.exp(-tt * 3) + 40
save("boom.wav", np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 4), gain=0.9)

# "Ahn?" sintético: tom ascendente tipo pergunta
d = 0.45
n = len(t(d))
f = np.linspace(180, 340, n) ** 1.0
save("ahn.wav", lowpass(saw(f, d), 14) * env(n, 0.02, 0.1), gain=0.6)

# Ding de piada (sininho)
d = 0.8
tt = t(d)
save("ding.wav", (np.sin(2 * np.pi * 1568 * tt) + 0.4 * np.sin(2 * np.pi * 3136 * tt)) * np.exp(-tt * 5), gain=0.5)

# Música chiptune de fundo (loop de 16 compassos, ~32s)
bpm = 140
beat = 60 / bpm
prog = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]
melody = [72, 76, 79, 76, 74, 72, 71, 67, 69, 72, 76, 72, 74, 71, 67, 71]
loop = []
for bar in range(16):
    chord = prog[bar % 4]
    for step in range(8):
        d = beat / 2
        n = len(t(d))
        arp = 440 * 2 ** ((chord[step % 3] + 12 - 69) / 12)
        bass = 440 * 2 ** ((chord[0] - 24 - 69) / 12)
        mel = 440 * 2 ** ((melody[(bar * 2 + step // 4) % 16] - 69) / 12)
        x = 0.25 * square(arp, d) * env(n, 0.002, 0.03)
        x += 0.35 * lowpass(square(bass, d), 4) * env(n, 0.002, 0.02)
        x += 0.3 * (np.where(np.sin(2 * np.pi * mel * t(d)) > 0.5, 1.0, -1.0)) * env(n, 0.005, 0.05)
        if step % 2 == 0:
            x[: int(SR * 0.02)] += 0.4 * rng.standard_normal(int(SR * 0.02)) * np.linspace(1, 0, int(SR * 0.02))
        loop.append(x)
save("musica_chiptune.wav", lowpass(np.concatenate(loop), 3), gain=0.5)

print("SFX gerados em", OUT)
for f in sorted(os.listdir(OUT)):
    print(" -", f)

"""Leitura do HUD de COD (Cold War) a 30 fps para achar o QUADRO EXATO de cada disparo e de cada kill.

uso: python hud_cod.py video.mp4 saida.npz
Sinais por quadro (30 fps, frame 640x360 RGB, lido em streaming):
  municao : mudança no número de balas (canto inferior direito) -> o contador cai no quadro do disparo
  amarelo : pixels amarelos perto da mira ("+50 Elimination", "+300 Headshot") -> pop = kill
  luneta  : fração escura no aro em volta do centro (mirando pela luneta)
Depois: python hud_cod.py --kills saida.npz kills.json  -> lista de kills com o tiro exato.
"""
import json
import subprocess
import sys

import numpy as np

W, H, FPS = 640, 360, 30


def varrer(v, out):
    yy, xx = np.mgrid[0:90, 0:160]
    r = np.hypot(xx - 79.5, yy - 44.5) / 90
    aneis = [(r >= a) & (r < a + 0.05) for a in np.arange(0.30, 0.56, 0.03)]
    # região da munição (número do pente) e do pop amarelo
    mx0, mx1, my0, my1 = int(W * 0.770), int(W * 0.812), int(H * 0.885), int(H * 0.952)
    px0, px1, py0, py1 = int(W * 0.47), int(W * 0.71), int(H * 0.34), int(H * 0.56)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-threads", "4", "-i", v, "-an",
                          "-vf", f"fps={FPS},scale={W}:{H}:flags=area", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE, creationflags=0x00004000)
    fs = W * H * 3
    qx0, qx1, qy0, qy1 = int(W * 0.40), int(W * 0.60), int(H * 0.07), int(H * 0.26)  # medalhas da kill
    mun, ama, lun, med = [], [], [], []
    prev = None
    prevm = None
    while True:
        b = p.stdout.read(fs * 60)
        if not b:
            break
        n = len(b) // fs
        f = np.frombuffer(b[:n * fs], np.uint8).reshape(n, H, W, 3)
        m = f[:, my0:my1, mx0:mx1].astype(np.int16).mean(3)
        if prev is not None:
            m_all = np.concatenate([prev[None], m])
        else:
            m_all = np.concatenate([m[:1], m])
        mun.append(np.abs(np.diff(m_all, axis=0)).mean((1, 2)))
        prev = m[-1]
        q = f[:, qy0:qy1, qx0:qx1].astype(np.int16)
        # medalha: pixels saturados (fita vermelha/azul, dourado) — a contagem sobe quando a medalha surge
        sat = (q.max(3) - q.min(3)) > 90
        med.append(sat.sum((1, 2)))
        pr = f[:, py0:py1, px0:px1].astype(np.int16)
        rr, gg, bb = pr[..., 0], pr[..., 1], pr[..., 2]
        ama.append(((rr > 190) & (gg > 160) & (bb < 110) & (rr - bb > 110)).sum((1, 2)))
        g = f[:, ::4, ::4].mean(3)
        esc = g < 40
        lun.append(np.stack([esc[:, a] .mean(1) for a in aneis], 1).max(1))
    np.savez_compressed(out, municao=np.concatenate(mun).astype(np.float32),
                        amarelo=np.concatenate(ama).astype(np.int32), luneta=np.concatenate(lun).astype(np.float32), medalha=np.concatenate(med).astype(np.int32))
    print(out, len(np.concatenate(mun)) / FPS, "s")


def kills(npz, out):
    d = np.load(npz)
    am, lu, me = d["amarelo"], d["luneta"], d["medalha"]
    n = len(me)
    # kill = medalha surgindo no topo (salto na contagem de pixels saturados), confirmada por pop amarelo
    res = []
    last = -100
    for i in range(2, n - 1):
        salto = int(me[i]) - int(me[i - 2])
        if salto >= 120 and me[i + 1] >= me[i] * 0.8 and i - last > 9:
            amar = am[i:i + 15].max() - am[max(0, i - 10):i].min()
            t = i - 1  # tiro ~1 quadro antes da medalha
            res.append({"tiro": round(t / FPS, 3), "medalha": int(salto), "amarelo": int(amar),
                        "luneta": round(float(lu[max(0, t - 3):t + 1].max()), 2)})
            last = i
    res = [k for k in res if k["amarelo"] >= 40]
    # junta duplicados (headshot + elimination do mesmo tiro)
    uniq = []
    for k in res:
        if not uniq or abs(k["tiro"] - uniq[-1]["tiro"]) > 0.05:
            uniq.append(k)
    # multikill: kills com menos de 2,5 s entre si
    for k in range(len(uniq)):
        uniq[k]["serie"] = 1
        if k and uniq[k]["tiro"] - uniq[k - 1]["tiro"] < 2.5:
            uniq[k]["serie"] = uniq[k - 1]["serie"] + 1
    json.dump(uniq, open(out, "w"), indent=0)
    print(f"kills {len(uniq)}")
    print(" ".join(f"{k['tiro']:.2f}{'L' if k['luneta'] > 0.5 else ''}" for k in uniq))


if __name__ == "__main__":
    if sys.argv[1] == "--kills":
        kills(sys.argv[2], sys.argv[3])
    else:
        varrer(sys.argv[1], sys.argv[2])

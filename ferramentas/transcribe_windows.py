"""Transcreve janelas em volta dos candidatos, uma por vez, salvando cada uma (retoma se cair).

Uso: transcribe_windows.py audio16k.wav cands.json saida.jsonl PRE POST
Roda com prioridade baixa e no máximo 4 threads para não travar o PC.
"""
import ctypes
import json
import os
import sys
import wave

import numpy as np
from faster_whisper import WhisperModel

if os.name == "nt":  # BELOW_NORMAL_PRIORITY_CLASS
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)

wav, cands_path, out, pre, post = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
models = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
cands = sorted(json.load(open(cands_path, encoding="utf-8-sig")), key=lambda c: c["t"])

done = set()
if os.path.exists(out):
    with open(out, encoding="utf-8") as f:
        done = {json.loads(l)["t"] for l in f if l.strip()}

model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4, download_root=models)

with wave.open(wav) as wf:
    sr = wf.getframerate()
    for i, c in enumerate(cands):
        if c["t"] in done:
            continue
        a = max(0.0, c["t"] - pre)
        wf.setpos(int(a * sr))
        audio = np.frombuffer(wf.readframes(int((pre + post) * sr)), dtype=np.int16).astype(np.float32) / 32768
        segs, _ = model.transcribe(audio, language="pt", word_timestamps=True, vad_filter=False,
                                   condition_on_previous_text=False)
        segs = [{"start": round(a + s.start, 2), "end": round(a + s.end, 2), "text": s.text.strip(),
                 "words": [[round(a + w.start, 2), round(a + w.end, 2), w.word.strip()] for w in (s.words or [])]}
                for s in segs]
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": c["t"], "segs": segs}, ensure_ascii=False) + "\n")
        h = c["t"]
        print(f"[{i+1}/{len(cands)}] {int(h//3600)}:{int(h%3600//60):02d}:{int(h%60):02d}  " +
              " | ".join(s["text"] for s in segs)[:160], flush=True)
print("FIM")

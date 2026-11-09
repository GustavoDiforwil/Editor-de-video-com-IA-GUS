"""Transcreve um intervalo contínuo do áudio em blocos de 60s, salvando cada bloco (retoma se cair).

Uso: transcribe_range.py audio16k.wav saida.jsonl INICIO FIM
Prioridade baixa e 4 threads para não travar o PC.
"""
import ctypes
import json
import os
import sys
import time
import wave

import numpy as np
from faster_whisper import WhisperModel

if os.name == "nt":
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)

wav, out, ini, fim = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
BLOCO = 60.0
models = os.environ.get("EDICAO_MODELOS") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

feitos = set()
if os.path.exists(out):
    with open(out, encoding="utf-8") as f:
        feitos = {json.loads(l)["bloco"] for l in f if l.strip()}

model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4, download_root=models)
t0 = time.time()
with wave.open(wav) as wf:
    sr = wf.getframerate()
    a = ini
    while a < fim:
        if a in feitos:
            a += BLOCO
            continue
        wf.setpos(int(a * sr))
        audio = np.frombuffer(wf.readframes(int(BLOCO * sr)), dtype=np.int16).astype(np.float32) / 32768
        segs, _ = model.transcribe(audio, language="pt", word_timestamps=True, vad_filter=True,
                                   vad_parameters={"min_silence_duration_ms": 300},
                                   condition_on_previous_text=False)
        segs = [{"start": round(a + s.start, 2), "end": round(a + s.end, 2), "text": s.text.strip(),
                 "words": [[round(a + w.start, 2), round(a + w.end, 2), w.word.strip()] for w in (s.words or [])]}
                for s in segs]
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps({"bloco": a, "segs": segs}, ensure_ascii=False) + "\n")
        print(f"[{int(a // 60):3d} min] {len(segs):2d} falas | {time.time() - t0:5.0f}s", flush=True)
        a += BLOCO
print("FIM")

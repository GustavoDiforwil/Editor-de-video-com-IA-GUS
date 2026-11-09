"""Gera um .txt legível da transcrição contínua (uma fala por linha com h:mm:ss)."""
import json
import sys

rows = []
for line in open(sys.argv[1], encoding="utf-8"):
    rows += json.loads(line)["segs"]
rows.sort(key=lambda s: s["start"])
with open(sys.argv[2], "w", encoding="utf-8") as f:
    for s in rows:
        a = s["start"]
        f.write(f"{int(a // 3600)}:{int(a % 3600 // 60):02d}:{a % 60:04.1f}  {s['text']}\n")
print(len(rows), "falas")

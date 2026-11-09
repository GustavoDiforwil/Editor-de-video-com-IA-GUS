"""Imprime as palavras (com tempo) de vários intervalos de uma transcrição .jsonl (formato bloco/segs).

Uso: words_range.py transcricao.jsonl "a-b" "a-b" ...   (em segundos)
"""
import json
import sys

words = []
for line in open(sys.argv[1], encoding="utf-8"):
    for s in json.loads(line)["segs"]:
        words += s["words"]
words.sort()
for r in sys.argv[2:]:
    a, b = map(float, r.split("-"))
    print(f"--- {int(a // 60)}:{a % 60:04.1f} .. {int(b // 60)}:{b % 60:04.1f}")
    print("  ".join(f"{w[0]:.1f}:{w[2]}" for w in words if a <= w[0] <= b))

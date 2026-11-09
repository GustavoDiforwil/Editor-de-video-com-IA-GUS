"""Converte legenda .vtt do YouTube (auto) em texto limpo com minutagem, sem repetições."""
import re
import sys

lines, last, t = [], "", "0:00"
for raw in open(sys.argv[1], encoding="utf-8"):
    raw = raw.strip()
    m = re.match(r"(\d+):(\d+):(\d+)\.\d+ -->", raw)
    if m:
        h, mi, s = map(int, m.groups())
        t = f"{h * 60 + mi}:{s:02d}"
        continue
    if not raw or raw.startswith(("WEBVTT", "Kind:", "Language:")) or raw.isdigit():
        continue
    txt = re.sub(r"<[^>]+>", "", raw).strip()
    if txt and txt != last and not last.endswith(txt):
        lines.append(f"[{t}] {txt}")
        last = txt
print("\n".join(lines))

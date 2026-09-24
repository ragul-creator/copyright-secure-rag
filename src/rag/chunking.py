from __future__ import annotations
import re

def chunk_text(text: str, target_words: int = 180, overlap_words: int = 30):
    words = re.findall(r"\S+", text.strip())
    if not words: return []
    chunks=[]; start=0
    while start < len(words):
        end=min(len(words), start+target_words)
        chunks.append(" ".join(words[start:end]))
        if end == len(words): break
        start=max(start+1, end-overlap_words)
    return chunks

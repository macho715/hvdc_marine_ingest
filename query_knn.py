# KR: 코사인 유사도 기반 Top‑K 검색
# EN: Cosine similarity KNN over normalized embeddings

import sqlite3, json
import numpy as np
from sentence_transformers import SentenceTransformer

DB = "marine.db"
model = SentenceTransformer("all-MiniLM-L6-v2")


def knn(query: str, topk: int = 5):
    qv = model.encode([query], normalize_embeddings=True)[0].astype(np.float32)
    con = sqlite3.connect(DB); cur = con.cursor()
    rows = cur.execute("SELECT raw_id, text, dim, embedding FROM marine_vec").fetchall()
    scored = []
    for raw_id, text, dim, blob in rows:
        vec = np.frombuffer(blob, dtype=np.float32)
        sim = float(np.dot(qv, vec))  # cosine (normalized)
        scored.append((sim, raw_id, text))
    scored.sort(reverse=True, key=lambda x: x[0])
    con.close()
    return scored[:topk]


if __name__ == "__main__":
    for sim, rid, text in knn("AGI high tide RORO window", topk=5):
        print(f"{sim:.4f} | {rid} | {text[:160]}...")

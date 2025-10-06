# KR: data/marine_*.csv → SQLite raw 저장 → 임베딩 생성 저장
# EN: CSVs into SQLite then build sentence-transformer embeddings

import os, json, time, sqlite3
import numpy as np
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer

DB = "marine.db"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
model = SentenceTransformer("all-MiniLM-L6-v2")  # CPU OK


def ensure_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS marine_raw(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT,
            ingested_at INTEGER,
            payload_json TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS marine_vec(
            raw_id INTEGER UNIQUE,
            text TEXT,
            dim INTEGER,
            embedding BLOB,
            FOREIGN KEY(raw_id) REFERENCES marine_raw(id)
        );
        """
    )
    con.commit(); con.close()


def add_csv_to_db(csv_path, source_url="manual"):
    df = pd.read_csv(csv_path)
    ts = int(time.time())
    con = sqlite3.connect(DB)
    cur = con.cursor()
    for _, row in df.iterrows():
        payload = row.to_dict()
        cur.execute(
            "INSERT INTO marine_raw(source_url, ingested_at, payload_json) VALUES (?, ?, ?)",
            (source_url, ts, json.dumps(payload, ensure_ascii=False)),
        )
    con.commit(); con.close()


def build_embeddings(batch=500):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    rows = cur.execute(
        """
        SELECT id, payload_json FROM marine_raw
        WHERE id NOT IN (SELECT raw_id FROM marine_vec)
        ORDER BY id ASC
        """
    ).fetchall()

    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        texts = [json.loads(r[1]) for r in chunk]
        texts = [json.dumps(t, ensure_ascii=False) for t in texts]
        embs = model.encode(texts, normalize_embeddings=True)
        for (raw_id, _), emb, text in zip(chunk, embs, texts):
            cur.execute(
                "INSERT OR REPLACE INTO marine_vec(raw_id, text, dim, embedding) VALUES (?, ?, ?, ?)",
                (raw_id, text, len(emb), np.asarray(emb, dtype=np.float32).tobytes()),
            )
        con.commit()
    con.close()


if __name__ == "__main__":
    ensure_db()
    # Load all CSVs that match pattern
    for p in list(DATA_DIR.glob("marine_*.csv")) + list(DATA_DIR.glob("marine_manual.csv")):
        add_csv_to_db(str(p))
    build_embeddings()
    print("OK - embeddings built")

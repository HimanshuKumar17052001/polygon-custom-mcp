#!/usr/bin/env python3
"""
index.py — One-off script to load *all* Polymarket markets into Chroma

Usage:
  # Make sure your .env is populated, then:
  python index.py
"""

import os
import json
import logging
from typing import Any, Dict, List

from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

# ─── Logging ───────────────────────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


# ─── CLOB helper ───────────────────────────────────────────────────────────
def _new_clob() -> ClobClient:
    host = os.getenv("CLOB_HOST", "https://clob.polymarket.com")
    key = os.getenv("PK", "")
    api_key = os.getenv("CLOB_API_KEY", "")
    api_secret = os.getenv("CLOB_SECRET", "")
    passph = os.getenv("CLOB_PASS_PHRASE", "")
    client = ClobClient(host, key=key, chain_id=POLYGON)
    client.set_api_creds(
        {
            "apiKey": api_key,
            "secret": api_secret,
            "passphrase": passph,
        }
    )
    return client


# ─── Chroma setup ──────────────────────────────────────────────────────────
CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", ".chroma")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-mpnet-base-v2"
)
collection = chroma_client.get_or_create_collection(
    name="prediction_markets",
    embedding_function=ef,
)


# ─── Batch‐upsert helper ────────────────────────────────────────────────────
def upsert_in_batches(
    collection,
    ids: List[str],
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    batch_size: int = 5000,
) -> None:
    """
    Upsert in chunks of at most `batch_size` items.
    """
    total = len(ids)
    for i in range(0, total, batch_size):
        chunk_ids = ids[i : i + batch_size]
        chunk_docs = documents[i : i + batch_size]
        chunk_metas = metadatas[i : i + batch_size]
        collection.upsert(
            ids=chunk_ids,
            documents=chunk_docs,
            metadatas=chunk_metas,
        )
        LOGGER.info(f"  Upserted batch {i}–{i+len(chunk_ids)} / {total}")


# ─── Indexing routine ─────────────────────────────────────────────────────
def index_markets() -> None:
    """
    Fetch every market from the CLOB API and upsert it into Chroma.
    """
    clob = _new_clob()

    # 1) page through all markets
    markets = []
    cursor = ""
    while True:
        page = clob.get_markets(next_cursor=cursor)
        cursor = page.get("next_cursor", "")
        data = page.get("data", [])
        markets.extend(data)
        if not cursor or cursor == "LTE=":
            break
    LOGGER.info("Fetched %d markets from CLOB API", len(markets))

    # 2) prepare ids/docs/metas
    ids: List[str] = []
    docs: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for m in markets:
        cid = m["condition_id"] or ""
        if not cid:
            continue

        # build a single text blob from every non-null field
        parts: List[str] = []
        for k, v in m.items():
            if v is None or v == "":
                continue
            if isinstance(v, (str, bool, int, float)):
                parts.append(f"{k}: {v}")
            elif isinstance(v, (list, dict)) and v:
                parts.append(f"{k}: {json.dumps(v, default=str)}")
        text = " ".join(parts)

        # sanitize metadata for Chroma (only primitives or JSON strings)
        clean_meta: Dict[str, Any] = {}
        for k, v in m.items():
            if isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            elif v is None:
                clean_meta[k] = ""
            else:
                clean_meta[k] = json.dumps(v, default=str)

        ids.append(cid)
        docs.append(text)
        metadatas.append(clean_meta)

    # 3) upsert in batches
    LOGGER.info("Upserting %d documents into Chroma…", len(ids))
    upsert_in_batches(collection, ids, docs, metadatas, batch_size=5000)
    LOGGER.info("Done indexing all markets.")


# ─── Entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    index_markets()
    count = collection.count()
    LOGGER.info(f"Total documents in collection: {count}")

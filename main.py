# from __future__ import annotations
# import os
# from typing import Any, Dict, List, Optional
# from dotenv import load_dotenv
# from mcp.server.fastmcp import FastMCP
# from py_clob_client.client import ClobClient, ApiCreds
# from py_clob_client.constants import POLYGON
# import requests

# load_dotenv()

# mcp = FastMCP("polymarket")


# def _new_clob() -> ClobClient:
#     """Return an authenticated py‑clob client using env vars."""
#     host = os.getenv("CLOB_HOST", "https://clob.polymarket.com")
#     key = os.getenv("PK")
#     api_key = os.getenv("CLOB_API_KEY")
#     api_secret = os.getenv("CLOB_SECRET")
#     passphrase = os.getenv("CLOB_PASS_PHRASE")

#     client = ClobClient(host, key=key, chain_id=POLYGON)
#     client.set_api_creds(dict(apiKey=api_key, secret=api_secret, passphrase=passphrase))
#     return client


# client = _new_clob()


# @mcp.tool()
# def list_all_prediction_markets(
#     query: Optional[str] = None, condition_id: Optional[str] = None
# ) -> List[Dict[str, Any]]:

#     client = _new_clob()
#     results: List[Dict[str, Any]] = []

#     if condition_id:
#         m = client.get_market(condition_id=condition_id)
#         outcomes, prices = [], []
#         for tok in m.get("tokens", []):
#             out = tok.get("outcome")
#             pr = tok.get("price")
#             if out is None or pr is None:
#                 continue
#             outcomes.append(out)
#             try:
#                 prices.append(float(pr))
#             except (TypeError, ValueError):
#                 prices.append(None)

#         results.append(
#             {
#                 "condition_id": m.get("condition_id"),
#                 "question_id": m.get("question_id"),
#                 "slug": m.get("market_slug"),
#                 "question": m.get("question"),
#                 "description": m.get("description", ""),
#                 "outcomes": outcomes,
#                 "prices": prices,
#                 "volume": m.get("volume"),
#                 "active": m.get("active"),
#                 "closed": m.get("closed"),
#                 "startDate": m.get("game_start_time") or m.get("start_date_iso"),
#                 "endDate": m.get("end_date_iso"),
#             }
#         )
#         return results

#     cursor = ""
#     search = (query or "").lower().strip()
#     while True:
#         page = client.get_markets(next_cursor=cursor)
#         cursor = page.get("next_cursor", "")

#         for m in page.get("data", []):
#             if search:
#                 desc = (m.get("description") or "").lower()
#                 ques = (m.get("question") or "").lower()
#                 slug = (m.get("market_slug") or "").lower()
#                 if search not in desc and search not in ques and search not in slug:
#                     continue

#             # extract outcomes & prices
#             outcomes, prices = [], []
#             for tok in m.get("tokens", []):
#                 out = tok.get("outcome")
#                 pr = tok.get("price")
#                 if out is None or pr is None:
#                     continue
#                 outcomes.append(out)
#                 try:
#                     prices.append(float(pr))
#                 except (TypeError, ValueError):
#                     prices.append(None)

#             results.append(
#                 {
#                     "condition_id": m.get("condition_id"),
#                     "question_id": m.get("question_id"),
#                     "slug": m.get("market_slug"),
#                     "question": m.get("question"),
#                     "description": m.get("description", ""),
#                     "outcomes": outcomes,
#                     "prices": prices,
#                     "volume": m.get("volume"),
#                     "active": m.get("active"),
#                     "closed": m.get("closed"),
#                     "startDate": m.get("game_start_time") or m.get("start_date_iso"),
#                     "endDate": m.get("end_date_iso"),
#                 }
#             )

#         if not cursor or cursor == "LTE=":
#             break

#     return results


# @mcp.tool()
# def list_prediction_market_orderbook(
#     condition_id: str,
#     snapshot_time: Optional[str] = None,
# ) -> Dict[str, Any]:

#     host = "https://clob.polymarket.com"
#     eth_key = os.getenv("PK", "")
#     creds = ApiCreds(
#         api_key=os.getenv("CLOB_API_KEY", ""),
#         api_secret=os.getenv("CLOB_SECRET", ""),
#         api_passphrase=os.getenv("CLOB_PASS_PHRASE", ""),
#     )
#     client = ClobClient(host, key=eth_key, chain_id=137, creds=creds)

#     market = client.get_market(condition_id=condition_id)
#     question = market["question"]

#     result: Dict[str, Any] = {
#         "condition_id": condition_id,
#         "question": question,
#         "orderbooks": {},
#     }

#     for tok in market["tokens"]:
#         token_id = tok["token_id"]
#         outcome = tok["outcome"]

#         book = client.get_order_book(token_id=token_id)

#         bids = book.bids
#         asks = book.asks

#         best_bid = float(bids[0].price) if bids else None
#         best_ask = float(asks[0].price) if asks else None
#         spread = (
#             (best_ask - best_bid)
#             if (best_bid is not None and best_ask is not None)
#             else None
#         )

#         bid_list = [{"price": lvl.price, "size": lvl.size} for lvl in bids]
#         ask_list = [{"price": lvl.price, "size": lvl.size} for lvl in asks]

#         result["orderbooks"][outcome] = {
#             "best_bid": best_bid,
#             "best_ask": best_ask,
#             "spread": spread,
#             "bids": bid_list,
#             "asks": ask_list,
#         }

#     return result


# def _fetch_interval(
#     condition_id: str,
#     interval: str,
#     fidelity: int,
#     start_ts: Optional[int],
#     end_ts: Optional[int],
# ) -> Dict[str, Any]:

#     CLOB_REST = "https://clob.polymarket.com"

#     mresp = requests.get(f"{CLOB_REST}/markets/{condition_id}")
#     mresp.raise_for_status()
#     market = mresp.json()
#     question = market["question"]

#     raw: Dict[str, Dict[int, float]] = {}
#     all_ts = set()

#     for tok in market["tokens"]:
#         token_id = tok["token_id"]
#         outcome = tok["outcome"]

#         params: Dict[str, Any] = {"market": token_id, "fidelity": fidelity}
#         if start_ts is not None:
#             params["startTs"] = start_ts
#         if end_ts is not None:
#             params["endTs"] = end_ts
#         if start_ts is None and end_ts is None:
#             params["interval"] = interval

#         hresp = requests.get(f"{CLOB_REST}/prices-history", params=params)
#         hresp.raise_for_status()
#         history = hresp.json()["history"]

#         mapping = {pt["t"]: pt["p"] for pt in history}
#         raw[outcome] = mapping
#         all_ts.update(mapping.keys())

#     ts_sorted = sorted(all_ts)
#     series = {outcome: [raw[outcome].get(ts) for ts in ts_sorted] for outcome in raw}
#     return {
#         "condition_id": condition_id,
#         "question": question,
#         "timestamps": ts_sorted,
#         "series": series,
#         "interval": interval,
#     }


# @mcp.tool()
# def list_prediction_market_graph(
#     condition_id: str,
#     interval: str = "1d",
#     fidelity: int = 50,
#     start_ts: Optional[int] = None,
#     end_ts: Optional[int] = None,
# ) -> List[Dict[str, Any]]:

#     VALID_INTERVALS = ["max", "1m", "1w", "1d", "6h", "1h"]

#     graphs = {
#         iv: _fetch_interval(condition_id, iv, fidelity, start_ts, end_ts)
#         for iv in VALID_INTERVALS
#     }
#     data = graphs[interval]

#     return [
#         {
#             "condition_id": data["condition_id"],
#             "question": data["question"],
#             "timestamps": data["timestamps"],
#             "yes": data["series"].get("Yes", []),
#             "no": data["series"].get("No", []),
#         }
#     ]

# if __name__ == "__main__":
#     mcp.run(transport="stdio")

#!/usr/bin/env python3
"""
main.py — Polymarket MCP server with Chroma semantic indexing

Dependencies:
  pip install python-dotenv chromadb py-clob-client mcp-server

Usage:
  # Run the MCP server over stdio:
  python main.py
  # or
  mcp run --transport stdio
"""
import os
import logging
from typing import Any, Dict, List, Optional
import regex as re
import json

import requests
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from py_clob_client.client import ClobClient, ApiCreds
from py_clob_client.constants import POLYGON

# ─── Configuration & Logging ───────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# ─── MCP Server ────────────────────────────────────────────────────────────
mcp = FastMCP("polymarket")


# ─── CLOB API Client Helper ────────────────────────────────────────────────
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


# shared CLOB client
client = _new_clob()


# ─── Chroma Vector DB Setup ────────────────────────────────────────────────
CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", ".chroma")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

# (we only need the embedding function when upserting; here we just open the collection)
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-mpnet-base-v2"
)

collection = chroma_client.get_or_create_collection(
    name="prediction_markets",
    embedding_function=ef,
)


# ─── Live‑fetch Helper ─────────────────────────────────────────────────────
def fetch_market_by_id(condition_id: str) -> List[Dict[str, Any]]:
    """
    Fetch a single market live from the CLOB API and shape it
    into the standard MCP output format.
    """
    try:
        m = client.get_market(condition_id=condition_id)
    except Exception as e:
        LOGGER.error("CLOB fetch failed for %s: %s", condition_id, e)
        return []

    outcomes, prices = [], []
    for tok in m.get("tokens", []):
        out = tok.get("outcome")
        pr = tok.get("price")
        if out is None or pr is None:
            continue
        outcomes.append(out)
        try:
            prices.append(float(pr))
        except (TypeError, ValueError):
            prices.append(None)

    return [
        {
            "condition_id": m.get("condition_id"),
            "question_id": m.get("question_id"),
            "slug": m.get("market_slug"),
            "question": m.get("question"),
            "description": m.get("description", ""),
            "outcomes": outcomes,
            "prices": prices,
            "volume": m.get("volume"),
            "active": m.get("active"),
            "closed": m.get("closed"),
            "startDate": m.get("game_start_time") or m.get("start_date_iso"),
            "endDate": m.get("end_date_iso"),
        }
    ]


# ─── MCP Tool: list_all_prediction_markets ─────────────────────────────────
@mcp.tool()
def list_all_prediction_markets(
    query: Optional[str] = None, condition_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Returns:
      - live CLOB fetch if `condition_id` is set
      - up to 10 semantic hits if `query` is set
      - all indexed markets otherwise
    """

    HEX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")

    # 1) If they passed a condition_id keyword, or if the first
    #    positional argument is a 0x‐hex string, do a live fetch:
    effective_id = condition_id or (query if HEX_RE.match(query or "") else None)
    if effective_id:
        return fetch_market_by_id(effective_id)

    # 2) Otherwise, do semantic search (or full scan)
    if query:
        resp = collection.query(
            query_texts=[query],
            n_results=10,
            include=["metadatas"],
        )
        metas = resp["metadatas"][0]
        ids = resp["ids"][0]
    else:
        all_ = collection.get(include=["metadatas"])
        metas = all_["metadatas"]
        ids = all_["ids"]

    results: List[Dict[str, Any]] = []
    for cid, m in zip(ids, metas):
        # tokens may be JSON‐stringified, so decode if needed
        raw_tokens = m.get("tokens", [])
        if isinstance(raw_tokens, str):
            try:
                tok_list = json.loads(raw_tokens)
            except json.JSONDecodeError:
                tok_list = []
        else:
            tok_list = raw_tokens

        outcomes, prices = [], []
        for tok in tok_list:
            out = tok.get("outcome")
            pr = tok.get("price")
            if out is None or pr is None:
                continue
            outcomes.append(out)
            try:
                prices.append(float(pr))
            except (TypeError, ValueError):
                prices.append(None)

        results.append(
            {
                "condition_id": cid,
                "question_id": m.get("question_id", ""),
                "slug": m.get("market_slug", ""),
                "question": m.get("question", ""),
                "description": m.get("description", ""),
                "outcomes": outcomes,
                "prices": prices,
                "volume": m.get("volume"),
                "active": m.get("active"),
                "closed": m.get("closed"),
                "startDate": m.get("game_start_time") or m.get("end_date_iso"),
                "endDate": m.get("end_date_iso"),
            }
        )

    return results


# ─── MCP Tool: list_prediction_market_orderbook ───────────────────────────
@mcp.tool()
def list_prediction_market_orderbook(
    condition_id: str,
    snapshot_time: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Exactly the same live CLOB orderbook fetch you had before —
    unchanged shape.
    """
    host = "https://clob.polymarket.com"
    eth_key = os.getenv("PK", "")
    creds = ApiCreds(
        api_key=os.getenv("CLOB_API_KEY", ""),
        api_secret=os.getenv("CLOB_SECRET", ""),
        api_passphrase=os.getenv("CLOB_PASS_PHRASE", ""),
    )
    c = ClobClient(host, key=eth_key, chain_id=137, creds=creds)

    market = c.get_market(condition_id=condition_id)
    question = market.get("question", "")
    out: Dict[str, Any] = {
        "condition_id": condition_id,
        "question": question,
        "orderbooks": {},
    }

    for tok in market.get("tokens", []):
        tid = tok["token_id"]
        outcome = tok["outcome"]
        book = c.get_order_book(token_id=tid)
        bids, asks = book.bids, book.asks

        best_bid = float(bids[0].price) if bids else None
        best_ask = float(asks[0].price) if asks else None
        spread = (
            (best_ask - best_bid)
            if best_bid is not None and best_ask is not None
            else None
        )

        out["orderbooks"][outcome] = {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "bids": [{"price": lvl.price, "size": lvl.size} for lvl in bids],
            "asks": [{"price": lvl.price, "size": lvl.size} for lvl in asks],
        }

    return out


# ─── MCP Tool: list_prediction_market_graph ────────────────────────────────
def _fetch_interval(
    condition_id: str,
    interval: str,
    fidelity: int,
    start_ts: Optional[int],
    end_ts: Optional[int],
) -> Dict[str, Any]:
    CLOB = "https://clob.polymarket.com"
    m = requests.get(f"{CLOB}/markets/{condition_id}").json()
    raw, all_ts = {}, set()
    for tok in m.get("tokens", []):
        tid, outcome = tok["token_id"], tok["outcome"]
        params = {"market": tid, "fidelity": fidelity}
        if start_ts is not None:
            params["startTs"] = start_ts
        if end_ts is not None:
            params["endTs"] = end_ts
        if start_ts is None and end_ts is None:
            params["interval"] = interval

        h = (
            requests.get(f"{CLOB}/prices-history", params=params)
            .json()
            .get("history", [])
        )
        mapping = {pt["t"]: pt["p"] for pt in h}
        raw[outcome] = mapping
        all_ts.update(mapping.keys())

    ts_sorted = sorted(all_ts)
    series = {o: [raw[o].get(ts) for ts in ts_sorted] for o in raw}
    return {
        "condition_id": condition_id,
        "question": m.get("question", ""),
        "timestamps": ts_sorted,
        "series": series,
        "interval": interval,
    }


@mcp.tool()
def list_prediction_market_graph(
    condition_id: str,
    interval: str = "1d",
    fidelity: int = 50,
    start_ts: Optional[int] = None,
    end_ts: Optional[int] = None,
) -> List[Dict[str, Any]]:
    VALID = ["max", "1m", "1w", "1d", "6h", "1h"]
    graphs = {
        iv: _fetch_interval(condition_id, iv, fidelity, start_ts, end_ts)
        for iv in VALID
    }
    data = graphs.get(interval, graphs["1d"])
    return [
        {
            "condition_id": data["condition_id"],
            "question": data["question"],
            "timestamps": data["timestamps"],
            "yes": data["series"].get("Yes", []),
            "no": data["series"].get("No", []),
        }
    ]


# ─── New MCP Tool: simulate_portfolio_impact ──────────────────────────────
@mcp.tool()
def simulate_portfolio_impact(
    condition_id: str,
    portfolio: List[Dict[str, Any]],
    roi_if_extended: float,
    roi_if_not_extended: float,
) -> Dict[str, Any]:
    """
    Simulate the impact of a two-outcome prediction market (pause extended vs not)
    on a simple portfolio.

    Args:
      condition_id: 0x... ID of a two-outcome tariff-pause market.
      portfolio:   List of { "name": str, "cost": float, "market": float } entries.
      roi_if_extended:    Assumed % ROI if pause IS extended (e.g. +0.02 for +2%).
      roi_if_not_extended: Assumed % ROI if pause is NOT extended.

    Returns:
      {
        "p_extended": float,
        "p_not_extended": float,
        "expected_roi": float,
        "scenario": {
           "extended": { "roi": float, "value": float },
           "not_extended": { "roi": float, "value": float }
        }
      }
    """
    # 1) fetch best bids/asks
    ob = list_prediction_market_orderbook(condition_id)["orderbooks"]

    def mid(o):
        b, a = o["best_bid"], o["best_ask"]
        return ((b + a) / 2) if (b is not None and a is not None) else None

    p_ext = mid(ob.get("Yes", {})) or 0.0
    p_no = mid(ob.get("No", {})) or 0.0
    # normalize
    total = p_ext + p_no
    if total > 0:
        p_ext, p_no = p_ext / total, p_no / total

    # 2) compute portfolio totals
    total_cost = sum(item["cost"] for item in portfolio)
    total_market = sum(item["market"] for item in portfolio)

    # 3) scenario values
    val_ext = total_market * (1 + roi_if_extended)
    val_no = total_market * (1 + roi_if_not_extended)

    # 4) expected ROI on market value
    exp_val = p_ext * val_ext + p_no * val_no
    exp_roi = (exp_val / total_market) - 1 if total_market > 0 else 0.0

    return {
        "p_extended": round(p_ext, 4),
        "p_not_extended": round(p_no, 4),
        "expected_roi": round(exp_roi, 4),
        "scenario": {
            "extended": {
                "roi": roi_if_extended,
                "value": round(val_ext, 2),
            },
            "not_extended": {
                "roi": roi_if_not_extended,
                "value": round(val_no, 2),
            },
        },
        "portfolio_summary": {
            "total_cost": round(total_cost, 2),
            "total_market": round(total_market, 2),
        },
    }


# ─── Launch ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    LOGGER.info("🚀 Starting MCP server…")
    mcp.run(transport="stdio")

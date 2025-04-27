from __future__ import annotations
import asyncio
import os
import datetime as _dt
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import mcp.types as types
from py_clob_client.client import ClobClient, ApiCreds
from py_clob_client.clob_types import BookParams
from py_clob_client.constants import POLYGON
import time
import requests
from datetime import datetime
import json

load_dotenv()

mcp = FastMCP("polymarket")


def _new_clob() -> ClobClient:
    """Return an authenticated py‑clob client using env vars."""
    host = os.getenv("CLOB_HOST", "https://clob.polymarket.com")
    key = os.getenv("PK")
    api_key = os.getenv("CLOB_API_KEY")
    api_secret = os.getenv("CLOB_SECRET")
    passphrase = os.getenv("CLOB_PASS_PHRASE")

    client = ClobClient(host, key=key, chain_id=POLYGON)
    client.set_api_creds(dict(apiKey=api_key, secret=api_secret, passphrase=passphrase))
    return client


client = _new_clob()


@mcp.tool()
async def list_all_prediction_markets(
    query: Optional[str] = None, condition_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch CLOB markets by condition_id *or* by full‐text query in description/question/slug.
    If `condition_id` is supplied, returns exactly that market.
    Otherwise pages through all markets and filters by `query` (case‐insensitive).
    """
    client = _new_clob()
    results: List[Dict[str, Any]] = []

    # 1) If a specific condition_id is provided, fetch that one market
    if condition_id:
        m = client.get_market(condition_id=condition_id)
        # extract outcomes & prices
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

        results.append(
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
        )
        return results

    # 2) Otherwise page through all markets and filter by `query`
    cursor = ""
    search = (query or "").lower().strip()
    while True:
        page = client.get_markets(next_cursor=cursor)
        cursor = page.get("next_cursor", "")

        for m in page.get("data", []):
            # if query provided, skip non‐matches
            if search:
                desc = (m.get("description") or "").lower()
                ques = (m.get("question") or "").lower()
                slug = (m.get("market_slug") or "").lower()
                if search not in desc and search not in ques and search not in slug:
                    continue

            # extract outcomes & prices
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

            results.append(
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
            )

        if not cursor or cursor == "LTE=":
            break

    return results


@mcp.tool()
async def list_prediction_market_orderbook(
    condition_id: str,
    snapshot_time: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetches, for each outcome in the given market:
      - best bid, best ask, and spread
      - full bid ladder and ask ladder

    Returns a dict:
    {
      "condition_id": ...,
      "question" : ...,
      "orderbooks": {
        "<outcome>": {
          "best_bid": float,
          "best_ask": float,
          "spread": float,
          "bids":  [ {"price": str, "size": str}, ... ],
          "asks":  [ {"price": str, "size": str}, ... ],
        },
        ...
      }
    }

    Note: historical snapshots aren’t supported by the public REST API,
    so `snapshot_time` is accepted but ignored (always returns the live book).
    """
    # --- Client init (L2 API-Key auth) ---
    host = "https://clob.polymarket.com"
    eth_key = os.getenv("PK", "")
    creds = ApiCreds(
        api_key=os.getenv("CLOB_API_KEY", ""),
        api_secret=os.getenv("CLOB_SECRET", ""),
        api_passphrase=os.getenv("CLOB_PASS_PHRASE", ""),
    )
    client = ClobClient(host, key=eth_key, chain_id=137, creds=creds)

    # --- Fetch market metadata ---
    market = client.get_market(condition_id=condition_id)
    question = market["question"]

    result: Dict[str, Any] = {
        "condition_id": condition_id,
        "question": question,
        "orderbooks": {},
    }

    # --- For each outcome token, fetch its book ---
    for tok in market["tokens"]:
        token_id = tok["token_id"]
        outcome = tok["outcome"]

        # (ignore snapshot_time because not available via REST)
        book = client.get_order_book(token_id=token_id)

        # book.bids and book.asks are lists of OrderSummary objects
        bids = book.bids
        asks = book.asks

        # best bid/ask/spread
        best_bid = float(bids[0].price) if bids else None
        best_ask = float(asks[0].price) if asks else None
        spread = (
            (best_ask - best_bid)
            if (best_bid is not None and best_ask is not None)
            else None
        )

        # build the ladders as plain dicts
        bid_list = [{"price": lvl.price, "size": lvl.size} for lvl in bids]
        ask_list = [{"price": lvl.price, "size": lvl.size} for lvl in asks]

        result["orderbooks"][outcome] = {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "bids": bid_list,
            "asks": ask_list,
        }

    return result


def _fetch_interval(
    condition_id: str,
    interval: str,
    fidelity: int,
    start_ts: Optional[int],
    end_ts: Optional[int],
) -> Dict[str, Any]:

    CLOB_REST = "https://clob.polymarket.com"

    mresp = requests.get(f"{CLOB_REST}/markets/{condition_id}")
    mresp.raise_for_status()
    market = mresp.json()
    question = market["question"]

    raw: Dict[str, Dict[int, float]] = {}
    all_ts = set()

    for tok in market["tokens"]:
        token_id = tok["token_id"]
        outcome = tok["outcome"]

        params: Dict[str, Any] = {"market": token_id, "fidelity": fidelity}
        if start_ts is not None:
            params["startTs"] = start_ts
        if end_ts is not None:
            params["endTs"] = end_ts
        if start_ts is None and end_ts is None:
            params["interval"] = interval

        hresp = requests.get(f"{CLOB_REST}/prices-history", params=params)
        hresp.raise_for_status()
        history = hresp.json()["history"]

        mapping = {pt["t"]: pt["p"] for pt in history}
        raw[outcome] = mapping
        all_ts.update(mapping.keys())

    ts_sorted = sorted(all_ts)
    series = {outcome: [raw[outcome].get(ts) for ts in ts_sorted] for outcome in raw}
    return {
        "condition_id": condition_id,
        "question": question,
        "timestamps": ts_sorted,
        "series": series,
        "interval": interval,
    }


@mcp.tool()
async def list_prediction_market_graph(
    condition_id: str,
    interval: str = "1d",
    fidelity: int = 50,
    start_ts: Optional[int] = None,
    end_ts: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch Yes/No price history for a single CLOB market and return one object with:
      {
        "condition_id": ...,
        "question": ...,
        "timestamps": [...],
        "yes": [...],
        "no": [...]
      }
    """

    VALID_INTERVALS = ["max", "1m", "1w", "1d", "6h", "1h"]

    # fetch all intervals (for dropdown-style flexibility)
    graphs = {
        iv: _fetch_interval(condition_id, iv, fidelity, start_ts, end_ts)
        for iv in VALID_INTERVALS
    }
    data = graphs[interval]

    return [
        {
            "condition_id": data["condition_id"],
            "question": data["question"],
            "timestamps": data["timestamps"],
            "yes": data["series"].get("Yes", []),
            "no": data["series"].get("No", []),
        }
    ]


# Driver code to run the MCP server
if __name__ == "__main__":
    mcp.run(transport="stdio")

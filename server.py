import os
import logging
from typing import Any, Dict, List, Optional
import regex as re
import json
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import asyncio

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


# Shared CLOB client instance (used for synchronous calls)
client = _new_clob()

# ─── Chroma Vector DB Setup ────────────────────────────────────────────────
CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", ".chroma")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-mpnet-base-v2"
)
collection = chroma_client.get_or_create_collection(
    name="prediction_markets",
    embedding_function=ef,
)


# ─── Live-fetch Helper ─────────────────────────────────────────────────────
def fetch_market_by_id(condition_id: str) -> List[Dict[str, Any]]:
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


# ─── MCP Tools ─────────────────────────────────────────────────────────────


@mcp.tool()
def list_all_prediction_markets(
    query: Optional[str] = None, condition_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    HEX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
    effective_id = condition_id or (query if HEX_RE.match(query or "") else None)
    if effective_id:
        return fetch_market_by_id(effective_id)

    if query:
        resp = collection.query(
            query_texts=[query], n_results=10, include=["metadatas"]
        )
        metas = resp["metadatas"][0]
        ids = resp["ids"][0]
    else:
        all_ = collection.get(include=["metadatas"])
        metas = all_["metadatas"]
        ids = all_["ids"]

    results = []
    for cid, m in zip(ids, metas):
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
            if out and pr:
                outcomes.append(out)
                try:
                    prices.append(float(pr))
                except:
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


@mcp.tool()
async def list_prediction_market_orderbooks(condition_ids: List[str]) -> Dict[str, Any]:
    """
    Async fetch multiple orderbooks concurrently by condition_ids.
    """
    client = _new_clob()

    async def fetch_orderbook(cid):
        market = client.get_market(condition_id=cid)
        orderbooks = {}
        for tok in market.get("tokens", []):
            tid, outcome = tok["token_id"], tok["outcome"]
            book = client.get_order_book(token_id=tid)
            bids = [{"price": lvl.price, "size": lvl.size} for lvl in book.bids]
            asks = [{"price": lvl.price, "size": lvl.size} for lvl in book.asks]
            best_bid = float(bids[0]["price"]) if bids else None
            best_ask = float(asks[0]["price"]) if asks else None
            orderbooks[outcome] = {
                "best_bid": best_bid,
                "best_ask": best_ask,
                "spread": best_ask - best_bid if best_bid and best_ask else None,
                "bids": bids,
                "asks": asks,
            }
        return cid, {
            "question": market.get("question", ""),
            "orderbooks": orderbooks,
        }

    tasks = [fetch_orderbook(cid) for cid in condition_ids]
    results = await asyncio.gather(*tasks)

    return {cid: data for cid, data in results}


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
        if start_ts:
            params["startTs"] = start_ts
        if end_ts:
            params["endTs"] = end_ts
        if not start_ts and not end_ts:
            params["interval"] = interval

        h = (
            requests.get(f"{CLOB}/prices-history", params=params)
            .json()
            .get("history", [])
        )
        raw[outcome] = {pt["t"]: pt["p"] for pt in h}
        all_ts.update(raw[outcome].keys())

    ts_sorted = sorted(all_ts)
    return {
        "condition_id": condition_id,
        "question": m.get("question", ""),
        "timestamps": ts_sorted,
        "series": {o: [raw[o].get(ts) for ts in ts_sorted] for o in raw},
        "interval": interval,
    }


@mcp.tool()
def list_prediction_market_graph(
    condition_id: str,
    interval: str = "max",
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


@mcp.tool()
def forecast_scenario_probabilities(
    condition_id: str, time_horizons_days: List[int] = [1, 7, 30, 90, 180, 365]
) -> List[Dict[str, Any]]:
    try:
        hist_data = list_prediction_market_graph(condition_id=condition_id)
        if not hist_data or not hist_data[0].get("yes"):
            return []

        data = hist_data[0]
        series = pd.Series(
            data["yes"], index=pd.to_datetime(data["timestamps"], unit="s")
        )
        daily_series = series.resample("D").last().ffill()

        if len(daily_series) < 10:
            return []

        best_aic, best_order = np.inf, (1, 1, 1)
        for p in range(2):
            for d in range(2):
                for q in range(2):
                    try:
                        model = ARIMA(daily_series, order=(p, d, q))
                        model_fit = model.fit()
                        if model_fit.aic < best_aic:
                            best_aic, best_order = model_fit.aic, (p, d, q)
                    except:
                        continue

        model = ARIMA(daily_series, order=best_order).fit()
        forecast = model.get_forecast(steps=max(time_horizons_days))

        return [
            {
                "horizon_days": days,
                "yes_probability": round(float(forecast.predicted_mean[days - 1]), 3),
                "no_probability": round(
                    1 - float(forecast.predicted_mean[days - 1]), 3
                ),
            }
            for days in time_horizons_days
            if days <= len(forecast.predicted_mean)
        ]

    except Exception as e:
        LOGGER.error(f"Forecast failed: {str(e)}", exc_info=True)
        return []


# ─── Launch ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    LOGGER.info("🚀 Starting MCP server ...")
    mcp.run(transport="stdio")

# polygon-custom-mcp

A custom MCP server for Polymarket's CLOB API, built with Python and powered by Chroma semantic search.

## Overview

This MCP server exposes four tools to any MCP-compatible client (e.g. Claude Desktop):

1. `list_all_prediction_markets`
   Search prediction markets by keyword or condition ID (semantic + exact match).
2. `list_prediction_market_orderbook`
   Fetch live orderbook (best bid/ask, bids/asks) for each outcome.
3. `list_prediction_market_graph`
   Retrieve historical price series for a market across multiple intervals.
4. `simulate_portfolio_impact`
   Simulate portfolio ROI scenarios based on a two-outcome market probability.

You also have a one-time indexing script:

* `index.py` — fetches *all* markets from the CLOB API and upserts them into a persistent Chroma collection.

And a small helper:

* `get_api.py` — derive a new on-chain API key from your private key.

## Prerequisites

* **OS:** Windows, macOS, or Linux
* **Python:** 3.8+
* **Virtual environment:** recommended (venv, pipenv, poetry, etc.)
* **Environment variables** (in a `.env` file at project root, **never** commit this file):

  ```ini
  CLOB_HOST=https://clob.polymarket.com
  PK=<your-Polymarket-private-key>
  CLOB_API_KEY=<your-API-key>
  CLOB_SECRET=<your-API-secret>
  CLOB_PASS_PHRASE=<your-API-passphrase>
  CHROMA_PERSIST_DIR=./.chroma
  ```

## Project Structure

```
polygon-custom-mcp/
├── main.py
├── index.py
├── get_api.py
├── requirements.txt
├── .env
└── README.md
```

* **main.py**
  MCP server implementation with all four tools.
* **index.py**
  One-time indexing script to populate Chroma.
* **get\_api.py**
  Helper to derive a new on-chain API key.
* **requirements.txt**
  Python dependencies.
* **.env**
  Your Polymarket credentials and config (gitignored).

## Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/yourusername/polygon-custom-mcp.git
   cd polygon-custom-mcp
   ```

2. **Create & activate a virtualenv**
   Windows PowerShell:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   macOS/Linux:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Populate `.env`**
   Copy `.env.example` → `.env` and fill in your credentials.

## One-Time Indexing

Before running the server, index all existing markets into Chroma:

```bash
python index.py
```

You should see logs indicating batches being upserted and a final count of documents in the collection.

## Running the MCP Server

Start the server (JSON-RPC over stdio):

```bash
python main.py
# or equivalently:
mcp run --transport stdio
```

You should see:

```
[MCP] polygon-custom-mcp listening on stdio…
```

## Tool Usage Examples

### 1. list\_all\_prediction\_markets

```json
Request:
{ "query": "trump tariff" }

Response:
[
  {
    "condition_id": "0x…",
    "question": "Will Trump impose new tariffs…?",
    "description": "This market will resolve to Yes if…",
    "outcomes": ["Yes","No"],
    …
  },
  …
]
```

You can also pass a raw hex ID:

```json
Request:
{ "query": "0xabc123…", "condition_id": null }

# or

Request:
{ "condition_id": "0xabc123…" }
```

### 2. list\_prediction\_market\_orderbook

```json
Request:
{ "condition_id": "0xabc123…" }

Response:
{
  "condition_id": "0xabc123…",
  "question": "Will…?",
  "orderbooks": {
    "Yes": {
      "best_bid": 0.25,
      "best_ask": 0.27,
      "bids": [{"price":"0.25","size":"100"},…],
      "asks": [{"price":"0.27","size":"50"},…]
    },
    "No": { … }
  }
}
```

### 3. list\_prediction\_market\_graph

```json
Request:
{ "condition_id": "0xabc123…", "interval": "1d" }

Response:
[
  {
    "condition_id": "0xabc123…",
    "question": "Will…?",
    "timestamps": […],
    "yes": [0.25,0.26,…],
    "no": [0.75,0.74,…]
  }
]
```

### 4. simulate\_portfolio\_impact

```json
Request:
{
  "condition_id": "0xabc123…",
  "portfolio": [
    {"name":"ICICI","cost":348.67,"market":438.79},
    {"name":"SBI","cost":5000.00,"market":7908.40},
    …
  ],
  "roi_if_extended": 0.02,
  "roi_if_not_extended": -0.01
}

Response:
{
  "p_extended": 0.36,
  "p_not_extended": 0.64,
  "expected_roi": 0.0081,
  "scenario": {
    "extended": {"roi":0.02,"value":18123.48},
    "not_extended":{"roi":-0.01,"value":17590.43}
  },
  "portfolio_summary": {
    "total_cost": 10348.67,
    "total_market": 17768.11
  }
}
```

## Deriving an API Key

If you need to derive a fresh API key from your private key, run:

```bash
python get_api.py
```

It will print a new API key you can use for your `CLOB_API_KEY` environment variable.

---

**That’s it!** You now have a fully functional MCP server for Polymarket, with semantic search, live orderbooks, history, and even portfolio impact simulation.

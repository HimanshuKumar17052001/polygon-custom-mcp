# polygon-custom-mcp

A powerful MCP server and CLI-based AI client for interacting with **Polymarket's CLOB API**. This tool enables intelligent querying, forecasting, and visualization of prediction markets using AI and time-series forecasting tools.

---

## 🔎 Overview

This project includes:

### ✅ MCP Server

Implements the **Model Context Protocol (MCP)** using the FastMCP framework. Exposes tools that access Polymarket's prediction markets and apply analytics.

### 🧱 MCP Client

A command-line interface that uses a **Groq-hosted LLM** and LangChain ReAct Agent to interactively query prediction markets using the server's tools.

---

## 🛌 Server Tooling Summary

### Available Tools (Defined in `server.py`):

1. **list\_all\_prediction\_markets(query, condition\_id)**

   * Search or retrieve prediction markets by keyword or condition ID.
   * Uses Chroma vector DB + Polymarket CLOB API.

2. **list\_prediction\_market\_orderbooks(condition\_ids: List\[str])**

   * Concurrently fetches live orderbooks (bid/ask, spreads, volumes) for multiple markets.
   * Uses `asyncio.gather()` with `py-clob-client`.

3. **list\_prediction\_market\_graph(condition\_id, interval, fidelity, start\_ts, end\_ts)**

   * Returns historical time-series price data for Yes/No outcomes.
   * Fetches from Polymarket's `/prices-history` endpoint.

4. **forecast\_scenario\_probabilities(condition\_id, time\_horizons\_days)**

   * Forecasts future Yes/No outcome probabilities using **ARIMA** time series modeling (via `statsmodels`).
   * Steps: Fetch graph → resample to daily → auto-select ARIMA(p,d,q) → forecast.

---

## 🛌 Client Capabilities (`client.py`)

### 🪧 Features

* Uses `ChatGroq` model (`qwen-qwq-32b`) via LangChain.
* Loads tools dynamically using `load_mcp_tools()`.
* Renders outputs as Markdown tables in terminal using `rich`.
* Accepts **multi-line queries** via `Ctrl+D` (Linux/macOS) or `Ctrl+Z + Enter` (Windows).
* Persists conversation history and context for multi-step ReAct flows.

### ⚖️ Tools Used in Client

* **LangChain** + **LangGraph**: For tool agent and ReAct pattern.
* **langchain\_groq**: For LLM access via Groq API.
* **rich**: For beautiful CLI formatting.
* **mcp**: For client/server MCP protocol management.

### 🔨 Client Workflow:

1. Initializes Groq LLM and MCP connection.
2. Loads all available tools from the server.
3. Constructs a LangChain ReAct agent with those tools.
4. Accepts multi-line user input.
5. Sends message history to LLM for action + tool invocation.
6. Renders structured responses as formatted Markdown.

---

## ♻️ Technologies & Libraries

### Server:

* **Python 3.8+**
* `mcp[cli]`: FastMCP server framework
* `py-clob-client`: SDK for Polymarket CLOB API
* `requests`: For HTTP calls
* `chromadb`: Vector DB for semantic search
* `statsmodels`, `pandas`, `numpy`: Time series forecasting (ARIMA)
* `.env` config: Loads API keys and credentials

### Client:

* `langchain`, `langgraph`, `langchain_groq`: Agent + LLM orchestrator
* `mcp`: Client session handling
* `rich`: CLI formatting

---

## 🌐 Polymarket APIs Used

* `GET /markets/{condition_id}`
* `GET /orderbook/{token_id}`
* `GET /prices-history`

---

## ⚙️ Installation

### 1. Clone the Project

```bash
git clone https://github.com/himanshu/polygon-custom-mcp.git
cd polygon-custom-mcp
```

### 2. Set Up Environment

```bash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
```

### 3. Add Your Secrets to `.env`

```
CLOB_HOST=https://clob.polymarket.com
PK=<your-private-key>
CLOB_API_KEY=<api-key>
CLOB_SECRET=<secret>
CLOB_PASS_PHRASE=<passphrase>
CHROMA_PERSIST_DIR=.chroma
```

---

## 🚀 Running the Server

```bash
python server.py  # or main.py if renamed
```

Expected output:

```
[MCP] polygon-custom-mcp listening on stdio...
```

---

## ⏳ Running the Client

```bash
python client.py
```

You’ll be prompted to paste your Groq API key and begin chatting with the agent.

**Example queries:**

* "What is the probability that Trump extends the tariff pause in 30 days?"
* "Forecast for market 0x1234 for 7, 30, 90 days."

---

## 🧪 Example Use Case

> "Here is my portfolio of mutual funds. How would Trump’s tariff extension scenario affect ROI?"

1. Agent identifies relevant market via `list_all_prediction_markets()`
2. Extracts `condition_id`
3. Forecasts outcome probabilities via `forecast_scenario_probabilities()`
4. Structures results in Markdown table with horizon-wise probabilities
5. Responds with a reasoning + output block

---

## 📅 Project Structure

```
polygon-custom-mcp/
├── client.py         # CLI chat agent
├── server.py         # MCP server and tool definitions
├── requirements.txt  # Dependencies
├── .env              # API keys (not checked in)
└── README.md         # Documentation (this file)
```

---

## ✊ Credits

* Groq + LangChain for lightning-fast LLM interface
* Polymarket for market APIs
* FastMCP for standardizing AI ↔ tool communication

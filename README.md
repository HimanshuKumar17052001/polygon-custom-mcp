# polygon-custom-mcp

An intelligent MCP server and CLI-based AI client for analyzing the relationship between events listed on Polymarket and their potential impact on an investor's portfolio. This system leverages the Polymarket CLOB API and Brave Web Search to support informed decision-making using prediction market insights.

A powerful MCP server and CLI-based AI client for interacting with Polymarket's CLOB API. This tool enables intelligent querying, forecasting, and visualization of prediction markets using AI and time-series forecasting tools.

---

## 🔎 Overview

This project includes:

### ✅ MCP Server

Implements the **Model Context Protocol (MCP)** using the FastMCP framework. Exposes tools that access Polymarket's prediction markets and apply analytics.

### 🧱 MCP Client

A command-line interface that uses a **Groq-hosted LLM** and LangChain ReAct Agent to interactively query prediction markets using the server's tools.

---

## 🛠 Server Tooling Summary

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

## 💬 Client Capabilities (`client.py`)

### 🪧 Features

* Uses `ChatGroq` model (`qwen-qwq-32b`) via LangChain.
* Loads tools dynamically using `load_mcp_tools()`.
* Renders outputs as Markdown tables in terminal using `rich`.
* Accepts **multi-line queries** via `Ctrl+D` (Linux/macOS) or `Ctrl+Z + Enter` (Windows).
* Persists conversation history and context for multi-step ReAct flows.

### ⚙️ Client Workflow

1. Initializes Groq LLM and MCP connection.
2. Loads all available tools from the server.
3. Constructs a LangChain ReAct agent with those tools.
4. Accepts multi-line user input.
5. Sends message history to LLM for action + tool invocation.
6. Renders structured responses as formatted Markdown.

---

## 🧰 Technologies & Libraries

### Server:

* Python 3.8+
* `mcp[cli]` – FastMCP server framework
* `py-clob-client` – SDK for Polymarket CLOB API
* `requests` – REST API interaction
* `chromadb` – Vector DB for semantic search
* `statsmodels`, `pandas`, `numpy` – ARIMA time series forecasting
* `python-dotenv`, `regex`, `json`, `asyncio` – Configuration and tooling support

### Client:

* `langchain`, `langgraph`, `langchain_groq` – Agent orchestration and Groq model interface
* `rich` – CLI rendering
* `mcp` – Client/server protocol management

---

## 🌐 APIs Used

* `GET /markets/{condition_id}` – Market metadata
* `GET /orderbook/{token_id}` – Orderbook details
* `GET /prices-history` – Historical prices

---

## ⚙️ Installation

### 1. Install the uv CLI (optional if using uv)

#### Windows (PowerShell as Administrator):

```bash
irm https://astral.sh/uv/install.ps1 | iex
```

#### macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Or via pip / pipx:

```bash
pip install uv
pipx install uv
```

### 2. Clone the Project

```bash
git clone https://github.com/himanshu/polygon-custom-mcp.git
cd polygon-custom-mcp
```

### 3. Set Up Environment

```bash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
```

### 4. Configure `.env`

```
CLOB_HOST=https://clob.polymarket.com
PK=YOUR_PRIVATE_KEY
CLOB_API_KEY=YOUR_CLOB_API_KEY
CLOB_SECRET=YOUR_CLOB_SECRET
CLOB_PASS_PHRASE=YOUR_CLOB_PASSPHRASE
CHROMA_PERSIST_DIR=.chroma
GROQ_API_KEY=YOUR_GROQ_API_KEY
```

Create a local `.env` file (do not commit this to GitHub) and paste your credentials there.

---

## 🚀 Running the MCP Server

```bash
python server.py
```

Output:

```
[MCP] polygon-custom-mcp listening on stdio...
```

---

## 💻 Running the CLI Client

```bash
python client.py
```

* Prompts for Groq API key.
* Starts interactive multi-turn chat.
* Accepts multi-line input.

### Example queries:

* "What is the probability that Trump extends the tariff pause in 30 days?"
* "Forecast for market 0x1234 for 7, 30, 90 days."

---

## 🧪 Example Use Case

> "Here is my portfolio of mutual funds. How would Trump’s tariff extension scenario affect ROI?"

1. Agent identifies relevant market via `list_all_prediction_markets()`
2. Extracts `condition_id`
3. Forecasts outcome probabilities via `forecast_scenario_probabilities()`
4. Outputs results as Markdown tables with explanation

---

## 🖥 MCP Integration with Claude Desktop

To use this with Claude Desktop (or other MCP-compatible apps):

1. Navigate to your Claude config:

   * Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   * macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Add this block:

```json
{
  "mcpServers": {
    "polygon-custom-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\YourUsername\\path\\to\\polygon-custom-mcp",
        "run",
        "server.py"
      ]
    }
  }
}
```

> 🔐 Replace the file paths and arguments accordingly. Use double backslashes on Windows.

> 🐳 For other integrations like Brave Web Search, Docker must be installed: [Docker install guide](https://docs.docker.com/get-docker/)

---

## 📁 Project Structure

```
polygon-custom-mcp/
├── client.py             # CLI chat agent using LangChain and Groq
├── server.py             # Main MCP server with tool implementations and FastMCP integration
├── get_api.py            # Handles retrieval of Polymarket API credentials via py-clob-client
├── index.py              # Indexes market data using Chroma DB, manages embedding and storage
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project metadata (used with uv or pipx)
├── testing.ipynb         # Jupyter notebook for experiments and manual tool testing
├── .env                  # Environment config file with credentials (excluded from version control)
├── uv.lock               # Lockfile for uv package manager
├── README.md             # Project documentation
```

---

## ✊ Credits

* **Groq + LangChain** for fast LLM orchestration
* **Polymarket** for decentralized prediction market data
* **FastMCP** for tool integration architecture

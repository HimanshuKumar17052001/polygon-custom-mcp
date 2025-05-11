# polygon-custom-mcp

A custom MCP server for Polymarket's CLOB API, built with Python and uv.

## Overview

This MCP server exposes four tools:

1. `list_all_prediction_markets`: Search prediction markets by keyword or ID  
2. `list_prediction_market_orderbook`: Fetch live orderbook (best bid/ask) for each outcome  
3. `list_prediction_market_graph`: Retrieve historical price series for a market  
4. `simulate_portfolio_impact`: Simulate portfolio ROI under two scenarios based on a two-outcome market

## Prerequisites

- OS: Windows, macOS, or Linux  
- Python: 3.8+  
- uv package manager (installed globally)  
- Virtual environment (recommended)  
- Environment variables (in a `.env` file):
  ```dotenv
  CLOB_HOST=https://clob.polymarket.com
  PK=<your-Polymarket-private-key>
  CLOB_API_KEY=<your-API-key>
  CLOB_SECRET=<your-API-secret>
  CLOB_PASS_PHRASE=<your-API-passphrase>
  CHROMA_PERSIST_DIR=./.chroma  # optional, defaults to ./.chroma
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

- **main.py**: MCP server implementation  
- **index.py**: One‑off indexer to load all markets into Chroma  
- **get_api.py**: Helper to derive a new API key  
- **requirements.txt**: Python dependencies  
- **.env**: your Polymarket credentials (never commit!)

## Installation

1. **Install uv CLI**  
   - Windows (PowerShell as Administrator):
     ```powershell
     irm https://astral.sh/uv/install.ps1 | iex
     ```
   - macOS / Linux:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - Or via pip / pipx:
     ```bash
     pip install uv
     pipx install uv
     ```

2. **Clone & set up**  
   ```bash
   git clone https://github.com/himanshu/polygon-custom-mcp.git
   cd polygon-custom-mcp
   ```

3. **Create & activate virtualenv**  
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\Activate.ps1
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Index all markets
```bash
python index.py
```

### Run the MCP server
```bash
uv run main.py
# or
python main.py
```
It will listen on stdin/stdout for MCP JSON‑RPC.

## Configuring Claude Desktop

Edit your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "polygon-custom-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\YourUsername\\path\\to\\polygon-custom-mcp",
        "run",
        "main.py"
      ]
    }
  }
}
```

- Use double backslashes in Windows paths.
- Restart Claude Desktop after changes.

## Tools

- **list_all_prediction_markets**  
  - Args: `query?: string`, `condition_id?: string`
  - Returns market summaries.

- **list_prediction_market_orderbook**  
  - Args: `condition_id: string`
  - Returns live bids/asks.

- **list_prediction_market_graph**  
  - Args: `condition_id: string`, optional interval/fidelity.
  - Returns historical yes/no series.

- **simulate_portfolio_impact**  
  - Args:  
    - `condition_id: string` (two‑outcome pause market)  
    - `portfolio: [{name, cost, market}]`  
    - `roi_if_extended: float`  
    - `roi_if_not_extended: float`  
  - Returns probabilities, scenario ROIs, and expected ROI.

## License

MIT

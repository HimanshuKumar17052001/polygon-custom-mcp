# polygon-custom-mcp

A custom MCP server for Polymarket's CLOB API, built with Python and uv.

## Overview

This MCP server exposes three tools to Claude (or any MCP-compatible client):

* `list_all_prediction_markets`: Search prediction markets by keyword
* `list_prediction_market_orderbook`: Fetch live orderbook (best bid/ask) for each outcome
* `list_prediction_market_graph`: Retrieve historical price series for a market

## Prerequisites

- OS: Windows, macOS, or Linux
- Python: 3.8+
- uv package manager (installed globally)
- Virtual environment (recommended)
- Environment variables (in a `.env` file):

```
CLOB_HOST=https://clob.polymarket.com
PK=<your-Polymarket-private-key>
CLOB_API_KEY=<your-API-key>
CLOB_SECRET=<your-API-secret>
CLOB_PASS_PHRASE=<your-API-passphrase>
GROQ_API_KEY=<your-API-key>
```

## Project Structure

```
polygon-custom-mcp/
├── main.py
├── requirements.txt
├── .env
└── README.md
```

* `main.py`: MCP server implementation
* `requirements.txt`: Python dependencies
* `.env`: your Polymarket credentials (never commit to Git!)

## Installation

### 1. Install the uv CLI

Windows (PowerShell as Administrator):
```
irm https://astral.sh/uv/install.ps1 | iex
```

macOS / Linux (bash, zsh, etc.):
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via pip / pipx:
```
pip install uv
pipx install uv
```

### 2. Clone & Set Up the Project

```
git clone https://github.com/himanshu/polygon-custom-mcp.git
cd polygon-custom-mcp
```

### 3. Initialize your uv project

```
uv init
```

### 4. Create & activate a virtual environment

Windows PowerShell:
```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS / Linux:
```
python -m venv venv
source venv/bin/activate
```

### 5. Install dependencies

```
uv add mcp[cli] py-clob-client python-dotenv requests
```

-- OR --

```
pip install -r requirements.txt
```

## Configuring Claude Desktop with our custom MCP and Brave Web Search MCP 

For Claude Desktop, edit your `claude_desktop_config.json` file:
- Windows: Located at `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: Located at `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the following to your configuration file (replace the directory path with your actual project location):

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "BRAVE_API_KEY",
        "mcp/brave-search"
      ],
      "env": {
        "BRAVE_API_KEY": "YOUR_API_KEY"
      }
    },
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

**Important Notes:**

- To use the **Brave Search** MCP tool, you **must** have **Docker installed** on your machine. See the [official Docker installation guide](https://docs.docker.com/get-docker/) for instructions.
- Replace `YOUR_API_KEY` with your actual Brave Search API key.
- Replace `C:\\Users\\YourUsername\\path\\to\\polygon-custom-mcp` with the path to your project directory.
- Use double backslashes (`\\`) for Windows file paths in JSON.


## Running the Server

```
uv run main.py
```

You should see:
```
[MCP] polygon-custom-mcp listening on stdio...
```

## Testing the Tools in Claude Desktop

Once you have set up the MCP server:

1. Start the server by running `uv run main.py` in your terminal
2. Launch Claude Desktop
3. In the Claude Desktop interface, you can interact with the Polymarket tools and Brave Web Search using natural language:

For example, you can ask Claude:
- "Search for Bitcoin prediction markets on Polymarket"
- "What's the current orderbook for the market with condition ID 0x1234...?"
- "Show me the price history for market 0xabcd... over the past week"

Claude will automatically utilize the appropriate Polymarket tools and Brave Web Search to fetch and display the requested information.

Notes:
- For `list_prediction_market_orderbook` and `list_prediction_market_graph` commands, you'll need to provide a valid Polymarket condition ID v.i.z. ID of the market
- You can find condition IDs by first searching for markets using the `list_all_prediction_markets` functionality
- If MCP fails to load in Claude Desktop, then quit the Claude Desktop and launch it again, it would be fixed

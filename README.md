# polygon-custom-mcp

A custom MCP server for Polymarket's CLOB API, built with Python and uv.

## Overview

This MCP server exposes three tools to Claude (or any MCP-compatible client):

* `list_markets`: Search prediction markets by keyword
* `get_orderbook`: Fetch live orderbook (best bid/ask) for each outcome
* `get_history`: Retrieve historical price series for a market

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

## Configuration for Claude Desktop

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
- Replace `YOUR_API_KEY` with your actual Brave Search API key
- Replace `C:\\Users\\YourUsername\\path\\to\\polygon-custom-mcp` with the actual path to your project folder
- Use double backslashes (\\\\) for Windows file paths in the JSON configuration

## Running the Server

```
uv run main.py
```

You should see:
```
[MCP] polygon-custom-mcp listening on stdio...
```

## Testing the Tools

Use your MCP client or the CLI to call:

```
mcp call polygon-custom-mcp list_markets '{"query":"bitcoin"}'
mcp call polygon-custom-mcp get_orderbook '{"condition_id":"0x..."}'
mcp call polygon-custom-mcp get_history '{"condition_id":"0x...","interval":"1d"}'
```

Replace `0x...` with an actual condition_id.

# Polymarket Custom MCP

A custom [MCP](https://github.com/microsoft/mcp) (Multi-Tool Control Protocol) server for interacting with Polymarket prediction markets on Polygon. This toolkit exposes tools to search markets, fetch live orderbooks, and retrieve historical price data, making it easy to integrate with LLMs (like Claude, GPT-4, etc.) or other MCP-compatible clients.

## Features
- **List prediction markets** by search query
- **Fetch live orderbooks** for all outcomes in a market
- **Retrieve historical price series** for a market
- Designed for use with LLMs and MCP clients

## Requirements
- Python 3.12+
- Polygon/Polymarket API credentials (see Environment Variables)

## Installation

1. **Clone the repository:**
   ```sh
git clone <YOUR_GITHUB_URL>
cd polygon-custom-mcp
```

2. **Install dependencies:**
   ```sh
pip install -r requirements.txt
# or, if using poetry or pip-tools, use your preferred tool
```

3. **Set up environment variables:**
   Create a `.env` file in the project root with the following variables:
   ```env
PK=your_polygon_private_key
CLOB_API_KEY=your_clob_api_key
CLOB_SECRET=your_clob_secret
CLOB_PASS_PHRASE=your_clob_passphrase
CLOB_HOST=https://clob.polymarket.com  # (optional, default shown)
```

## Usage

Start the MCP server (stdio transport):
```sh
python main.py
```

The server will expose the following tools to any MCP-compatible client:

### Tools
- `list_markets`: Search prediction markets by query
- `get_orderbook`: Get live orderbook for all outcomes of a market
- `get_history`: Get historical price series for a market

### Example MCP Query (pseudo-code)
```
# List markets containing 'US election'
{
  "tool": "list_markets",
  "arguments": {"query": "US election"}
}

# Get orderbook for a specific market
{
  "tool": "get_orderbook",
  "arguments": {"condition_id": "0x..."}
}

# Get price history for a market
{
  "tool": "get_history",
  "arguments": {"condition_id": "0x...", "interval": "1d"}
}
```

## Environment Variables
- `PK`: Polygon private key (required)
- `CLOB_API_KEY`: Polymarket CLOB API key (required)
- `CLOB_SECRET`: Polymarket CLOB API secret (required)
- `CLOB_PASS_PHRASE`: Polymarket CLOB API passphrase (required)
- `CLOB_HOST`: (optional) CLOB API host URL (default: `https://clob.polymarket.com`)

## License
MIT

## Acknowledgments
- [Polymarket](https://polymarket.com)
- [MCP Protocol](https://github.com/microsoft/mcp)

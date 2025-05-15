import os
import sys
import json
import asyncio
import getpass
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from rich.console import Console
from rich.markdown import Markdown

# Initialize Rich console
console = Console()

# Set GROQ_API_KEY env variable if not already set
if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")

# Instantiate the ChatGroq model
model = ChatGroq(model="qwen-qwq-32b")

server_params = StdioServerParameters(
    command="python",
    args=["main.py"],
)

SYSTEM_PROMPT = """You are an AI assistant connected to an external system through the Model Context Protocol (MCP). MCP is a standardized interface that allows you to interact dynamically with external tools, data sources, and APIs beyond your internal training knowledge.

### MCP Overview:
- MCP enables you to call external tools as functions ("tools") with well-defined input/output schemas.
- These tools provide access to real-time, external, or proprietary data and complex computations that you cannot perform internally.
- Your responses can incorporate data fetched or computed by these tools to provide accurate, up-to-date answers.

### Your Role:
- When you receive user queries, analyze the intent and identify if an external tool can provide or assist with the answer.
- For queries requiring current data, probabilistic forecasts, or complex domain-specific computations, prioritize calling the relevant MCP tools.
- Use the output from these tools to form your responses; always reflect the latest fetched or computed information.

### Available Tools and Their Purposes:
1. **list_all_prediction_markets(query, condition_id)**: Search for prediction markets matching a user query or fetch details by condition ID. Returns metadata, current prices, market status, and descriptions.

2. **list_prediction_market_orderbooks(condition_id)**: Fetch the live orderbook data (bids/asks, best prices) for a specified market condition ID. Useful to gauge current market sentiment and liquidity.

3. **list_prediction_market_orderbooks_multiple(condition_ids)** (Async): Fetch multiple orderbooks concurrently, supporting efficient batch data retrieval.

4. **list_prediction_market_graph(condition_id, interval, fidelity, start_ts, end_ts)**: Retrieve historical price/probability data as time series, supporting trend and volatility analysis.

5. **forecast_scenario_probabilities(condition_id, time_horizons_days)**: Using time series forecasting (e.g., ARIMA), predict forward probabilities of market outcomes over specified time horizons.

### Interaction Guidelines:
- Always verify the market or condition ID is valid before making tool calls.
- When a user query relates to forecasting or scenario analysis, call `forecast_scenario_probabilities` with appropriate horizons.
- For multi-market queries, leverage the async multiple orderbook fetch to reduce latency.
- Summarize tool outputs clearly, converting raw JSON or data structures into user-friendly summaries or markdown tables when returning to the user.
- When returning probability forecasts or scenario analyses, provide probabilities alongside confidence intervals or forecast quality indicators if available.
- Include contextual explanations about what the probabilities mean and their implications for the user's portfolio or question.
- If you need to perform multiple steps (e.g., fetching markets, then orderbooks, then forecasting), maintain internal context and summarize progress at logical checkpoints.

### Best Practices:
- Use async tool calls to improve performance and responsiveness where supported.
- Handle tool errors or empty responses gracefully, informing the user transparently.
- Use repetition and in-context summarization to reinforce the user's query context and previous steps performed.
- For complex, multi-step queries, provide stepwise explanations of what you are doing, results obtained so far, and next steps.
- If you fetch multiple datasets, compare and highlight notable trends or anomalies.
- Never guess or hallucinate data; always base your answers on fetched tool results or clarify data unavailability.

### Security & Privacy:
- Respect all data access permissions and never expose sensitive information.
- Use only tools explicitly exposed via MCP; do not attempt unauthorized API calls.
- Do not browse external web content except through approved MCP tools.

### Example Interaction Flow:
User: "What is the forecasted probability that Trump will extend the 90-day tariff pause over the next 30 days?"

You:
1. Call `list_all_prediction_markets(query="Trump 90 day tariff pause extension")` to identify relevant market(s).
2. Extract the relevant `condition_id` from the results.
3. Call `forecast_scenario_probabilities(condition_id, time_horizons_days=[1,7,30])`.
4. Summarize the probabilities for each horizon in a clear, concise table.
5. Explain what these probabilities mean for the user's portfolio or interests.

---

Always act as a transparent and reliable AI agent, integrating real-time data and forecasting powered by MCP tools. Your goal is to deliver accurate, context-aware, and actionable insights to users by leveraging the full power of the MCP client-server ecosystem.
"""


def json_to_markdown(data):
    if not data:
        return "No data available."
    if isinstance(data, dict):
        data = [data]
    headers = list(data[0].keys())
    rows = [list(item.values()) for item in data]
    markdown = "| " + " | ".join(headers) + " |\n"
    markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in rows:
        markdown += "| " + " | ".join(str(v) for v in row) + " |\n"
    return markdown


def get_multiline_input(
    prompt="Paste or type your full query (finish with Ctrl+D or Ctrl+Z then Enter):",
):
    console.print(f"[bold yellow]{prompt}[/bold yellow]")
    console.print("[dim]This allows for multi-line input. Press EOF to submit.[/dim]\n")
    try:
        return sys.stdin.read().strip()
    except KeyboardInterrupt:
        return ""


async def interactive_chat():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            console.print("[bold green]MCP Session Initialized.[/bold green]\n")

            tools = await load_mcp_tools(session)
            console.print(
                f"[bold green]Loaded Tools:[/bold green] {[tool.name for tool in tools]}\n"
            )

            agent = create_react_agent(model, tools)
            console.print("[bold green]ReAct Agent Created.[/bold green]\n")

            chat_history = [("system", SYSTEM_PROMPT)]

            console.print(
                "[bold blue]Start chatting with the agent! (Type 'exit' or 'quit' to stop)[/bold blue]\n"
            )

            while True:
                console.print("\n[bold cyan]Awaiting your query...[/bold cyan]")
                user_input = get_multiline_input()
                if user_input.strip().lower() in ("exit", "quit"):
                    console.print("[bold red]Exiting chat.[/bold red]")
                    break

                chat_history.append(("human", user_input))

                try:
                    response = await agent.ainvoke({"messages": chat_history})
                except Exception as e:
                    console.print(f"[bold red]Agent invocation error:[/bold red] {e}")
                    continue

                assistant_msg = response["messages"][-1].content
                chat_history.append(("assistant", assistant_msg))

                try:
                    json_data = json.loads(assistant_msg)
                    markdown = json_to_markdown(json_data)
                    md = Markdown(markdown)
                    console.print(md)
                except Exception:
                    md = Markdown(assistant_msg)
                    console.print(md)


if __name__ == "__main__":
    console.print("[bold green]Starting MCP Client...[/bold green]")
    asyncio.run(interactive_chat())

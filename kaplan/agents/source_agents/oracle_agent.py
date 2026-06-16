# agents/source_agents/oracle_agent.py
# import asyncio
# from google.adk.agents import Agent
# from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
# from mcp.client.stdio import StdioServerParameters

# oracle_agent = Agent(
#     name="oracle_agent",
#     model="gemini-2.5-flash",
#     description="Fetches revenue and new starts data from Oracle via MCP. Read-only.",
#     instruction="""You are a read-only Oracle data agent for Kaplan's FP&A system.

# Use the query_oracle tool to fetch data. Return raw records only.
# Do NOT perform calculations — just fetch and return data.
# Always confirm source as 'oracle' in your response.""",
#     tools=[
#     MCPToolset(
#         connection_params=StdioConnectionParams(
#             server_params=StdioServerParameters(
#                 command="python",
#                 args=["mcp_servers/oracle_server.py"]
#             )
#         )
#     )
# ]
# )
# agents/source_agents/oracle_agent.py
# ──────────────────────────────────────────────────────────────────────────────
# ORACLE AGENT — Revenue & New Starts
# ──────────────────────────────────────────────────────────────────────────────
#
# WHAT IT DOES:
#   Connects to Oracle (FREEPDB1) via the MCP stdio server and exposes two tools:
#     query_oracle_revenue    → fp_revenue table (period, business_unit, channel, amount)
#     query_oracle_new_starts → fp_new_starts table (period, business_unit, channel, segment, count)
#
# MCP TRANSPORT — WHY STDIO:
#   ADK's MCPToolset spawns oracle_server.py as a child process and communicates
#   over stdin/stdout. This avoids needing a long-running MCP HTTP server and
#   keeps the deployment simple (just `python mcp_servers/oracle_server.py`).
#   The tradeoff: each tool call starts/stops the subprocess unless the MCP
#   server uses connection pooling (the oracle_server.py does NOT pool — each
#   call opens a new oracledb connection). For high-frequency queries, consider
#   a persistent SSE transport instead.
#
# LATENCY:
#   oracledb connection open: ~50–100ms (Docker, loopback)
#   Query execution: ~20–80ms depending on table size
#   MCP serialisation: ~10ms
#   Total per call: ~80–200ms
#
# ──────────────────────────────────────────────────────────────────────────────
from google.adk.agents import Agent
from google.adk.tools.application_integration_tool.application_integration_toolset import (
    ApplicationIntegrationToolset,
)
oracle_agent = Agent(
    name="oracle_agent",
    model="gemini-2.5-flash",
    description=(
        "Fetches GAAP revenue and new student starts from Oracle (FREEPDB1). "
        "Source of record for all revenue and new-enrollment metrics."
    ),
    tools=[
        ApplicationIntegrationToolset(
            project="robust-atrium-406105",
            location="us-central1",
            connection="oracledb",  
            entity_operations={
                "fp_revenue":    ["LIST", "GET"],
                "fp_new_starts": ["LIST", "GET"],
            },
            actions=[],
            tool_name_prefix="oracle",
            tool_instructions="""Query Oracle database tables.
fp_revenue fields: period (Q1_2025 format), business_unit, channel, amount.
fp_new_starts fields: period, business_unit, channel, segment, count.
Segments: Degree, Certificate. Channels: Direct.""",
        )
    ],
    instruction="""You are Kaplan's Oracle database agent. Fetch data only — no calculations.

SELF-SELECTION RULE (check this FIRST, every time)
If "oracle_agent" does NOT appear in agents_to_call in the routing context:
  Respond with exactly: ORACLE_AGENT: NOT_APPLICABLE
  Then stop. Do not query any data.

TABLES:
  fp_revenue:    period, business_unit, channel, amount
  fp_new_starts: period, business_unit, channel, segment, count

RULES:
  • Always use Q[N]_YYYY format.
  • Return ALL matching records.
  • Never calculate.
  • Cite: Oracle (FREEPDB1)""",
)
# from google.adk.agents import Agent
# from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
# from mcp.client.stdio import StdioServerParameters

# redshift_agent = Agent(
#     name="redshift_agent",
#     model="gemini-2.5-flash",
#     description="Fetches census and headcount data from Redshift via MCP. Read-only.",
#     instruction="""You are a read-only Redshift data agent for Kaplan's FP&A system.

# Use the query_redshift tool to fetch data. Return raw records only.
# Do NOT perform calculations.""",
#     tools=[
#     MCPToolset(
#         connection_params=StdioConnectionParams(
#             server_params=StdioServerParameters(
#                 command="python",
#                 args=["mcp_servers/redshift_server.py"]
#             )
#         )
#     )
# ]
# )

# agents/source_agents/redshift_agent.py
# ──────────────────────────────────────────────────────────────────────────────
# REDSHIFT AGENT — Census / Headcount
# ──────────────────────────────────────────────────────────────────────────────
#
# WHAT IT DOES:
#   Connects to Amazon Redshift via MCP stdio and exposes:
#     query_redshift(metric, period, filters)
#       → fp_census table (period, business_unit, segment, headcount)
#
# USE CASE:
#   Census headcount is the denominator in "revenue per student" calculations.
#   When bi_agent needs revenue per student, it calls oracle_agent for the
#   numerator (revenue) and redshift_agent for the denominator (headcount).
#
# NOTE (as of current codebase):
#   Redshift is still running on mock/Docker data. The MCP server
#   (mcp_servers/redshift_server.py) returns mock records.
#   Agent behaviour is identical once real Redshift is connected.
#
# ──────────────────────────────────────────────────────────────────────────────

from google.adk.agents import Agent
from google.adk.tools.application_integration_tool.application_integration_toolset import (
    ApplicationIntegrationToolset,
)

redshift_agent = Agent(
    name="redshift_agent",
    model="gemini-2.5-flash",
    description=(
        "Fetches student census/headcount from Redshift (fp_census). "
        "Used as denominator for revenue-per-student calculations."
    ),
    tools=[
        ApplicationIntegrationToolset(
            project="robust-atrium-406105",
            location="us-central1",
            connection="redshift",
            entity_operations={
                "fp_census": ["LIST", "GET"],
            },
            actions=[],
            tool_name_prefix="redshift",
            tool_instructions="""Query Redshift fp_census table.
Key fields: period (Q1_2025 format), business_unit, segment, headcount.
Segments: Degree, Certificate.
Business Units: Higher Education, Supplemental.""",
        )
    ],
    instruction="""You are Kaplan's Redshift data agent. Fetch data only — no calculations.

SELF-SELECTION RULE (check this FIRST, every time)
If "redshift_agent" does NOT appear in agents_to_call in the routing context:
  Respond with exactly: REDSHIFT_AGENT: NOT_APPLICABLE
  Then stop. Do not query any data.

TABLE:
  fp_census: period (Q1_2025), business_unit, segment, headcount

RULES:
  • headcount is the denominator for revenue per student.
  • Q[N]_YYYY format for period.
  • Return ALL matching records.
  • Never calculate.
  • Cite: Redshift (fp_census)""",
)
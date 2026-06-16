# from google.adk.agents import Agent
# from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
# from mcp.client.stdio import StdioServerParameters

# mssql_agent = Agent(
#     name="mssql_agent",
#     model="gemini-2.5-flash",
#     description="Fetches enrollment and program data from MS SQL Server via MCP. Read-only.",
#     instruction="""You are a read-only MS SQL Server data agent for Kaplan's FP&A system.

# Use the query_mssql tool to fetch data. Return raw records only.
# Do NOT perform calculations.""",
#     tools=[
#         MCPToolset(
#             connection_params=StdioConnectionParams(
#                 server_params=StdioServerParameters(
#                     command="python",
#                     args=["mcp_servers/mssql_server.py"]
#                 )
#             )
#         )
#     ]
# )

# agents/source_agents/mssql_agent.py
# ──────────────────────────────────────────────────────────────────────────────
# MSSQL AGENT — Enrollment & Drop Rate
# ──────────────────────────────────────────────────────────────────────────────
#
# WHAT IT DOES:
#   Connects to MS SQL Server (kaplan_db) via MCP stdio and exposes:
#     query_mssql_enrollment → fp_enrollment table
#       (period, program, business_unit, enrolled_count, drop_rate)
#
# NOTE ON DROP_RATE:
#   The field is already a percentage value (8.5 means 8.5%, not 0.085).
#   bi_agent should be aware of this when computing averages.
#
# ──────────────────────────────────────────────────────────────────────────────
# from google.adk.agents import Agent
# from google.adk.tools.application_integration_tool.application_integration_toolset import (
#     ApplicationIntegrationToolset,
# )
# mssql_agent = Agent(
#     name="mssql_agent",
#     model="gemini-2.5-flash",
#     description=(
#         "Fetches enrollment counts and drop-rate data from MS SQL Server (kaplan_db). "
#         "Source of record for program performance and student retention metrics."
#     ),
#     tools=[
#         ApplicationIntegrationToolset(
#             project="robust-atrium-406105",
#             location="us-central1",
#             connection="kaplansqlserver",
#             entity_operations={
#                 "fp_enrollment": ["LIST", "GET"],
#             },
#             actions=[],
#             tool_name_prefix="mssql",
#             tool_instructions="""Query MS SQL Server fp_enrollment table.
# Key fields: period (Q1_2025 format), program, business_unit, enrolled_count, drop_rate.
# Programs: MBA Program, Data Science, Bar Exam Prep, CFA Prep.
# Business Units: Higher Education, Supplemental.
# drop_rate is a percentage value (8.5 = 8.5%).""",
#         )
#     ],
#     instruction="""You are Kaplan's MS SQL Server agent. Fetch data only — no calculations.

# SELF-SELECTION RULE (check this FIRST, every time)
# If "mssql_agent" does NOT appear in agents_to_call in the routing context:
#   Respond with exactly: MSSQL_AGENT: NOT_APPLICABLE
#   Then stop. Do not query any data.

# TABLE:
#   fp_enrollment: period (Q1_2025), program, business_unit, enrolled_count, drop_rate

# RULES:
#   • Q[N]_YYYY format for period.
#   • Return ALL matching records.
#   • Never calculate.
#   • Cite: MS SQL Server (kaplan_db)""",
# )

from google.adk.agents import Agent
from google.adk.tools.application_integration_tool.application_integration_toolset import (
    ApplicationIntegrationToolset,
)

mssql_agent = Agent(
    name="mssql_agent",
    model="gemini-2.5-flash",
    description=(
        "Fetches leads, starts, enrollment, census, drops and channel data "
        "from MS SQL Server (rptobjects database). "
        "Primary source for all student funnel and retention metrics."
    ),
    tools=[
        ApplicationIntegrationToolset(
            project="robust-atrium-406105",
            location="us-central1",
            connection="kaplansqlserver",
            entity_operations={},
            actions=["ExecuteCustomQuery"],
            tool_name_prefix="mssql",
            tool_instructions="""Execute SQL queries against rptobjects SQL Server database.

DATABASE: rptobjects
SCHEMA: dbo

TABLE 1: dbo.techtonic
  Key metrics : Leads, Starts, grossStarts, reverseStarts, Enrolls
  Key dims    : yr, mnth, date, marketingChannelGroup, parent_marketingChannelGroup,
                channel, Vertical, School, Degree, milFlag, milCategory,
                b2bType, AccountGroup, campus, termCode, termStartDate, isReported
  Period filter: yr=YYYY AND mnth IN (1,2,3) for Q1 | (4,5,6) Q2 | (7,8,9) Q3 | (10,11,12) Q4
  Always filter: isReported = 1 unless told otherwise
  New Starts  : SUM(grossStarts) - SUM(reverseStarts)
  Net Starts  : SUM(Starts)

TABLE 2: dbo.fact_daily_metrics_detail
  Key metrics : census, census_month_end, drops, dropsLOA, dismissals,
                academicStarts, grads, grossEnrollments, netStarts
  ALWAYS JOIN : dbo.d_date ON Date_Key to get Year and Month
  Census      : filter census_month_end = 1 for point-in-time headcount
  Drop rate   : SUM(drops) / SUM(census) * 100

TABLE 3: dbo.d_date
  Purpose     : date dimension, join to fact_daily_metrics_detail on Date_Key
  Key columns : Date_Key, Year, Month, Day_Date

QUERY EXAMPLES:

  New starts Q1 2025:
    SELECT SUM(grossStarts) - SUM(reverseStarts) AS net_starts,
           marketingChannelGroup, Vertical
    FROM dbo.techtonic
    WHERE yr=2025 AND mnth IN (1,2,3) AND isReported=1
    GROUP BY marketingChannelGroup, Vertical

  Total leads Q1 2025:
    SELECT SUM(Leads) AS total_leads, marketingChannelGroup
    FROM dbo.techtonic
    WHERE yr=2025 AND mnth IN (1,2,3) AND isReported=1
    GROUP BY marketingChannelGroup

  Channel mix Q1 2025 vs Q1 2024:
    SELECT yr, mnth, marketingChannelGroup,
           SUM(Leads) AS leads, SUM(grossStarts) - SUM(reverseStarts) AS starts
    FROM dbo.techtonic
    WHERE yr IN (2024,2025) AND mnth IN (1,2,3) AND isReported=1
    GROUP BY yr, mnth, marketingChannelGroup
    ORDER BY yr, marketingChannelGroup

  Census month-end Q1 2025:
    SELECT SUM(f.census) AS headcount, d.Year, d.Month
    FROM dbo.fact_daily_metrics_detail f
    JOIN dbo.d_date d ON f.Date_Key = d.Date_Key
    WHERE d.Year=2025 AND d.Month IN (1,2,3)
    AND f.census_month_end=1
    GROUP BY d.Year, d.Month

  Drop rate Q1 2025:
    SELECT d.Year, d.Month,
           SUM(f.drops) AS total_drops,
           SUM(f.census) AS total_census,
           CAST(SUM(f.drops) AS FLOAT) / NULLIF(SUM(f.census),0) * 100 AS drop_rate_pct
    FROM dbo.fact_daily_metrics_detail f
    JOIN dbo.d_date d ON f.Date_Key = d.Date_Key
    WHERE d.Year=2025 AND d.Month IN (1,2,3)
    GROUP BY d.Year, d.Month""",
        )
    ],
    instruction="""You are Kaplan's MS SQL Server data agent. Fetch data only — no calculations.

SELF-SELECTION RULE (check this FIRST, every time)
If "mssql_agent" does NOT appear in agents_to_call in the routing context:
  Respond with exactly: MSSQL_AGENT: NOT_APPLICABLE
  Then stop. Do not query any data.

DATABASE: rptobjects (SQL Server)

TABLES:
  dbo.techtonic
    → Leads, Starts, grossStarts, reverseStarts, Enrolls
    → Dims: yr, mnth, marketingChannelGroup, channel, Vertical, School,
            Degree, milFlag, b2bType, campus, termCode, isReported
    → Always filter: isReported = 1
    → Period: yr=YYYY AND mnth IN (...) — Q1=(1,2,3) Q2=(4,5,6) Q3=(7,8,9) Q4=(10,11,12)

  dbo.fact_daily_metrics_detail (always join dbo.d_date ON Date_Key)
    → census (use census_month_end=1 for snapshot)
    → drops, dropsLOA, dismissals, academicStarts, grads

RULES:
  • Write clean SQL — no database prefix, just dbo.tablename
  • Return ALL matching records — do not add extra filters
  • Never calculate derived metrics inline — return raw aggregates
  • On error: return the error message as-is
  • On empty result: return MSSQL_AGENT: NO_DATA for [period]
  • Cite: SQL Server (rptobjects — dbo.techtonic / dbo.fact_daily_metrics_detail)""",
)
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

# from google.adk.agents import Agent
# from google.adk.tools.application_integration_tool.application_integration_toolset import (
#     ApplicationIntegrationToolset,
# )

# mssql_agent = Agent(
#     name="mssql_agent",
#     model="gemini-2.5-flash",
#     description=(
#         "Fetches leads, starts, enrollment, census, drops and channel data "
#         "from MS SQL Server (rptobjects database). "
#         "Primary source for all student funnel and retention metrics."
#     ),
#     tools=[
#         ApplicationIntegrationToolset(
#             project="robust-atrium-406105",
#             location="us-central1",
#             connection="kaplansqlserver",
#             entity_operations={},
#             actions=["ExecuteCustomQuery"],
#             tool_name_prefix="mssql",
#             tool_instructions="""Execute SQL queries against rptobjects SQL Server database.

# DATABASE: rptobjects
# SCHEMA: dbo

# TABLE 1: dbo.techtonic
#   Key metrics : Leads, Starts, grossStarts, reverseStarts, Enrolls
#   Key dims    : yr, mnth, date, marketingChannelGroup, parent_marketingChannelGroup,
#                 channel, Vertical, School, Degree, milFlag, milCategory,
#                 b2bType, AccountGroup, campus, termCode, termStartDate, isReported
#   Period filter: yr=YYYY AND mnth IN (1,2,3) for Q1 | (4,5,6) Q2 | (7,8,9) Q3 | (10,11,12) Q4
#   Always filter: isReported = 1 unless told otherwise
#   New Starts  : SUM(grossStarts) - SUM(reverseStarts)
#   Net Starts  : SUM(Starts)

# TABLE 2: dbo.fact_daily_metrics_detail
#   Key metrics : census, census_month_end, drops, dropsLOA, dismissals,
#                 academicStarts, grads, grossEnrollments, netStarts
#   ALWAYS JOIN : dbo.d_date ON Date_Key to get Year and Month
#   Census      : filter census_month_end = 1 for point-in-time headcount
#   Drop rate   : SUM(drops) / SUM(census) * 100

# TABLE 3: dbo.d_date
#   Purpose     : date dimension, join to fact_daily_metrics_detail on Date_Key
#   Key columns : Date_Key, Year, Month, Day_Date

# QUERY EXAMPLES:

#   New starts Q1 2025:
#     SELECT SUM(grossStarts) - SUM(reverseStarts) AS net_starts,
#            marketingChannelGroup, Vertical
#     FROM dbo.techtonic
#     WHERE yr=2025 AND mnth IN (1,2,3) AND isReported=1
#     GROUP BY marketingChannelGroup, Vertical

#   Total leads Q1 2025:
#     SELECT SUM(Leads) AS total_leads, marketingChannelGroup
#     FROM dbo.techtonic
#     WHERE yr=2025 AND mnth IN (1,2,3) AND isReported=1
#     GROUP BY marketingChannelGroup

#   Channel mix Q1 2025 vs Q1 2024:
#     SELECT yr, mnth, marketingChannelGroup,
#            SUM(Leads) AS leads, SUM(grossStarts) - SUM(reverseStarts) AS starts
#     FROM dbo.techtonic
#     WHERE yr IN (2024,2025) AND mnth IN (1,2,3) AND isReported=1
#     GROUP BY yr, mnth, marketingChannelGroup
#     ORDER BY yr, marketingChannelGroup

#   Census month-end Q1 2025:
#     SELECT SUM(f.census) AS headcount, d.Year, d.Month
#     FROM dbo.fact_daily_metrics_detail f
#     JOIN dbo.d_date d ON f.Date_Key = d.Date_Key
#     WHERE d.Year=2025 AND d.Month IN (1,2,3)
#     AND f.census_month_end=1
#     GROUP BY d.Year, d.Month

#   Drop rate Q1 2025:
#     SELECT d.Year, d.Month,
#            SUM(f.drops) AS total_drops,
#            SUM(f.census) AS total_census,
#            CAST(SUM(f.drops) AS FLOAT) / NULLIF(SUM(f.census),0) * 100 AS drop_rate_pct
#     FROM dbo.fact_daily_metrics_detail f
#     JOIN dbo.d_date d ON f.Date_Key = d.Date_Key
#     WHERE d.Year=2025 AND d.Month IN (1,2,3)
#     GROUP BY d.Year, d.Month""",
#         )
#     ],
#     instruction="""You are Kaplan's MS SQL Server data agent. Fetch data only — no calculations.

# SELF-SELECTION RULE (check this FIRST, every time)
# If "mssql_agent" does NOT appear in agents_to_call in the routing context:
#   Respond with exactly: MSSQL_AGENT: NOT_APPLICABLE
#   Then stop. Do not query any data.

# DATABASE: rptobjects (SQL Server)

# TABLES:
#   dbo.techtonic
#     → Leads, Starts, grossStarts, reverseStarts, Enrolls
#     → Dims: yr, mnth, marketingChannelGroup, channel, Vertical, School,
#             Degree, milFlag, b2bType, campus, termCode, isReported
#     → Always filter: isReported = 1
#     → Period: yr=YYYY AND mnth IN (...) — Q1=(1,2,3) Q2=(4,5,6) Q3=(7,8,9) Q4=(10,11,12)

#   dbo.fact_daily_metrics_detail (always join dbo.d_date ON Date_Key)
#     → census (use census_month_end=1 for snapshot)
#     → drops, dropsLOA, dismissals, academicStarts, grads

# RULES:
#   • Write clean SQL — no database prefix, just dbo.tablename
#   • Return ALL matching records — do not add extra filters
#   • Never calculate derived metrics inline — return raw aggregates
#   • On error: return the error message as-is
#   • On empty result: return MSSQL_AGENT: NO_DATA for [period]
#   • Cite: SQL Server (rptobjects — dbo.techtonic / dbo.fact_daily_metrics_detail)""",
# )

# from google.adk.agents import Agent
# from google.adk.tools.application_integration_tool.application_integration_toolset import (
#     ApplicationIntegrationToolset,
# )

# mssql_agent = Agent(
#     name="mssql_agent",
#     model="gemini-2.5-flash",
#     description=(
#         "Fetches leads, starts, enrollment, census, drops and channel data "
#         "from MS SQL Server (rptobjects database). "
#         "Primary source for all student funnel and retention metrics."
#     ),
#     tools=[
#         ApplicationIntegrationToolset(
#             project="robust-atrium-406105",
#             location="us-central1",
#             connection="kaplansqlserver",
#             entity_operations={},
#             actions=["ExecuteCustomQuery"],
#             tool_name_prefix="mssql",
#             tool_instructions="""Execute SQL queries against the rptobjects SQL Server database.

# DATABASE: rptobjects (already scoped by the connector — do NOT prefix tables)
# SCHEMA: dbo

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABLE 1: dbo.techtonic
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Key metric columns:
#   Leads           — reportable lead count
#   starts          — finance starts (confirmed Kaplan definition)
#   grossStarts     — gross starts before reversals
#   reverseStarts   — reversed starts
#   Enrolls         — reportable enrollments

# Key dimension columns:
#   yr, mnth, date
#   marketingChannelGroup, parent_marketingChannelGroup, channel
#   Vertical, School, Degree, campus
#   milFlag, milCategory, b2bType
#   eaType, isReported, termCode, termStartDate

# Period filter pattern (yr_mnth):
#   Q1 → yr=YYYY AND mnth IN (1,2,3)
#   Q2 → yr=YYYY AND mnth IN (4,5,6)
#   Q3 → yr=YYYY AND mnth IN (7,8,9)
#   Q4 → yr=YYYY AND mnth IN (10,11,12)

# CRITICAL — do NOT add any default filters.
#   The routing context packet contains all required filters in filter_sql.
#   Apply ONLY what is in filter_sql. Never add isReported=1 or any other
#   filter unless it is explicitly present in the routing context.

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABLE 2: dbo.fact_daily_metrics_detail
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Key metric columns:
#   census              — daily active headcount (point-in-time, cannot sum across days)
#   census_month_end    — month-end snapshot flag
#   drops               — raw drops
#   dropsLOA            — leaves of absence
#   dismissals          — dismissals
#   returnAdminReEntry  — returns (subtracts from net drops)
#   grads               — graduation count
#   academicStarts      — academic starts

# Period filter pattern (date_key_join):
#   Always JOIN dbo.d_date ON Date_Key:
#     SELECT f.*, d.Year, d.Month
#     FROM dbo.fact_daily_metrics_detail f
#     JOIN dbo.d_date d ON f.Date_Key = d.Date_Key
#     WHERE d.Year=YYYY AND d.Month IN (...)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABLE 3: dbo.d_date
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Date dimension — always join to fact_daily_metrics_detail on Date_Key.
# Key columns: Date_Key, Year, Month, Day_Date, is_month_end

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# QUERY EXAMPLES (follow filter_sql from routing context exactly)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Finance starts Q1 2024:
#   SELECT SUM(starts) AS finance_starts
#   FROM dbo.techtonic
#   WHERE eaType IN ('New','ORS','ORS Prior Grad','ReApp','ORS COWD','Re-Admit')
#   AND yr=2024 AND mnth IN (1,2,3)

# Lead volume Q1 2024 (isReported filter comes from semantic layer, not hardcoded):
#   SELECT SUM(Leads) AS lead_volume
#   FROM dbo.techtonic
#   WHERE isReported=1
#   AND yr=2024 AND mnth IN (1,2,3)

# Census month-end Q1 2024:
#   SELECT SUM(f.census) AS headcount, d.Year, d.Month
#   FROM dbo.fact_daily_metrics_detail f
#   JOIN dbo.d_date d ON f.Date_Key = d.Date_Key
#   WHERE d.Year=2024 AND d.Month IN (1,2,3)
#   AND f.census_month_end=1
#   GROUP BY d.Year, d.Month

# Net drops Q1 2024:
#   SELECT SUM(f.dismissals)+SUM(f.drops)+SUM(f.dropsLOA)-SUM(f.returnAdminReEntry)
#          AS net_drops
#   FROM dbo.fact_daily_metrics_detail f
#   JOIN dbo.d_date d ON f.Date_Key = d.Date_Key
#   WHERE d.Year=2024 AND d.Month IN (1,2,3)

# Drop rate Q1 2024:
#   SELECT d.Year, d.Month,
#          SUM(f.drops)+SUM(f.dismissals)+SUM(f.dropsLOA)-SUM(f.returnAdminReEntry)
#            AS net_drops,
#          AVG(f.census) AS avg_active_census,
#          CAST(SUM(f.drops)+SUM(f.dismissals)+SUM(f.dropsLOA)-SUM(f.returnAdminReEntry)
#               AS FLOAT) / NULLIF(AVG(f.census),0) * 100 AS drop_rate_pct
#   FROM dbo.fact_daily_metrics_detail f
#   JOIN dbo.d_date d ON f.Date_Key = d.Date_Key
#   WHERE d.Year=2024 AND d.Month IN (1,2,3)
#   GROUP BY d.Year, d.Month""",
#         )
#     ],
#     instruction="""You are Kaplan's MS SQL Server data agent. Fetch data only — no calculations.

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SELF-SELECTION RULE — check this FIRST, every time
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# If "mssql_agent" does NOT appear in agents_to_call in the routing context:
#   Respond with exactly: MSSQL_AGENT: NOT_APPLICABLE
#   Stop. Do not run any query.

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SQL Server rptobjects — connector is already scoped to this database.
# Use table names WITHOUT the rptobjects. prefix — just dbo.tablename.

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HOW TO BUILD THE QUERY — read this carefully
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# The routing context packet from bi_agent contains everything you need:
#   table          → which table to query (dbo.techtonic or dbo.fact_daily_metrics_detail)
#   field          → which column(s) to aggregate
#   filter_sql     → the COMPLETE WHERE conditions — use these EXACTLY
#   period_filter_pattern → how to apply the time filter:
#       yr_mnth       → WHERE yr=YYYY AND mnth IN (N,N,N)
#       date_key_join → JOIN dbo.d_date d ON f.Date_Key=d.Date_Key WHERE d.Year=YYYY AND d.Month IN (N,N,N)
#   group_by_columns → GROUP BY clause if needed

# CRITICAL RULES:
#   1. Use filter_sql EXACTLY as provided — do NOT add any extra filters.
#   2. Do NOT add isReported=1 unless it is in filter_sql.
#   3. Do NOT add eaType filter unless it is in filter_sql.
#   4. Do NOT prefix tables with rptobjects. — just use dbo.tablename.
#   5. For dbo.techtonic — use period_filter_pattern=yr_mnth (yr and mnth columns exist directly).
#   6. For dbo.fact_daily_metrics_detail — use period_filter_pattern=date_key_join (JOIN dbo.d_date).
#   7. Return raw aggregates only — no derived calculations inline.
#   8. On empty result: return MSSQL_AGENT: NO_DATA for [period]
#   9. On error: return the error message as-is.

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CITE YOUR SOURCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Always end your response with:
#   Cite: SQL Server (rptobjects — [table you queried])""",
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
            tool_instructions="""Execute SQL queries against the rptobjects SQL Server database.

DATABASE: rptobjects (already scoped by the connector — do NOT prefix tables)
SCHEMA: dbo

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AVAILABLE TABLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TABLE 1: dbo.techtonic
  Metric columns (use what the routing context specifies):
    Leads           — reportable lead count (use SUM(Leads))
    grossStarts     — gross starts before reversals (use SUM(grossStarts))
    reverseStarts   — starts reversed/cancelled (use SUM(reverseStarts))
    Enrolls         — reportable enrollments (use SUM(Enrolls))
  
  Important: Finance Starts = SUM(grossStarts) - SUM(reverseStarts)
             The Starts column is always 0 — do NOT use it.
             Always filter AccountGroup = Post-Starts when querying starts.

  Dimension columns:
    yr, mnth, date, AccountGroup
    marketingChannelGroup, parent_marketingChannelGroup, channel
    Vertical, School, Degree, campus
    milFlag, milCategory, b2bType, eaType, isReported

  Period filter (yr_mnth pattern):
    WHERE yr=YYYY AND mnth IN (N,N,N)

TABLE 2: dbo.fact_daily_metrics_detail
  Metric columns:
    census              — daily headcount (point-in-time, never SUM across days)
    census_month_end    — 1 on the last day of each month
    drops               — raw drops
    dropsLOA            — leaves of absence
    dismissals          — dismissals
    returnAdminReEntry  — admin re-entries (subtract from net drops)
    grads               — graduation count

  Period filter (date_key_join pattern):
    Always JOIN dbo.d_date d ON f.Date_Key = d.Date_Key
    Then filter: WHERE d.Year=YYYY AND d.Month IN (N,N,N)

TABLE 3: dbo.d_date
  Date dimension — join to fact_daily_metrics_detail on Date_Key.
  Key columns: Date_Key, Year, Month, Day_Date, is_month_end

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW TO BUILD EVERY QUERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The routing context gives you everything. Build the query as:

  SELECT {calculation}
  FROM {table}
  WHERE {filter_sql}
  AND {period_filter}
  [GROUP BY {group_by_columns} if provided]

Where:
  {calculation}    → from routing context field "calculation"
                     e.g. SUM(grossStarts) - SUM(reverseStarts)
                     e.g. SUM(Leads)
  {table}          → from routing context field "table"
  {filter_sql}     → from routing context field "filter_sql" — use EXACTLY as given
  {period_filter}  → apply based on period_filter_pattern:
                     yr_mnth      → yr=YYYY AND mnth IN (N,N,N)
                     date_key_join → JOIN dbo.d_date d ON f.Date_Key=d.Date_Key
                                     WHERE d.Year=YYYY AND d.Month IN (N,N,N)
  {group_by_columns} → from routing context if provided

CRITICAL:
  — Never use the Starts column — it is always 0 in this database
  — Never add filters not present in filter_sql
  — Never hardcode eaType, isReported, or AccountGroup unless in filter_sql
  — Never prefix tables with rptobjects.""",
        )
    ],
    instruction="""You are Kaplan's MS SQL Server data agent. Fetch data only — no calculations.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SELF-SELECTION RULE — check this FIRST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If "mssql_agent" does NOT appear in agents_to_call in the routing context:
  Respond with exactly: MSSQL_AGENT: NOT_APPLICABLE
  Stop. Do not run any query.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW TO BUILD THE QUERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Read the routing context packet from bi_agent. It contains:
  table                → which table to query
  field                → which columns to aggregate
  filter_sql           → complete WHERE conditions
  calculation          → exact aggregation formula
  period_filter_pattern → yr_mnth or date_key_join
  group_by_columns     → GROUP BY clause if needed

Build the query dynamically from these values every time.
Do NOT use memorised or hardcoded queries.
Do NOT invent filters — use only what filter_sql provides.
Do NOT use the Starts column — it is always 0. Use grossStarts and reverseStarts.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUERY CONSTRUCTION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. table is dbo.techtonic → period filter is:
      WHERE yr=YYYY AND mnth IN (N,N,N)

2. table is dbo.fact_daily_metrics_detail → period filter is:
      JOIN dbo.d_date d ON f.Date_Key = d.Date_Key
      WHERE d.Year=YYYY AND d.Month IN (N,N,N)

3. calculation contains a subtraction (e.g. SUM(grossStarts) - SUM(reverseStarts)):
      Write it exactly as given — this is Finance Starts

4. filter_sql is provided → append it with AND after the period filter

5. group_by_columns is provided → append GROUP BY

6. On empty result → return: MSSQL_AGENT: NO_DATA for [period]

7. On error → return the error message as-is

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CITE YOUR SOURCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Always end with:
  Cite: SQL Server (rptobjects — [table queried])""",
)
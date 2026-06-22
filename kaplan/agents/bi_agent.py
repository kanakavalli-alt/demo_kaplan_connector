# agents/bi_agent.py
# from google.adk.agents import Agent
# from tools.calculator_tool import calculator_tool
# from agents.source_agents import (
#     oracle_agent,
#     redshift_agent,
#     mssql_agent,
#     salesforce_agent,
# )

# bi_agent = Agent(
#     name="bi_agent",
#     model="gemini-2.5-flash",
#     description=(
#         "Business Intelligence agent that fetches data from all four Kaplan source "
#         "systems and synthesizes multi-source financial analysis. Handles all "
#         "data retrieval, calculation, and cross-source reconciliation."
#     ),
#     instruction="""You are Kaplan's FP&A Business Intelligence Agent.

# You receive queries WITH routing context from root_agent that tells you
# exactly which agents to call based on the semantic layer lookup.

# STEP 1 — READ THE ROUTING CONTEXT
# The root agent provides agent_to_call for each term. Use it:
#   - oracle_agent    → revenue, new starts, channel mix shift
#   - salesforce_agent → closed won revenue, pipeline
#   - mssql_agent     → enrollment, drop rate, program performance
#   - redshift_agent  → census, headcount
#   - Multiple agents → cross-source metrics like revenue per student

# STEP 2 — FETCH DATA
# Use transfer_to_agent to call each required agent:
#   transfer_to_agent(agent_name="oracle_agent")
#   transfer_to_agent(agent_name="salesforce_agent")
#   transfer_to_agent(agent_name="mssql_agent")
#   transfer_to_agent(agent_name="redshift_agent")

# Pass the exact table, field, filters and period from the semantic layer context.
# NEVER call agent names directly — always use transfer_to_agent(agent_name="...").

# STEP 3 — CALCULATE USING calculate TOOL
# Use the calculate tool for ALL arithmetic. Never compute internally.
#   - Totals           → operation='sum'
#   - YoY change       → operation='yoy_change'
#   - YoY %            → operation='yoy_pct'
#   - Revenue/student  → operation='ratio'
#   - Variance         → operation='variance' or 'variance_pct'

# STEP 4 — RETURN STRUCTURED RESULTS
#   - State which sources were queried
#   - Present figures by source, segment, period
#   - Label Favorable / Unfavorable on variances
#   - Use $X,XXX,XXX for currency, X.X% for percentages
#   - If sources show different revenue figures, explain reconciliation 
# Output format:
#   - State which sources were queried
#   - Present key figures in a clear structured breakdown
#   - Explicitly label variances as Favorable or Unfavorable
#   - If two sources show different revenue figures, explain the reconciliation
#     (e.g. Oracle = recognized GAAP, Salesforce = closed-won pipeline)
#   - Use $X,XXX,XXX format for currency and X.X% for percentages""",
#     tools=[calculator_tool],
#     sub_agents=[oracle_agent, redshift_agent, mssql_agent, salesforce_agent],
# )

# agents/bi_agent.py
# from google.adk.agents import Agent
# from tools.calculator_tool import calculator_tool
# from agents.source_agents import (
#     oracle_agent,
#     redshift_agent,
#     mssql_agent,
#     salesforce_agent,
# )

# bi_agent = Agent(
#     name="bi_agent",
#     model="gemini-2.5-flash",
#     description=(
#         "Business Intelligence agent that fetches data from Kaplan source "
#         "systems and synthesizes multi-source financial analysis."
#     ),
#     tools=[calculator_tool],
#     sub_agents=[oracle_agent, redshift_agent, mssql_agent, salesforce_agent],
#     instruction="""You are Kaplan's FP&A Business Intelligence Agent.

# You ALWAYS receive explicit routing instructions from root_agent.
# The routing comes directly from the BigQuery semantic layer — it is authoritative.

# STEP 1 — READ ROUTING INSTRUCTIONS CAREFULLY
# Root agent tells you exactly:
#   "revenue → oracle_agent → fp_revenue.amount"
#   "drop rate → mssql_agent → fp_enrollment.drop_rate"
#   "pipeline → salesforce_agent → Opportunity.Amount (Stage open)"

# STEP 2 — FOLLOW ROUTING EXACTLY
# Use transfer_to_agent with the EXACT agent name from routing instructions:

#   transfer_to_agent(agent_name="oracle_agent")    ← revenue, new starts
#   transfer_to_agent(agent_name="salesforce_agent") ← closed won, pipeline
#   transfer_to_agent(agent_name="mssql_agent")     ← enrollment, drop rate
#   transfer_to_agent(agent_name="redshift_agent")  ← census, headcount

# CRITICAL RULES:
#   - NEVER guess which agent to call
#   - ALWAYS use the agent_to_call value from semantic layer
#   - For cross-source metrics (e.g. revenue per student):
#     call oracle_agent first, then redshift_agent
#   - Pass table name, field name and filters to the sub-agent

# STEP 3 — CALCULATE USING calculate TOOL
# Never compute numbers internally. Always use calculate:
#   - Totals      → operation='sum'
#   - YoY change  → operation='yoy_change'
#   - YoY %       → operation='yoy_pct'
#   - Ratio       → operation='ratio'
#   - Variance    → operation='variance' or 'variance_pct'

# STEP 4 — RETURN STRUCTURED RESULTS
#   - State which sources were queried
#   - $X,XXX,XXX for currency, X.X% for percentages
#   - Favorable / Unfavorable on variances
#   - Cross-source reconciliation notes if applicable""",
# )

# from google.adk.agents import Agent
# from tools.calculator_tool import calculator_tool
# from agents.source_agents import (
#     oracle_agent,
#     redshift_agent,
#     mssql_agent,
#     salesforce_agent,
# )

# bi_agent = Agent(
#     name="bi_agent",
#     model="gemini-2.5-flash",
#     description=(
#         "FP&A Business Intelligence orchestrator. Receives routing context "
#         "from semantic layer and fetches data from the correct source agent. "
#         "Handles multi-source queries and all calculations."
#     ),
#     tools=[calculator_tool],
#     sub_agents=[oracle_agent, redshift_agent, mssql_agent, salesforce_agent],
#     instruction="""You are Kaplan's FP&A Business Intelligence Agent.

# You receive a query WITH explicit routing context from root_agent.
# The routing is authoritative — it comes from the BigQuery semantic layer.

# ROUTING MAP (from semantic layer):
#   oracle_agent      → revenue (fp_revenue), new starts (fp_new_starts),
#                       channel mix shift
#   salesforce_agent  → closed won revenue, open pipeline, accounts, leads
#   mssql_agent       → enrollment (fp_enrollment), drop rate, program performance
#   redshift_agent    → census/headcount (fp_census)
#   cross-source      → revenue per student needs oracle_agent + redshift_agent

# STEP 1 — READ ROUTING CONTEXT
# Extract from root_agent message:
#   - Which agent(s) to call (agent_to_call from semantic layer)
#   - Period (e.g. Q3_2025, [Q1_2025, Q2_2025, Q3_2025] for YTD)
#   - Table and field to query
#   - Any filters to apply
#   - Calculation needed

# STEP 2 — FETCH DATA
# Use transfer_to_agent with the EXACT agent name from routing:
#   transfer_to_agent(agent_name="oracle_agent")
#   transfer_to_agent(agent_name="salesforce_agent")
#   transfer_to_agent(agent_name="mssql_agent")
#   transfer_to_agent(agent_name="redshift_agent")

# When passing the request to a sub-agent, include:
#   - Exact metric name
#   - Period in Kaplan format (Q3_2025)
#   - Any filters (business_unit, channel, segment, program)
#   - What fields to return

# For YTD or multi-period: call the agent once per period or pass all periods.
# For cross-source metrics: call each required agent separately.

# STEP 3 — CALCULATE
# Use the calculate tool for ALL arithmetic. Never compute internally.
#   sum          → total of values
#   variance     → actual minus reference [actual, reference]
#   variance_pct → variance as % [actual, reference]
#   ratio        → numerator / denominator [numerator, denominator]
#   yoy_change   → current minus prior [current, prior]
#   yoy_pct      → YoY % change [current, prior]

# STEP 4 — RETURN STRUCTURED RESULTS
# Format your response clearly:
#   - Which source(s) were queried
#   - Raw data by segment/period
#   - Calculated totals and variances
#   - Favorable/Unfavorable labels
#   - Any data gaps or limitations noted""",
# )

# bi agent
# from google.adk.agents import Agent
# from tools.calculator_tool import calculator_tool
# from agents.source_agents import (
#     oracle_agent,
#     mssql_agent,
#     salesforce_agent,
#     redshift_agent,
# )

# bi_agent = Agent(
#     name="bi_agent",
#     model="gemini-2.5-flash",
#     description=(
#         "FP&A data orchestrator. Receives semantic-layer routing context from "
#         "root_agent and fetches data from the exact source agent(s) specified. "
#         "Handles all calculations via calculator_tool."
#     ),
#     tools=[calculator_tool],
#     sub_agents=[oracle_agent, mssql_agent, salesforce_agent, redshift_agent],
#     instruction="""You are Kaplan's FP&A BI data orchestrator.

# You receive a ROUTING CONTEXT PACKET from root_agent. It tells you exactly:
#   • Which agent(s) to call
#   • Which table and field to query
#   • Which period(s) to fetch
#   • What calculation to perform

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1 — READ THE ROUTING CONTEXT (do not guess)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Extract from the routing context:
#   • agent_to_call (e.g. oracle_agent, mssql_agent, salesforce_agent)
#   • table and field
#   • period(s) in Q[N]_YYYY format
#   • filters (e.g. business_unit, channel, StageName)
#   • calculation needed

# ROUTING MAP (for reference — always prefer what root_agent says):
#   oracle_agent      → revenue (fp_revenue.amount), new starts (fp_new_starts.count)
#   mssql_agent       → enrollment (fp_enrollment.enrolled_count), drop rate (fp_enrollment.drop_rate)
#   salesforce_agent  → closed-won revenue, open pipeline (Opportunity)
#   redshift_agent    → census/headcount (fp_census.headcount)
#   CROSS-SOURCE:     → revenue per student needs oracle_agent + redshift_agent

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2 — FETCH DATA (follow routing exactly)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Use transfer_to_agent with the exact agent name:
#   transfer_to_agent(agent_name="oracle_agent")
#   transfer_to_agent(agent_name="mssql_agent")
#   transfer_to_agent(agent_name="salesforce_agent")
#   transfer_to_agent(agent_name="redshift_agent")

# When calling a sub-agent, pass:
#   • The metric name
#   • Period in Q[N]_YYYY format (e.g. Q3_2025)
#   • Any filters from the routing context
#   • What fields to return

# For YTD (multiple periods): pass each period separately or all at once.
# For cross-source metrics: call each required agent, collect both results.

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3 — CALCULATE (never compute inline)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Use calculator_tool for ALL arithmetic:
#   operation="sum"          → total of a list of values
#   operation="variance"     → actual − reference   [actual, reference]
#   operation="variance_pct" → variance as %        [actual, reference]
#   operation="ratio"        → numerator / denom    [numerator, denominator]
#   operation="yoy_change"   → current − prior year [current, prior]
#   operation="yoy_pct"      → YoY % change         [current, prior]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4 — RETURN STRUCTURED RESULTS to root_agent
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Format your response as a clear data packet:

#   SOURCES QUERIED: oracle_agent (fp_revenue), mssql_agent (fp_enrollment)
  
#   RAW DATA:
#     [Oracle] Q3_2025 revenue: $4,200,000 (Higher Ed: $2,800,000 | Supplemental: $1,400,000)
#     [MSSQL]  Q3_2025 drop rate: 8.5% avg across all programs
  
#   CALCULATIONS:
#     YoY revenue change: +$320,000 (+8.2%) — Favorable
#     Drop rate vs Q2_2025: +0.5pp — Unfavorable
  
#   DATA GAPS: [note any missing periods, filter mismatches, or errors]

# Keep it precise and complete. root_agent will format the final user-facing answer.""",
# )

# new bi agent
# agents/bi_agent.py
# agents/bi_agent.py
# from google.adk.agents import Agent
# from tools.calculator_tool import calculator_tool
# from agents.source_agents import (
#     oracle_agent,
#     mssql_agent,
#     salesforce_agent,
#     redshift_agent,
# )

# bi_agent = Agent(
#     name="bi_agent",
#     model="gemini-2.5-flash",
#     description=(
#         "FP&A data orchestrator. Executes routing instructions from the "
#         "semantic layer — fetches data from source agents and calculates."
#     ),
#     tools=[calculator_tool],
#     sub_agents=[oracle_agent, mssql_agent, salesforce_agent, redshift_agent],
#     instruction="""You are Kaplan's FP&A BI data orchestrator.

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORE PRINCIPLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# You receive a ROUTING CONTEXT PACKET from root_agent.
# Every routing decision in that packet came from the semantic layer.
# Follow it exactly. Never override or second-guess it.

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1 — READ THE ROUTING CONTEXT PACKET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Extract for each metric:
#   • agent_to_call — use this exactly
#   • category — Identity or Causal/Influential
#   • table and field
#   • period(s) in Q[N]_YYYY format
#   • filters
#   • formula_logic and calculation

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2 — FETCH DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Call transfer_to_agent using the exact agent_to_call from the packet:
#   transfer_to_agent(agent_name="oracle_agent")
#   transfer_to_agent(agent_name="mssql_agent")
#   transfer_to_agent(agent_name="salesforce_agent")
#   transfer_to_agent(agent_name="redshift_agent")

# Pass to each agent: metric name, period(s), filters, fields needed.
# For cross-source metrics: call each required agent separately.
# For YTD: fetch all quarters in the list.

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3 — HANDLE BY CATEGORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# IDENTITY → use calculator_tool, never compute inline:
#   sum, ratio, variance, variance_pct, yoy_change, yoy_pct

#   Favorable direction:
#     Revenue / starts / census → higher = Favorable
#     Drop rate → LOWER = Favorable

# CAUSAL/INFLUENTIAL → pattern analysis, no single number:
#   → Fetch data across periods and segments
#   → Describe direction and magnitude of the effect
#   → Isolate mix effect vs rate effect where relevant
#   → State which direction this driver is pushing the KPI
#   → Flag counter-intuitive patterns

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4 — RETURN STRUCTURED DATA PACKET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   SOURCES QUERIED: [list agents used]

#   IDENTITY METRICS:
#     [Metric]: [value] | [segment breakdown]
#     YoY: [change] ([%]) — Favorable / Unfavorable

#   CAUSAL ANALYSIS:
#     [Driver]: [directional description]
#     Evidence: [data points]
#     KPI Impact: [effect on the primary metric]

#   DATA GAPS: [missing data, errors, open questions from semantic layer]""",
# )

# agents/bi_agent.py
from google.adk.agents import Agent, SequentialAgent
from tools.calculator_tool import calculator_tool
from agents.source_agents import (
    oracle_agent,
    mssql_agent,
    salesforce_agent,
    redshift_agent,
)


bi_sequential = SequentialAgent(
    name="bi_sequential",
    description="Sequential data fetcher — runs source agents one at a time.",
    sub_agents=[oracle_agent, mssql_agent, salesforce_agent, redshift_agent],
)
bi_agent = Agent(
    name="bi_agent",
    model="gemini-2.5-flash",
    description=(
        "FP&A data orchestrator. Routes all queries through bi_parallel, "
        "then applies calculations via calculator_tool."
    ),
    tools=[calculator_tool],
    sub_agents=[bi_sequential],   # ← bi_sequential only, no source agents here
    instruction="""You are Kaplan's FP&A BI data orchestrator.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE PRINCIPLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━═════════════════════════════════════════════════════════════════════════════
You receive a ROUTING CONTEXT PACKET from root_agent.
Always route through bi_sequential — it handles both single and multi-source
queries. Source agents self-select based on agents_to_call in the packet.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — PARSE THE ROUTING CONTEXT PACKET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━═════════════════════════════════════════════════════════════════════════════
  • table, field, filters, period(s) in Q[N]_YYYY format
  • formula_logic, calculation

STEP 2 — FETCH DATA

Delegate to bi_sequential using:
  agent_name: "bi_sequential"
  Pass the FULL routing context packet as the message.
  bi_sequential will run source agents one at a time.
  Wait for ALL responses before proceeding to Step 3.

If bi_sequential returns an error or timeout:
  Return: DATA_FETCH_ERROR — [error message]
  Do not proceed to calculations.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3 — HANDLE RESULTS BY CATEGORY TYPE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━═════════════════════════════════════════════════════════════════════════════
Ignore any NOT_APPLICABLE responses.

IDENTITY metrics → use calculator_tool (never compute inline):
  Operations: sum, ratio, variance, variance_pct, yoy_change, yoy_pct
  Favorable: Revenue/starts/census higher = Favorable | Drop rate lower = Favorable

CAUSAL/INFLUENTIAL metrics → directional pattern analysis:
  Describe direction + magnitude. Isolate mix vs rate effect.
  State which way this driver pushes the primary KPI.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4 — RETURN STRUCTURED DATA PACKET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━═════════════════════════════════════════════════════════════════════════════
  SOURCES QUERIED: [agents that returned actual data, not NOT_APPLICABLE]

  IDENTITY METRICS:
    [Metric]: [value] | [segment breakdown if available]
    YoY: [± change] ([± %]) — Favorable / Unfavorable

  CAUSAL ANALYSIS:
    [Driver]: [directional description]
    Evidence: [data points]
    KPI Impact: [effect on primary metric]

  DATA GAPS: [errors, timeouts, missing data]""",
)
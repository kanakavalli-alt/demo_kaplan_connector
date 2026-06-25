# agents/source_agents/salesforce_agent.py mcp server version
# agents/source_agents/salesforce_agent.py
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

salesforce_agent = Agent(
    name="salesforce_agent",
    model="gemini-2.5-flash",
    description=(
        "Fetches live Salesforce CRM data — closed-won revenue, open pipeline, "
        "accounts and leads via direct Salesforce API through MCP server. "
        "Understands natural language queries and maps them to Salesforce tools."
    ),
    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="python",
                    args=["mcp_servers/salesforce_server.py"]
                )
            )
        )
    ],
    instruction="""You are Kaplan's Salesforce CRM data agent.

SELF-SELECTION RULE — check FIRST:
  If "salesforce_agent" is NOT in agents_to_call:
    → Respond: SALESFORCE_AGENT: NOT_APPLICABLE
    → Stop.
  If "salesforce_agent" IS in agents_to_call:
    → Proceed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR JOB — NLP → TOOL CALL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You receive natural language requests. Your job is to:
  1. Understand the intent
  2. Map it to the correct tool and parameters
  3. Call the tool
  4. Return raw results

NEVER say you cannot handle a query.
NEVER ask the user to rephrase into tool syntax.
ALWAYS interpret the intent and call the best matching tool.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTENT → TOOL MAPPING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OPPORTUNITIES (revenue / pipeline):
  Use query_salesforce_opportunities()

  Natural language → parameters:

  "closed won" / "won deals" / "closed pipeline"
  / "booked revenue" / "actual CRM revenue"
    → stage="Closed Won"

  "open pipeline" / "active deals" / "in progress"
  / "not yet closed" / "forecast"
    → stage="open"

  "lost deals" / "closed lost"
    → stage="Closed Lost"

  "all opportunities" / "every deal" / "total pipeline"
    → stage=None (no filter)

  Period extraction:
    "Q3 2025" / "Q3_2025" / "third quarter 2025"
      → period_year=2025, period_quarter=3
    "last quarter" / "Q1 2026"
      → period_year=2026, period_quarter=1
    "this year" / "2025"
      → period_year=2025, period_quarter=None
    "last month" / no period mentioned
      → period_year=None, period_quarter=None

  Business type extraction:
    "new customers" / "new business"
      → business_type="New Customer"
    "existing customers" / "upsell" / "expansion"
      → business_type="Existing Customer - Upgrade"
    not mentioned
      → business_type=None

  EXAMPLES — NLP to tool call:
    "Show me all closed won deals for Q3 2025"
      → query_salesforce_opportunities(stage="Closed Won", period_year=2025, period_quarter=3)

    "What is our current open pipeline?"
      → query_salesforce_opportunities(stage="open")

    "How much revenue did we book last quarter?"
      → query_salesforce_opportunities(stage="Closed Won", period_year=2026, period_quarter=1)

    "Give me all Salesforce opportunities"
      → query_salesforce_opportunities()

    "What deals closed in 2025?"
      → query_salesforce_opportunities(stage="Closed Won", period_year=2025)

    "Show me new customer wins this year"
      → query_salesforce_opportunities(stage="Closed Won", period_year=2025, business_type="New Customer")

    "What is our pipeline for Q4 2025?"
      → query_salesforce_opportunities(stage="open", period_year=2025, period_quarter=4)

ACCOUNTS (customers / institutions):
  Use query_salesforce_accounts()

  Natural language → parameters:
    "education accounts" / "education customers"
      → industry="Education"
    "all accounts" / "all customers" / "all institutions"
      → industry=None
    "technology accounts"
      → industry="Technology"

  EXAMPLES:
    "Show me all Kaplan customer accounts"
      → query_salesforce_accounts()
    "Which education institutions are we working with?"
      → query_salesforce_accounts(industry="Education")

LEADS (prospects / inquiries):
  Use query_salesforce_leads()

  Natural language → parameters:
    "open leads" / "new leads" / "active prospects"
      → status="Open"
    "converted leads" / "leads that became customers"
      → status="Converted"
    "all leads" / "total leads" / "lead volume"
      → status=None

  EXAMPLES:
    "How many leads do we have?"
      → query_salesforce_leads()
    "Show me all open leads"
      → query_salesforce_leads(status="Open")
    "Which leads were converted?"
      → query_salesforce_leads(status="Converted")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AMBIGUOUS QUERIES — always attempt, never refuse
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If the intent is unclear, make a reasonable assumption
and fetch the most relevant data:

  "Salesforce revenue" → query_salesforce_opportunities(stage="Closed Won")
  "CRM data" → query_salesforce_opportunities()
  "deals" → query_salesforce_opportunities()
  "customers" → query_salesforce_accounts()
  "prospects" → query_salesforce_leads()
  "pipeline vs actual" → call BOTH:
      query_salesforce_opportunities(stage="open")
      query_salesforce_opportunities(stage="Closed Won")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Always return:
  - Which tool was called and with what parameters
  - All records returned
  - total_amount (pre-calculated — use as-is)
  - Record count
  - Source citation

Never calculate beyond what the tool returns.
Never refuse a natural language query.
Cite: Source: Salesforce CRM (Live via MCP)""",
)


#IC for salesforce_agent.py
# from google.adk.agents import Agent
# from google.adk.tools.application_integration_tool.application_integration_toolset import (
#     ApplicationIntegrationToolset,
# )

# salesforce_agent = Agent(
#     name="salesforce_agent",
#     model="gemini-2.5-flash",
#     description=(
#         "Fetches live Salesforce CRM data — closed-won revenue and open pipeline "
#         "from Opportunities, plus Accounts and Leads. "
#         "Connects via GCP Application Integration Connector (OAuth)."
#     ),
#     tools=[
#         ApplicationIntegrationToolset(
#             project="robust-atrium-406105",
#             location="us-central1",
#             connection="salesforce",
#             entity_operations={
#                 "Opportunity": ["LIST", "GET"],
#                 "Account":     ["LIST", "GET"],
#                 "Lead":        ["LIST", "GET"],
#                 "Contact":     ["LIST", "GET"],
#             },
#             actions=[],
#             tool_name_prefix="salesforce",
#             tool_instructions="""Query live Salesforce CRM.
# Key Opportunity fields: Id, Name, Amount, StageName, CloseDate, AccountId, Type, Probability.
# Key Account fields: Id, Name, Industry, AnnualRevenue, Type.
# Key Lead fields: Id, Name, Status, LeadSource, Company.""",
#         )
#     ],
#     instruction="""You are Kaplan's Salesforce CRM data agent. Fetch data only — no calculations.

# CONNECTION: GCP Application Integration Connector (OAuth — do not modify).

# KEY QUERY PATTERNS:
#   Closed-Won revenue (use for GAAP-pipeline reconciliation):
#     LIST Opportunity WHERE StageName = 'Closed Won'
#     Fields to return: Name, Amount, CloseDate, AccountId, Type

#   Open Pipeline (forward-looking revenue indicator):
#     LIST Opportunity WHERE StageName NOT IN ('Closed Won', 'Closed Lost')
#     Fields: Name, Amount, StageName, CloseDate, Probability

#   Quarter date ranges for CloseDate filtering:
#     Q1 = 2025-01-01 to 2025-03-31
#     Q2 = 2025-04-01 to 2025-06-30
#     Q3 = 2025-07-01 to 2025-09-30
#     Q4 = 2025-10-01 to 2025-12-31
#     (Adjust year to match requested period)

#   Accounts: LIST Account
#   Leads:    LIST Lead

# RULES:
#   • Return complete records with all available fields.
#   • Always include Amount and StageName for revenue queries.
#   • Never calculate — raw data only.
#   • Cite: Salesforce CRM (Live — GCP Integration Connector)""",
# )

# new one trial

# agents/source_agents/salesforce_agent.py
# ─────────────────────────────────────────────────────────────────────────────
# SALESFORCE AGENT — Discovery Engine (confirmed working path)

# ENGINE:        gemini-enterprise-17804909_1780490979854
# SERVING CONFIG: default_search
# FULL PATH:     projects/321544097371/locations/global/collections/
#                default_collection/engines/gemini-enterprise-17804909_1780490979854/
#                servingConfigs/default_search

# KEY INSIGHT — FEDERATED connector:
#   The Salesforce connector type is THIRD_PARTY_FEDERATED — data stays in
#   Salesforce and is queried live. Documents are NOT copied into GCP.
#   The engine searches across ALL attached datastores (Salesforce entities
#   + BigQuery data dictionary). We filter by datastore_id to get only
#   Salesforce records, not BQ data dictionary matches.

# DATASTORE IDs per Salesforce entity:
#   opportunity  → kaplan-salesforce-connector_1780494585965_opportunity
#   account      → kaplan-salesforce-connector_1780494585965_account
#   lead         → kaplan-salesforce-connector_1780494585965_lead
#   contact      → kaplan-salesforce-connector_1780494585965_contact
#   case         → kaplan-salesforce-connector_1780494585965_case
#   task         → kaplan-salesforce-connector_1780494585965_task
# ─────────────────────────────────────────────────────────────────────────────

# import os
# import json
# from google.adk.agents import Agent
# from google.cloud import discoveryengine_v1 as discoveryengine
# from mcp_servers.salesforce_server import (
#     query_salesforce_opportunities,
#     query_salesforce_accounts,
#     query_salesforce_leads,
#     get_connection
# )

# # ── Confirmed resource identifiers (from curl output) ────────────────────────
# PROJECT_NUMBER  = "321544097371"
# LOCATION        = "global"
# COLLECTION      = "default_collection"
# ENGINE_ID       = "gemini-enterprise-17804909_1780490979854"
# SERVING_CONFIG  = "default_search"

# SERVING_CONFIG_PATH = (
#     f"projects/{PROJECT_NUMBER}/locations/{LOCATION}"
#     f"/collections/{COLLECTION}/engines/{ENGINE_ID}"
#     f"/servingConfigs/{SERVING_CONFIG}"
# )

# # Salesforce entity datastore IDs — used to filter out BQ data dictionary hits
# SF_DATASTORE_PREFIX = "kaplan-salesforce-connector_1780494585965"
# SF_DATASTORES = {
#     "opportunity":   f"{SF_DATASTORE_PREFIX}_opportunity",
#     "account":       f"{SF_DATASTORE_PREFIX}_account",
#     "lead":          f"{SF_DATASTORE_PREFIX}_lead",
#     "contact":       f"{SF_DATASTORE_PREFIX}_contact",
#     "case":          f"{SF_DATASTORE_PREFIX}_case",
#     "task":          f"{SF_DATASTORE_PREFIX}_task",
# }

# # ── Module-level client — created once per process ────────────────────────────
# _CLIENT: discoveryengine.SearchServiceClient | None = None

# def _get_client() -> discoveryengine.SearchServiceClient:
#     global _CLIENT
#     if _CLIENT is None:
#         _CLIENT = discoveryengine.SearchServiceClient()
#     return _CLIENT


# def _is_salesforce_record(document) -> bool:
#     """
#     Returns True if the document came from a Salesforce datastore,
#     not from the BigQuery data dictionary.
#     The document name contains the datastore ID — check for the SF prefix.
#     """
#     doc_name = getattr(document, "name", "") or ""
#     return SF_DATASTORE_PREFIX in doc_name


# def _extract_record(result) -> dict | None:
#     """
#     Extract a usable dict from a Discovery Engine search result.
#     Returns None if the record is from the BQ data dictionary (not Salesforce).
#     """
#     doc = result.document

#     # Filter — only return Salesforce records, skip BQ data dictionary hits
#     if not _is_salesforce_record(doc):
#         return None

#     record = {}

#     # Convert protobuf Struct to plain dict
#     try:
#         doc_dict = type(doc).to_dict(doc)
#         struct_data = doc_dict.get("structData", {})
#         derived_data = doc_dict.get("derivedStructData", {})
#         if struct_data:
#             record.update(struct_data)
#         # derived_data has entity_type, snippets etc — add selectively
#         if derived_data.get("entity_type"):
#             record["_entity_type"] = derived_data["entity_type"]
#     except Exception:
#         pass

#     if doc.id:
#         record["_id"] = doc.id

#     return record if record else None


# def search_salesforce(query: str, entity: str = "all", page_size: int = 10) -> str:
#     """
#     Search Kaplan's live Salesforce CRM data via Discovery Engine.

#     Queries the Gemini Enterprise engine which federates live Salesforce data.
#     Data is NOT copied to GCP — it is queried live from Salesforce.

#     Args:
#         query:     Natural language search string.
#                    Examples:
#                      "closed won opportunities"
#                      "open pipeline deals"
#                      "all accounts"
#                      "leads not yet contacted"
#                      "opportunities above 50000"
#         entity:    Salesforce object to filter by. One of:
#                      "opportunity", "account", "lead",
#                      "contact", "case", "task", "all"
#                    Default "all" searches across every entity.
#         page_size: Results to return (default 10, max 100).

#     Returns:
#         JSON string with matching Salesforce records.
#     """
#     try:
#         client = _get_client()

#         # Build the search request
#         request = discoveryengine.SearchRequest(
#             serving_config=SERVING_CONFIG_PATH,
#             query=query,
#             page_size=page_size,
#         )

#         # If a specific entity is requested, add a datastore filter
#         # This uses the dataStoreSpecs to restrict results to one entity
#         if entity != "all" and entity in SF_DATASTORES:
#             datastore_id = SF_DATASTORES[entity]
#             request.data_store_specs = [
#                 discoveryengine.SearchRequest.DataStoreSpec(
#                     data_store=f"projects/{PROJECT_NUMBER}/locations/{LOCATION}"
#                                f"/collections/{COLLECTION}/dataStores/{datastore_id}"
#                 )
#             ]

#         response = client.search(request)

#         records = []
#         skipped_bq = 0
#         for result in response.results:
#             record = _extract_record(result)
#             if record:
#                 records.append(record)
#             else:
#                 skipped_bq += 1

#         if not records:
#             return json.dumps({
#                 "status":  "empty",
#                 "query":   query,
#                 "entity":  entity,
#                 "message": (
#                     f"No Salesforce records matched '{query}' for entity '{entity}'. "
#                     f"Skipped {skipped_bq} non-Salesforce results. "
#                     "Try a broader query or entity='all'."
#                 ),
#                 "records": []
#             }, indent=2)

#         return json.dumps({
#             "status":        "success",
#             "query":         query,
#             "entity_filter": entity,
#             "count":         len(records),
#             "skipped_bq":    skipped_bq,
#             "source":        f"Salesforce (federated) via {ENGINE_ID}",
#             "records":       records
#         }, indent=2)

#     except Exception as e:
#         return json.dumps({
#             "status":  "error",
#             "query":   query,
#             "error":   str(e),
#             "records": []
#         }, indent=2)


# # ── ADK Agent ─────────────────────────────────────────────────────────────────
# salesforce_agent = Agent(
#     name="salesforce_agent",
#     model="gemini-2.5-flash",
#     description=(
#         "Queries live Salesforce CRM data using direct API database queries "
#         "and the Gemini Enterprise Discovery Engine. Returns Opportunities, Accounts, and Leads."
#     ),
#     # 🌟 Added your live API Python functions directly to the agent's toolkit
#     tools=[
#         search_salesforce, 
#         query_salesforce_opportunities, 
#         query_salesforce_accounts, 
#         query_salesforce_leads
#     ],
#     instruction="""You are Kaplan's Salesforce CRM data agent.
#     SELF-SELECTION RULE (check this FIRST, every time)
# If "salesforce_agent" does NOT appear in agents_to_call in the routing context:
#   Respond with exactly:  SALESFORCE_AGENT: NOT_APPLICABLE
#   Then stop. Do not query any data.

# You have two ways to look up data. Always choose the best path:
# 1. For structured data lookups, counting records, totaling amounts, or if search returns empty results: 
#    USE the direct database tools: query_salesforce_opportunities(), query_salesforce_accounts(), or query_salesforce_leads().
# 2. For broad, natural language conceptual searches across everything: Use search_salesforce().

# CRITICAL RULE: If search_salesforce() returns a status of "empty", immediately fall back to using your direct query tools (like query_salesforce_opportunities) to fetch the live database records.

# RULES:
#   • Return raw records exactly — do not calculate or summarise.
#   • Cite source accurately: State whether data came from Live API Query or Federated Search Index.""",
# )
from google.adk.agents import Agent
from google.adk.tools import VertexAiSearchTool

DATASTORE_ID = (
    "projects/321544097371/locations/global/collections/"
    "default_collection/dataStores/big-query_1780656766583_data_dictionary"
)

semantic_agent = Agent(
    name="semantic_agent",
    model="gemini-2.5-flash",
    description=(
        "Looks up Kaplan FP&A business terms from the Vertex AI Search "
        "semantic layer backed by BigQuery. Returns exact routing context "
        "including which agent to call, table, field and filters."
    ),
    tools=[VertexAiSearchTool(data_store_id=DATASTORE_ID)],
    instruction="""You are Kaplan's semantic layer lookup agent.

You have access to Kaplan's FP&A data dictionary via Vertex AI Search.
When given a business term, search for it and return ALL of these fields:

  - definition: Kaplan's exact business definition
  - source_system: oracle / salesforce / mssql / redshift / cross_source
  - agent_name: exact agent to call (oracle_agent, salesforce_agent, etc)
  - table_name: exact database table
  - field_name: exact field to query
  - filters: any required SQL filters (e.g. StageName = 'Closed Won')
  - calculation: how to compute the metric
  - related_terms: other terms that may be relevant
  - aliases: other names for this term

Search for the exact term first. If not found, search for related terms.
Always return the agent_name — this is critical for routing.

Examples:
  "revenue"        → oracle_agent, fp_revenue, amount
  "new starts"     → oracle_agent, fp_new_starts, count
  "drop rate"      → mssql_agent, fp_enrollment, drop_rate
  "pipeline"       → salesforce_agent, Opportunity, Amount
  "census"         → redshift_agent, fp_census, headcount""",
)
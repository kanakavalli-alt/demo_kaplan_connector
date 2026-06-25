
# tools/rag_tool.py
# import os
# import requests
# from google.auth import default
# from google.auth.transport.requests import Request
# from google.adk.tools import FunctionTool


# def lookup_fp_and_a_term(term: str) -> dict:
#     """
#     Look up Kaplan FP&A business term from the semantic layer.
#     Tries Vertex AI Search first, falls back to BigQuery direct query.
#     Returns agent routing context: agent_to_call, table, field, filters.

#     Args:
#         term: Business term e.g. 'revenue', 'new starts', 'drop rate',
#               'pipeline', 'census', 'enrollment', 'yoy', 'favorability'

#     Returns:
#         Dictionary with routing context including which agent to call.
#     """
#     # ── Try Vertex AI Search first ─────────────────────────────────────────
#     try:
#         credentials, _ = default(
#             scopes=["https://www.googleapis.com/auth/cloud-platform"]
#         )
#         credentials.refresh(Request())
#         token = credentials.token

#         data_store_id = os.getenv(
#             "VERTEX_SEARCH_DATASTORE_ID",
#             "big-query_1780656766583_data_dictionary"
#         )

#         url = (
#             f"https://discoveryengine.googleapis.com/v1alpha"
#             f"/projects/321544097371/locations/global"
#             f"/collections/default_collection"
#             f"/dataStores/{data_store_id}"
#             f"/servingConfigs/default_config:search"
#         )

#         response = requests.post(
#             url,
#             headers={
#                 "Authorization": f"Bearer {token}",
#                 "Content-Type": "application/json",
#                 "x-goog-user-project": "spheric-gasket-478706-h0",
#             },
#             json={
#                 "query": term,
#                 "pageSize": 3,
#                 "queryExpansionSpec": {"condition": "AUTO"},
#             },
#             timeout=10,
#         )

#         if response.status_code == 200:
#             results = [
#                 r.get("document", {}).get("structData", {})
#                 for r in response.json().get("results", [])
#             ]
#             results = [r for r in results if r]

#             if results:
#                 p = results[0]
#                 return {
#                     "term":          term,
#                     "found":         True,
#                     "source":        "vertex_ai_search",
#                     "definition":    p.get("definition"),
#                     "source_system": p.get("source_system"),
#                     "agent_to_call": p.get("agent_name"),
#                     "table":         p.get("table_name"),
#                     "field":         p.get("field_name"),
#                     "filters":       p.get("filters"),
#                     "calculation":   p.get("calculation"),
#                     "related_terms": p.get("related_terms"),
#                     "category":      p.get("category"),
#                 }

#     except Exception:
#         pass  # Fall through to BigQuery

#     # ── BigQuery direct fallback ────────────────────────────────────────────
#     try:
#         from google.cloud import bigquery

#         client = bigquery.Client(project="spheric-gasket-478706-h0")

#         query = """
#             SELECT
#                 term, aliases, definition, source_system,
#                 agent_name, table_name, field_name,
#                 filters, related_terms, category, calculation
#             FROM `spheric-gasket-478706-h0.kaplan_semantic_layer.kaplan_metrics`
#             WHERE
#                 LOWER(term) = LOWER(@term)
#                 OR LOWER(IFNULL(aliases, '')) LIKE LOWER(CONCAT('%', @term, '%'))
#                 OR LOWER(@term) LIKE LOWER(CONCAT('%', term, '%'))
#             ORDER BY
#                 CASE WHEN LOWER(term) = LOWER(@term) THEN 0 ELSE 1 END
#             LIMIT 3
#         """

#         rows = list(client.query(
#             query,
#             job_config=bigquery.QueryJobConfig(
#                 query_parameters=[
#                     bigquery.ScalarQueryParameter("term", "STRING", term)
#                 ]
#             )
#         ).result())

#         if rows:
#             p = dict(rows[0])
#             return {
#                 "term":          term,
#                 "found":         True,
#                 "source":        "bigquery_fallback",
#                 "definition":    p.get("definition"),
#                 "source_system": p.get("source_system"),
#                 "agent_to_call": p.get("agent_name"),
#                 "table":         p.get("table_name"),
#                 "field":         p.get("field_name"),
#                 "filters":       p.get("filters"),
#                 "calculation":   p.get("calculation"),
#                 "related_terms": p.get("related_terms"),
#                 "category":      p.get("category"),
#             }

#     except Exception as e:
#         return {
#             "term":          term,
#             "found":         False,
#             "error":         str(e),
#             "agent_to_call": None,
#             "source_system": None,
#         }

#     return {
#         "term":          term,
#         "found":         False,
#         "definition":    "Term not found in semantic layer.",
#         "agent_to_call": None,
#         "source_system": None,
#     }


# rag_tool = FunctionTool(func=lookup_fp_and_a_term)


# tools/rag_tool.py
# import os
# import requests
# from google.auth import default
# from google.auth.transport.requests import Request
# from google.adk.tools import FunctionTool


# INTENT_MAP = {
#     # Revenue variations
#     "actual revenue":           "revenue",
#     "oracle revenue":           "revenue",
#     "actual oracle revenue":    "revenue",
#     "gaap revenue":             "revenue",
#     "total revenue":            "revenue",
#     "booked revenue":           "revenue",
#     "recognized revenue":       "revenue",

#     # Closed won variations
#     "closed won pipeline":      "closed won revenue",
#     "won deals":                "closed won revenue",
#     "closed pipeline":          "closed won revenue",
#     "won opportunities":        "closed won revenue",
#     "closed opportunities":     "closed won revenue",

#     # Pipeline variations
#     "open pipeline":            "pipeline",
#     "active pipeline":          "pipeline",
#     "deal pipeline":            "pipeline",
#     "sales pipeline":           "pipeline",
#     "open opportunities":       "pipeline",
#     "forecast":                 "pipeline",

#     # Census variations
#     "headcount":                "census",
#     "student count":            "census",
#     "student population":       "census",
#     "active students":          "census",
#     "enrolled students":        "census",
#     "student headcount":        "census",

#     # Drop rate variations
#     "dropout rate":             "drop rate",
#     "attrition":                "drop rate",
#     "students dropping":        "drop rate",
#     "dropping out":             "drop rate",
#     "withdrawal rate":          "drop rate",
#     "student attrition":        "drop rate",
#     "retention":                "drop rate",  # inverse

#     # New starts variations
#     "new enrollments":          "new starts",
#     "student starts":           "new starts",
#     "fresh enrollments":        "new starts",
#     "new student count":        "new starts",
#     "enrollment starts":        "new starts",

#     # RPS variations
#     "rps":                      "revenue per student",
#     "revenue per head":         "revenue per student",
#     "average revenue per student": "revenue per student",
#     "revenue per learner":      "revenue per student",
#     "revenue per capita":       "revenue per student",

#     # Lead variations
#     "prospects":                "lead volume",
#     "inquiries":                "lead volume",
#     "lead flow":                "lead volume",
#     "new leads":                "lead volume",

#     # Credit hour variations
#     "course load":              "average credit hours per student",
#     "credit load":              "average credit hours per student",
#     "credits per student":      "average credit hours per student",

#     # Tuition variations
#     "tuition rate":             "realized tuition per credit hour",
#     "net tuition":              "realized tuition per credit hour",
#     "tuition per credit":       "realized tuition per credit hour",

#     # LTV variations
#     "ltv":                      "lifetime value",
#     "student ltv":              "lifetime value",
#     "long term value":          "lifetime value",

#     # Channel variations
#     "channel shift":            "channel mix shift",
#     "lead source mix":          "channel mix shift",
#     "seo vs aggregator":        "channel mix shift",

#     # Military variations
#     "military students":        "military student mix",
#     "veteran students":         "military student mix",
#     "military share":           "military student mix",

#     # Conversion variations
#     "conversion rate":          "within-channel conversion",
#     "enrollment conversion":    "within-channel conversion",
#     "inquiry to start":         "within-channel conversion",
#     "lead conversion":          "within-channel conversion",
# }


# def _normalize_term(term: str) -> str:
#     """Map natural language variations to canonical semantic layer terms."""
#     normalized = term.strip().lower()
    
#     # Direct map check
#     if normalized in INTENT_MAP:
#         return INTENT_MAP[normalized]
    
#     # Partial match — check if any key is contained in the term
#     for key, canonical in INTENT_MAP.items():
#         if key in normalized:
#             return canonical
    
#     return term  # Return original if no mapping found


# def lookup_fp_and_a_term(term: str) -> dict:
#     """
#     Look up Kaplan FP&A business term from the semantic layer.
#     Queries kaplan_metrics table which contains client-provided metric
#     definitions including Identity vs Causal/Influential categorization.

#     Args:
#         term: Business term e.g. 'new starts', 'drop rate', 'census',
#               'revenue per student', 'channel mix shift', 'lead volume',
#               'within-channel conversion', 'track-timing correction',
#               'graduation count', 'lifetime value', 'military student mix'

#     Returns:
#         Dictionary with routing context, category, formula logic and
#         which agent to call.
#     """

    
#     # Try Vertex AI Search first

#     normalized_term = _normalize_term(term)
#     try:
#         credentials, _ = default(
#             scopes=["https://www.googleapis.com/auth/cloud-platform"]
#         )
#         credentials.refresh(Request())
#         token = credentials.token

#         data_store_id = os.getenv(
#             "VERTEX_SEARCH_DATASTORE_ID",
#             "big-query_1780656766583_data_dictionary"
#         )

#         url = (
#             f"https://discoveryengine.googleapis.com/v1alpha"
#             f"/projects/321544097371/locations/global"
#             f"/collections/default_collection"
#             f"/dataStores/{data_store_id}"
#             f"/servingConfigs/default_config:search"
#         )

#         response = requests.post(
#             url,
#             headers={
#                 "Authorization": f"Bearer {token}",
#                 "Content-Type": "application/json",
#                 "x-goog-user-project": "robust-atrium-406105",
#             },
#             json={
#                 "query": term,
#                 "pageSize": 3,
#                 "queryExpansionSpec": {"condition": "AUTO"},
#             },
#             timeout=10,
#         )

#         if response.status_code == 200:
#             results = [
#                 r.get("document", {}).get("structData", {})
#                 for r in response.json().get("results", [])
#             ]
#             results = [r for r in results if r]
#             if results:
#                 p = results[0]
#                 return _build_result(term, p, "vertex_ai_search")

#     except Exception:
#         pass

#     # BigQuery direct fallback
#     try:
#         from google.cloud import bigquery
#         client = bigquery.Client(project="robust-atrium-406105")

#         query = """
#             SELECT
#                 term, aliases, definition, category,
#                 source_system, agent_name, table_name, field_name,
#                 filters, related_terms, calculation,
#                 use_cases, formula_logic, open_questions
#             FROM `robust-atrium-406105.kaplan_semantic_layer.kaplan_metrics`
#             WHERE
#                 LOWER(term) = LOWER(@term)
#                 OR LOWER(IFNULL(aliases, '')) LIKE LOWER(CONCAT('%', @term, '%'))
#                 OR LOWER(@term) LIKE LOWER(CONCAT('%', term, '%'))
#             ORDER BY
#                 CASE WHEN LOWER(term) = LOWER(@term) THEN 0 ELSE 1 END
#             LIMIT 3
#         """

#         rows = list(client.query(
#             query,
#             job_config=bigquery.QueryJobConfig(
#                 query_parameters=[
#                     bigquery.ScalarQueryParameter("term", "STRING", term)
#                 ]
#             )
#         ).result())

#         if rows:
#             return _build_result(term, dict(rows[0]), "bigquery_kaplan_metrics")

#     except Exception as e:
#         return {
#             "term":          term,
#             "found":         False,
#             "error":         str(e),
#             "agent_to_call": None,
#             "source_system": None,
#         }

#     return {
#         "term":          term,
#         "found":         False,
#         "definition":    "Term not found in Kaplan semantic layer.",
#         "agent_to_call": None,
#         "source_system": None,
#     }


# def _build_result(term: str, p: dict, source: str) -> dict:
#     return {
#         "term":           term,
#         "found":          True,
#         "source":         source,
#         "definition":     p.get("definition"),
#         "category":       p.get("category"),
#         "source_system":  p.get("source_system"),
#         "agent_to_call":  p.get("agent_name"),
#         "table":          p.get("table_name"),
#         "field":          p.get("field_name"),
#         "filters":        p.get("filters"),
#         "calculation":    p.get("calculation"),
#         "formula_logic":  p.get("formula_logic"),
#         "related_terms":  p.get("related_terms"),
#         "use_cases":      p.get("use_cases"),
#         "open_questions": p.get("open_questions"),
#     }


# rag_tool = FunctionTool(func=lookup_fp_and_a_term)

# tools/rag_tool.py--working 
# """
# Semantic layer lookup for the Kaplan FP&A Analytics Agent.
# """

# import os
# from google.adk.tools import FunctionTool


# # ── Fast-path cache ───────────────────────────────────────────────────────────
# # Keep this SHORT — it is only for the highest-frequency aliases that save a
# # BigQuery round-trip.  All other normalisation is handled by the BQ
# # aliases column (which you updated via bq UPDATE).
# FAST_PATH_MAP: dict[str, str] = {
#     "actual revenue":             "revenue",
#     "oracle revenue":             "revenue",
#     "headcount":                  "census",
#     "rps":                        "revenue per student",
#     "dropout rate":               "drop rate",
#     "course load":                "average credit hours per student",
#     "tuition rate":               "realized tuition per credit hour",
#     "ltv":                        "lifetime value",
#     "closed won pipeline":        "closed won revenue",
#     "open pipeline":              "pipeline",
#     # New:
#     "closed won opportunities":   "closed won revenue",
#     "won deals":                  "closed won revenue",
#     "won opportunities":          "closed won revenue",
#     "pipeline value":             "pipeline",
#     "open opportunities":         "pipeline",
#     "total pipeline":             "pipeline",
#     "crm leads":                  "lead volume",
#     "salesforce leads":           "lead volume",
#     "number of leads":            "lead volume",
# }

# # ── Category mapping ──────────────────────────────────────────────────────────
# # BQ stores "metric" / "calculation" / "dimension".
# # Agent instructions use "Identity" / "Causal/Influential".
# # Dimensions (channel mix shift, military mix, etc.) are causal drivers;
# # KPI metrics and calculation helpers are Identity.
# _CATEGORY_TYPE_MAP: dict[str, str] = {
#     "metric":      "Identity",
#     "calculation": "Identity",
#     "dimension":   "Causal/Influential",
# }


# def _normalize_term(term: str) -> str:
#     """Fast-path alias resolution before hitting BigQuery."""
#     key = term.strip().lower()
#     if key in FAST_PATH_MAP:
#         return FAST_PATH_MAP[key]
#     # Partial-match fallback (keeps the map useful for compound phrases)
#     for alias, canonical in FAST_PATH_MAP.items():
#         if alias in key:
#             return canonical
#     return term


# def _parse_agents(raw: str | None) -> list[str]:
#     """
#     Convert BQ agent_name string → Python list.
#     "oracle_agent,redshift_agent" → ["oracle_agent", "redshift_agent"]
#     """
#     if not raw:
#         return []
#     return [a.strip() for a in raw.split(",") if a.strip()]


# def _build_result(term: str, row: dict, source: str) -> dict:
#     """Build the normalised result dict from a BQ/cache row."""
#     raw_category = (row.get("category") or "").lower()
#     agents = _parse_agents(row.get("agent_name"))
#     return {
#         "term":           term,
#         "found":          True,
#         "source":         source,
#         # ── Routing ───────────────────────────────────────────────────────────
#         "agents_to_call": agents,                        # list — always use this
#         "agent_to_call":  agents[0] if len(agents) == 1 else None,  # single-agent convenience
#         "is_multi_source": len(agents) > 1,
#         # ── Classification ────────────────────────────────────────────────────
#         "category":       row.get("category"),           # raw BQ value
#         "category_type":  _CATEGORY_TYPE_MAP.get(raw_category, "Identity"),
#         # ── Data location ─────────────────────────────────────────────────────
#         "source_system":  row.get("source_system"),
#         "table":          row.get("table_name"),
#         "field":          row.get("field_name"),
#         "filters":        row.get("filters"),
#         # ── Computation ───────────────────────────────────────────────────────
#         "calculation":    row.get("calculation"),
#         "formula_logic":  row.get("formula_logic"),
#         # ── Enrichment ────────────────────────────────────────────────────────
#         "definition":     row.get("definition"),
#         "related_terms":  row.get("related_terms"),
#         "use_cases":      row.get("use_cases"),
#         "open_questions": row.get("open_questions"),
#     }


# def lookup_fp_and_a_term(term: str) -> dict:
#     """
#     Look up a Kaplan FP&A business term from the semantic layer
#     (kaplan_semantic_layer.kaplan_metrics in BigQuery).

#     The result tells bi_agent:
#       • agents_to_call  → list of agents needed (split for you already)
#       • is_multi_source → True if 2+ agents required → use bi_parallel
#       • category_type   → "Identity" (KPI) or "Causal/Influential" (driver)
#       • table / field / filters → exact query targets
#       • calculation / formula_logic → how to compute the metric

#     Args:
#         term: Business term e.g. "revenue", "new starts", "drop rate",
#               "channel mix shift", "revenue per student".
#               Natural-language variants like "headcount", "course load",
#               "dropout rate" are automatically resolved via alias matching.

#     Returns:
#         Dictionary with full routing context.
#     """
#     normalized = _normalize_term(term)

#     try:
#         from google.cloud import bigquery

#         # Use the project that owns the semantic layer dataset
#         client = bigquery.Client(project="robust-atrium-406105")

#         query = """
#             SELECT
#                 term,
#                 aliases,
#                 definition,
#                 category,
#                 source_system,
#                 agent_name,
#                 table_name,
#                 field_name,
#                 filters,
#                 related_terms,
#                 calculation,
#                 use_cases,
#                 formula_logic,
#                 open_questions
#             FROM `robust-atrium-406105.kaplan_semantic_layer.kaplan_metrics_new`
#             WHERE
#                 -- Exact match on canonical term (highest priority)
#                 LOWER(term) = LOWER(@term)
#                 -- Normalized term also checked (fast-path resolved)
#                 OR LOWER(term) = LOWER(@normalized)
#                 -- BQ alias column contains the searched term
#                 OR LOWER(IFNULL(aliases, '')) LIKE LOWER(CONCAT('%', @term, '%'))
#                 OR LOWER(IFNULL(aliases, '')) LIKE LOWER(CONCAT('%', @normalized, '%'))
#                 -- Searched term contains the canonical term (substring)
#                 OR LOWER(@term) LIKE LOWER(CONCAT('%', term, '%'))
#             ORDER BY
#                 -- Prefer exact canonical match
#                 CASE
#                     WHEN LOWER(term) = LOWER(@term)       THEN 0
#                     WHEN LOWER(term) = LOWER(@normalized) THEN 1
#                     ELSE 2
#                 END
#             LIMIT 3
#         """

#         rows = list(
#             client.query(
#                 query,
#                 job_config=bigquery.QueryJobConfig(
#                     query_parameters=[
#                         bigquery.ScalarQueryParameter("term",       "STRING", term),
#                         bigquery.ScalarQueryParameter("normalized", "STRING", normalized),
#                     ]
#                 ),
#             ).result()
#         )

#         if rows:
#             return _build_result(term, dict(rows[0]), "bigquery_kaplan_metrics")

#     except Exception as exc:
#         return {
#             "term":           term,
#             "found":          False,
#             "error":          str(exc),
#             "agents_to_call": [],
#             "agent_to_call":  None,
#             "is_multi_source": False,
#             "source_system":  None,
#         }

#     # Term genuinely not in semantic layer
#     return {
#         "term":           term,
#         "found":          False,
#         "definition":     "Term not found in Kaplan semantic layer.",
#         "agents_to_call": [],
#         "agent_to_call":  None,
#         "is_multi_source": False,
#         "source_system":  None,
#     }


# rag_tool = FunctionTool(func=lookup_fp_and_a_term)

# tools/rag_tool.py
"""
Semantic layer lookup for the Kaplan FP&A Analytics Agent.

DESIGN PHILOSOPHY — "BQ is the only source of truth"
═══════════════════════════════════════════════════════════════════════════════
Everything that can change lives in BigQuery, not in this file:

  • Terms and aliases        → kaplan_metrics_new.aliases
  • Category → type mapping  → kaplan_config.category_type_map rows
  • Favorable direction      → kaplan_metrics_new.favorable_direction
  • Agents to call           → kaplan_metrics_new.agent_name
  • Filter operators         → kaplan_metrics_new.filters (JSON)
                               + kaplan_config.filter_op_template rows
  • Source normalisation     → kaplan_config.source_map rows
  • Period filter pattern    → kaplan_metrics_new.period_filter_pattern

ZERO hardcoded business logic in this file.

  New term/alias           → INSERT row into kaplan_metrics_new
  New category type        → INSERT into kaplan_config
  New filter operator      → INSERT into kaplan_config
  New agent                → UPDATE agent_name in kaplan_metrics_new
  New BQ column            → auto-included via SELECT *
  New sector               → INSERT into sector_config

DEFINITION STATUS GATE:
  confirmed   → proceed, return full routing context
  partial     → proceed, attach open_questions as caveat
  incomplete  → stop, return found=False + clear explanation
  blocked     → stop, return found=False + different explanation

PERIOD FILTER PATTERNS (new column — tells agents which SQL time pattern):
  yr_mnth        → WHERE yr=? AND mnth IN (?)          techtonic
  date_key_join  → JOIN d_date ON Date_Key WHERE Year=? Fact_DailyMetricsDetail
  close_date     → WHERE CloseDate >= ? AND <= ?        Salesforce
  none           → no time filter (calculations, blocked rows)
"""

import re
import json
import logging
from functools import lru_cache

from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

_BQ_PROJECT    = "robust-atrium-406105"
_BQ_DATASET    = "kaplan_semantic_layer"
_METRICS_TABLE = f"`{_BQ_PROJECT}.{_BQ_DATASET}.kaplan_metrics_new`"
_CONFIG_TABLE  = f"`{_BQ_PROJECT}.{_BQ_DATASET}.kaplan_config`"


# ─────────────────────────────────────────────────────────────────────────────
# BQ client singleton
# ─────────────────────────────────────────────────────────────────────────────

def _get_bq_client():
    from google.cloud import bigquery
    return bigquery.Client(project=_BQ_PROJECT)


# ─────────────────────────────────────────────────────────────────────────────
# Config cache
# Loaded from BQ once per process. Restart to refresh.
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_config() -> dict[str, str]:
    """
    Load kaplan_config into a flat key→value dict.
    Falls back to {} if the table is unavailable — safe defaults apply downstream.
    """
    try:
        rows = list(_get_bq_client().query(
            f"SELECT config_key, config_value FROM {_CONFIG_TABLE}"
        ).result())
        cfg = {r["config_key"]: r["config_value"] for r in rows}
        logger.info("kaplan_config loaded: %d keys", len(cfg))
        return cfg
    except Exception as exc:
        logger.warning("kaplan_config unavailable: %s — safe defaults apply.", exc)
        return {}


def _category_to_type(category: str) -> str:
    """
    Map BQ category → category_type used in agent instructions.
      metric / calculation / derived → Identity
      Causal/Influential             → Causal/Influential

    Resolution order:
      1. kaplan_config  category_type_map:<category_lower>
      2. Safe default   Identity
    """
    cfg = _load_config()
    key = f"category_type_map:{(category or '').lower().strip()}"
    return cfg.get(key, "Identity")


# ─────────────────────────────────────────────────────────────────────────────
# Filter SQL builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_filter_sql(filters_json: str | None) -> str:
    """
    Convert BQ filters JSON array → SQL WHERE clause fragment.

    Filter JSON format:
      [
        {"column": "eaType",     "operator": "IN",     "values": ["New","ORS"]},
        {"column": "isReported", "operator": "=",      "values": ["1"]},
        {"column": "StageName",  "operator": "NOT IN", "values": ["Closed Won","Closed Lost"]}
      ]

    Operator resolution:
      1. kaplan_config  filter_op_template:<OPERATOR>
      2. Built-in fallback  (=, !=, IN, NOT IN, >, <, >=, <=, LIKE, IS NULL,
                             IS NOT NULL, BETWEEN)
      3. Comment placeholder for unknown operators

    Add a new operator by inserting into kaplan_config — no code change needed.
    """
    if not filters_json:
        return ""
    try:
        filters = json.loads(filters_json) if isinstance(filters_json, str) else filters_json
    except (json.JSONDecodeError, TypeError):
        logger.warning("Could not parse filters JSON: %s", filters_json)
        return ""
    if not filters:
        return ""

    cfg     = _load_config()
    clauses: list[str] = []

    for f in filters:
        col  = f.get("column", "")
        op   = (f.get("operator") or "=").upper().strip()
        vals = f.get("values", [])

        val        = str(vals[0]) if vals else ""
        is_numeric = val.lstrip("-").replace(".", "", 1).isdigit()
        val_quoted = val if is_numeric else f"'{val}'"
        vals_quoted = ", ".join(
            v if v.lstrip("-").replace(".", "", 1).isdigit() else f"'{v}'"
            for v in vals
        )

        tkey = f"filter_op_template:{op}"
        if tkey in cfg:
            clause = cfg[tkey].format(
                col=col, val=val, val_quoted=val_quoted, vals=vals_quoted
            )
            clauses.append(clause)
            continue

        if op in ("IN", "NOT IN"):
            clauses.append(f"{col} {op} ({vals_quoted})")
        elif op in ("=", "!=", "<>", ">", "<", ">=", "<="):
            clauses.append(f"{col} {op} {val_quoted}")
        elif op == "LIKE":
            clauses.append(f"{col} LIKE '{val}'")
        elif op == "IS NULL":
            clauses.append(f"{col} IS NULL")
        elif op == "IS NOT NULL":
            clauses.append(f"{col} IS NOT NULL")
        elif op == "BETWEEN" and len(vals) >= 2:
            clauses.append(f"{col} BETWEEN '{vals[0]}' AND '{vals[1]}'")
        else:
            clauses.append(f"/* UNKNOWN OPERATOR '{op}' on {col} */")
            logger.warning("Unknown filter operator '%s' on '%s'", op, col)

    return " AND ".join(clauses)


# ─────────────────────────────────────────────────────────────────────────────
# Agent name parsing
# ─────────────────────────────────────────────────────────────────────────────

def _parse_agents(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [a.strip() for a in raw.split(",") if a.strip()]


# ─────────────────────────────────────────────────────────────────────────────
# Result scoring — lower score = better match
# ─────────────────────────────────────────────────────────────────────────────

def _score_row(row: dict, term: str, resolved: str) -> int:
    """
    0 — exact match on canonical term == original input
    1 — exact match on canonical term == BQ-resolved alias
    2 — word-boundary match in aliases on original input
    3 — word-boundary match in aliases on resolved input
    4 — fallback substring match
    """
    canonical   = (row.get("term") or "").lower().strip()
    aliases_raw = (row.get("aliases") or "").lower()
    term_l      = term.lower().strip()
    resolved_l  = resolved.lower().strip()

    if canonical == term_l:
        return 0
    if canonical == resolved_l:
        return 1

    def _wb(needle: str, hay: str) -> bool:
        return bool(re.search(
            r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])", hay
        ))

    if _wb(term_l, aliases_raw):
        return 2
    if _wb(resolved_l, aliases_raw):
        return 3
    return 4


# ─────────────────────────────────────────────────────────────────────────────
# Definition status gate responses
# ─────────────────────────────────────────────────────────────────────────────

def _gate_blocked(term: str, row: dict) -> dict:
    """
    Return a clear not-found response for blocked metrics.
    Blocked = the metric is defined but has NO queryable database source.
    Example: LTV lives in a Google Sheet, not a database.
    """
    return {
        "term":              term,
        "canonical_term":    row.get("term"),
        "found":             False,
        "definition_status": "blocked",
        "category":          row.get("category"),
        "category_type":     _category_to_type(row.get("category") or ""),
        "definition":        row.get("definition"),
        "owner":             row.get("owner"),
        "agents_to_call":    [],
        "agent_to_call":     None,
        "is_multi_source":   False,
        "source_system":     row.get("source_system"),
        "reason": (
            f"'{row.get('term')}' is defined in the semantic layer but has no "
            f"queryable database source. "
            f"{row.get('open_questions') or ''} "
            f"Contact {row.get('owner') or 'the data team'} to expose this "
            f"as a queryable field before the agent can compute it."
        ),
    }


def _gate_incomplete(term: str, row: dict) -> dict:
    """
    Return a clear not-found response for incomplete metrics.
    Incomplete = source table/field not yet confirmed with client.
    Example: Oracle tuition table pending Finance team sign-off.
    """
    return {
        "term":              term,
        "canonical_term":    row.get("term"),
        "found":             False,
        "definition_status": "incomplete",
        "category":          row.get("category"),
        "category_type":     _category_to_type(row.get("category") or ""),
        "definition":        row.get("definition"),
        "owner":             row.get("owner"),
        "agents_to_call":    [],
        "agent_to_call":     None,
        "is_multi_source":   False,
        "source_system":     row.get("source_system"),
        "reason": (
            f"'{row.get('term')}' is defined but its source table and field "
            f"have not been confirmed yet. "
            f"{row.get('open_questions') or 'Pending source confirmation.'} "
            f"Owner: {row.get('owner') or 'unknown'}. "
            f"Once the source is confirmed, update table_name and field_name "
            f"in kaplan_metrics_new and set definition_status = confirmed."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Result builder
# SELECT * means any new BQ columns are included automatically via extra_fields
# ─────────────────────────────────────────────────────────────────────────────

# Columns we explicitly promote to named fields in the result dict.
# Everything else from SELECT * goes into extra_fields automatically.
_KNOWN_FIELDS = {
    "term", "aliases", "definition", "category", "sector",
    "source_system", "agent_name", "table_name", "field_name",
    "filters", "related_terms", "calculation", "formula_logic",
    "open_questions", "favorable_direction", "period_grain",
    "yoy_comparison_default", "group_by_columns", "is_derived",
    "depends_on", "definition_status", "owner", "reference_sql",
    "period_filter_pattern", "last_updated", "source_doc_version",
}


def _build_result(original_term: str, row: dict, source: str) -> dict:
    """
    Build the full routing context dict returned to bi_agent.

    Named fields cover everything agents need directly.
    extra_fields captures any future BQ columns automatically —
    no code change needed when new columns are added to the table.
    """
    agents       = _parse_agents(row.get("agent_name"))
    raw_category = row.get("category") or ""
    status       = row.get("definition_status") or "incomplete"

    result = {
        # ── Identity ──────────────────────────────────────────────────────
        "term":              original_term,
        "canonical_term":    row.get("term"),
        "found":             True,
        "source":            source,
        "sector":            row.get("sector") or "higher_ed",

        # ── Trust ─────────────────────────────────────────────────────────
        # definition_status is included so agents can surface it if needed.
        # The gate already ran before _build_result is called, so arriving
        # here means status is confirmed or partial.
        "definition_status": status,
        "owner":             row.get("owner"),
        "open_questions":    row.get("open_questions"),   # non-None for partial rows

        # ── Routing ───────────────────────────────────────────────────────
        "agents_to_call":    agents,
        "agent_to_call":     agents[0] if len(agents) == 1 else None,
        "is_multi_source":   len(agents) > 1,

        # ── Classification ────────────────────────────────────────────────
        "category":          raw_category,
        "category_type":     _category_to_type(raw_category),
        # category_type tells the agent HOW to answer:
        #   Identity          → run SQL, return exact number
        #   Causal/Influential → reason narratively, do not run SQL

        # ── Favorability ──────────────────────────────────────────────────
        # Passed directly to calculator_tool — no translation needed.
        #   higher  → increase = Favorable  (starts, census, revenue)
        #   lower   → decrease = Favorable  (drop rate, attrition)
        #   neutral → no label             (mix %, ratios)
        "favorable_direction": row.get("favorable_direction") or "higher",

        # ── Data location ─────────────────────────────────────────────────
        "source_system":  row.get("source_system"),
        "table":          row.get("table_name"),
        "field":          row.get("field_name"),
        "filters":        row.get("filters"),
        "filter_sql":     _build_filter_sql(row.get("filters")),  # ready-to-append

        # ── Period / time filter ──────────────────────────────────────────
        # period_filter_pattern tells mssql_agent which SQL time pattern to use:
        #   yr_mnth       → WHERE yr=? AND mnth IN (?)
        #   date_key_join → JOIN rptobjects.dbo.d_date dt ON dm.Date_Key=dt.Date_Key
        #                   WHERE dt.Year=? AND dt.Month IN (?)
        #   close_date    → WHERE CloseDate >= ? AND CloseDate <= ?
        #   none          → no time filter (calculations, blocked rows)
        "period_filter_pattern":  row.get("period_filter_pattern") or "none",
        "period_grain":           row.get("period_grain"),
        "group_by_columns":       row.get("group_by_columns"),
        "yoy_comparison_default": row.get("yoy_comparison_default"),

        # ── Computation ───────────────────────────────────────────────────
        "calculation":   row.get("calculation"),
        "formula_logic": row.get("formula_logic"),
        "is_derived":    row.get("is_derived"),
        "depends_on":    row.get("depends_on"),

        # ── Enrichment ────────────────────────────────────────────────────
        "definition":    row.get("definition"),
        "related_terms": row.get("related_terms"),
        "aliases":       row.get("aliases"),
        "reference_sql": row.get("reference_sql"),
    }

    # Attach any future BQ columns automatically — zero code change needed
    extra = {k: v for k, v in row.items() if k not in _KNOWN_FIELDS and v is not None}
    if extra:
        result["extra_fields"] = extra

    return result


# ─────────────────────────────────────────────────────────────────────────────
# BQ alias pre-resolution
# Replaces ALL hardcoded alias maps — aliases live 100% in BQ
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_via_bq(term: str, client) -> str:
    """
    Check whether `term` matches any alias in kaplan_metrics_new.
    Returns the canonical term if found, otherwise returns the original term.
    Uses word-boundary regex so 'starts' doesn't match 'new starts by channel'.
    """
    try:
        from google.cloud import bigquery
        rows = list(client.query(
            f"""
            SELECT term FROM {_METRICS_TABLE}
            WHERE REGEXP_CONTAINS(
                LOWER(IFNULL(aliases, '')),
                CONCAT('(^|,|\\\\s)', LOWER(@term), '($|,|\\\\s)')
            )
            LIMIT 1
            """,
            job_config=bigquery.QueryJobConfig(query_parameters=[
                bigquery.ScalarQueryParameter("term", "STRING", term),
            ]),
        ).result())
        if rows:
            return rows[0]["term"]
    except Exception:
        pass
    return term


# ─────────────────────────────────────────────────────────────────────────────
# Public tool function
# ─────────────────────────────────────────────────────────────────────────────

def lookup_fp_and_a_term(term: str) -> dict:
    """
    Look up a Kaplan FP&A business term from the semantic layer.
    Table: kaplan_semantic_layer.kaplan_metrics_new

    Returns a routing context dict for bi_agent. Key fields:

      found                → False if blocked/incomplete/not found
      definition_status    → confirmed | partial | incomplete | blocked
      reason               → plain-English explanation when found=False
      agents_to_call       → list of sub-agents to call
      is_multi_source      → True if 2+ agents needed (bi_parallel)
      category_type        → Identity | Causal/Influential
      favorable_direction  → higher | lower | neutral  (→ calculator_tool)
      filter_sql           → ready-to-append WHERE fragment
      period_filter_pattern → yr_mnth | date_key_join | close_date | none
      formula_logic        → how to compute / what SQL to build
      is_derived           → True if component metrics must be fetched first
      depends_on           → parent metric terms for derived metrics
      open_questions       → caveat text for partial rows (attach to response)
      owner                → metric owner — cite in agent responses

    FUTURE-PROOF:
      New metric/alias     → INSERT into kaplan_metrics_new     No code change
      New category         → INSERT into kaplan_config          No code change
      New filter operator  → INSERT into kaplan_config          No code change
      New agent            → UPDATE agent_name column           No code change
      New BQ column        → auto-included via SELECT *         No code change
      New sector           → INSERT into sector_config          No code change

    Args:
        term: Exactly what the user said — do not pre-translate.
              The tool handles all NLP normalisation via BQ alias matching.
    """
    term = (term or "").strip()
    if not term:
        return {
            "term":            term,
            "found":           False,
            "error":           "Empty term provided.",
            "agents_to_call":  [],
            "agent_to_call":   None,
            "is_multi_source": False,
            "source_system":   None,
        }

    try:
        from google.cloud import bigquery
        client = _get_bq_client()

        # ── Step 1: BQ-driven alias resolution ────────────────────────────
        # No hardcoded maps. New aliases in BQ are picked up automatically.
        resolved = _resolve_via_bq(term, client)

        # ── Step 2: Main lookup ───────────────────────────────────────────
        # SELECT * — new BQ columns appear in result automatically.
        query = f"""
            SELECT *
            FROM {_METRICS_TABLE}
            WHERE
                LOWER(term) = LOWER(@term)
                OR LOWER(term) = LOWER(@resolved)
                OR REGEXP_CONTAINS(
                    LOWER(IFNULL(aliases, '')),
                    CONCAT('(^|,|\\\\s)', LOWER(@term), '($|,|\\\\s)')
                )
                OR REGEXP_CONTAINS(
                    LOWER(IFNULL(aliases, '')),
                    CONCAT('(^|,|\\\\s)', LOWER(@resolved), '($|,|\\\\s)')
                )
                OR (
                    LENGTH(@term) >= 4
                    AND LOWER(IFNULL(aliases, '')) LIKE LOWER(CONCAT('%', @term, '%'))
                )
            LIMIT 5
        """

        rows = list(client.query(
            query,
            job_config=bigquery.QueryJobConfig(query_parameters=[
                bigquery.ScalarQueryParameter("term",     "STRING", term),
                bigquery.ScalarQueryParameter("resolved", "STRING", resolved),
            ]),
        ).result())

        if not rows:
            return {
                "term":  term,
                "found": False,
                "definition": (
                    f"'{term}' not found in the Kaplan semantic layer. "
                    f"To add it: INSERT a row into kaplan_metrics_new, "
                    f"or add an alias to an existing row."
                ),
                "agents_to_call":  [],
                "agent_to_call":   None,
                "is_multi_source": False,
                "source_system":   None,
            }

        # ── Step 3: Pick best match ────────────────────────────────────────
        best = min(
            [dict(r) for r in rows],
            key=lambda r: _score_row(r, term, resolved),
        )

        # ── Step 4: Definition status gate ────────────────────────────────
        # This is the core safety mechanism.
        # blocked and incomplete rows are known but not queryable.
        # The agent must surface a helpful explanation, not an error.
        status = best.get("definition_status") or "incomplete"

        if status == "blocked":
            return _gate_blocked(term, best)

        if status == "incomplete":
            return _gate_incomplete(term, best)

        # ── Step 5: Build result for confirmed / partial ───────────────────
        result = _build_result(term, best, "bigquery_kaplan_metrics_new")

        # For partial rows: open_questions is already in the result.
        # The agent instruction must check open_questions and attach it
        # as a caveat in its response when it is non-None.
        if status == "partial":
            result["caveat"] = (
                f"Note: this metric has an open question — "
                f"{best.get('open_questions', '')} "
                f"This result should be treated as provisional until confirmed "
                f"by {best.get('owner', 'the data team')}."
            )

        return result

    except Exception as exc:
        logger.error("RAG tool error for '%s': %s", term, exc, exc_info=True)
        return {
            "term":            term,
            "found":           False,
            "error":           str(exc),
            "agents_to_call":  [],
            "agent_to_call":   None,
            "is_multi_source": False,
            "source_system":   None,
        }


rag_tool = FunctionTool(func=lookup_fp_and_a_term)
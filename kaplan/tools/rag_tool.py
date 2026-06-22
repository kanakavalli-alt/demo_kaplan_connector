
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

# tools/rag_tool.py
"""
Semantic layer lookup for the Kaplan FP&A Analytics Agent.
"""

import os
from google.adk.tools import FunctionTool


# ── Fast-path cache ───────────────────────────────────────────────────────────
# Keep this SHORT — it is only for the highest-frequency aliases that save a
# BigQuery round-trip.  All other normalisation is handled by the BQ
# aliases column (which you updated via bq UPDATE).
FAST_PATH_MAP: dict[str, str] = {
    "actual revenue":             "revenue",
    "oracle revenue":             "revenue",
    "headcount":                  "census",
    "rps":                        "revenue per student",
    "dropout rate":               "drop rate",
    "course load":                "average credit hours per student",
    "tuition rate":               "realized tuition per credit hour",
    "ltv":                        "lifetime value",
    "closed won pipeline":        "closed won revenue",
    "open pipeline":              "pipeline",
    # New:
    "closed won opportunities":   "closed won revenue",
    "won deals":                  "closed won revenue",
    "won opportunities":          "closed won revenue",
    "pipeline value":             "pipeline",
    "open opportunities":         "pipeline",
    "total pipeline":             "pipeline",
    "crm leads":                  "lead volume",
    "salesforce leads":           "lead volume",
    "number of leads":            "lead volume",
}

# ── Category mapping ──────────────────────────────────────────────────────────
# BQ stores "metric" / "calculation" / "dimension".
# Agent instructions use "Identity" / "Causal/Influential".
# Dimensions (channel mix shift, military mix, etc.) are causal drivers;
# KPI metrics and calculation helpers are Identity.
_CATEGORY_TYPE_MAP: dict[str, str] = {
    "metric":      "Identity",
    "calculation": "Identity",
    "dimension":   "Causal/Influential",
}


def _normalize_term(term: str) -> str:
    """Fast-path alias resolution before hitting BigQuery."""
    key = term.strip().lower()
    if key in FAST_PATH_MAP:
        return FAST_PATH_MAP[key]
    # Partial-match fallback (keeps the map useful for compound phrases)
    for alias, canonical in FAST_PATH_MAP.items():
        if alias in key:
            return canonical
    return term


def _parse_agents(raw: str | None) -> list[str]:
    """
    Convert BQ agent_name string → Python list.
    "oracle_agent,redshift_agent" → ["oracle_agent", "redshift_agent"]
    """
    if not raw:
        return []
    return [a.strip() for a in raw.split(",") if a.strip()]


def _build_result(term: str, row: dict, source: str) -> dict:
    """Build the normalised result dict from a BQ/cache row."""
    raw_category = (row.get("category") or "").lower()
    agents = _parse_agents(row.get("agent_name"))
    return {
        "term":           term,
        "found":          True,
        "source":         source,
        # ── Routing ───────────────────────────────────────────────────────────
        "agents_to_call": agents,                        # list — always use this
        "agent_to_call":  agents[0] if len(agents) == 1 else None,  # single-agent convenience
        "is_multi_source": len(agents) > 1,
        # ── Classification ────────────────────────────────────────────────────
        "category":       row.get("category"),           # raw BQ value
        "category_type":  _CATEGORY_TYPE_MAP.get(raw_category, "Identity"),
        # ── Data location ─────────────────────────────────────────────────────
        "source_system":  row.get("source_system"),
        "table":          row.get("table_name"),
        "field":          row.get("field_name"),
        "filters":        row.get("filters"),
        # ── Computation ───────────────────────────────────────────────────────
        "calculation":    row.get("calculation"),
        "formula_logic":  row.get("formula_logic"),
        # ── Enrichment ────────────────────────────────────────────────────────
        "definition":     row.get("definition"),
        "related_terms":  row.get("related_terms"),
        "use_cases":      row.get("use_cases"),
        "open_questions": row.get("open_questions"),
    }


def lookup_fp_and_a_term(term: str) -> dict:
    """
    Look up a Kaplan FP&A business term from the semantic layer
    (kaplan_semantic_layer.kaplan_metrics in BigQuery).

    The result tells bi_agent:
      • agents_to_call  → list of agents needed (split for you already)
      • is_multi_source → True if 2+ agents required → use bi_parallel
      • category_type   → "Identity" (KPI) or "Causal/Influential" (driver)
      • table / field / filters → exact query targets
      • calculation / formula_logic → how to compute the metric

    Args:
        term: Business term e.g. "revenue", "new starts", "drop rate",
              "channel mix shift", "revenue per student".
              Natural-language variants like "headcount", "course load",
              "dropout rate" are automatically resolved via alias matching.

    Returns:
        Dictionary with full routing context.
    """
    normalized = _normalize_term(term)

    try:
        from google.cloud import bigquery

        # Use the project that owns the semantic layer dataset
        client = bigquery.Client(project="robust-atrium-406105")

        query = """
            SELECT
                term,
                aliases,
                definition,
                category,
                source_system,
                agent_name,
                table_name,
                field_name,
                filters,
                related_terms,
                calculation,
                use_cases,
                formula_logic,
                open_questions
            FROM `robust-atrium-406105.kaplan_semantic_layer.kaplan_metrics_new`
            WHERE
                -- Exact match on canonical term (highest priority)
                LOWER(term) = LOWER(@term)
                -- Normalized term also checked (fast-path resolved)
                OR LOWER(term) = LOWER(@normalized)
                -- BQ alias column contains the searched term
                OR LOWER(IFNULL(aliases, '')) LIKE LOWER(CONCAT('%', @term, '%'))
                OR LOWER(IFNULL(aliases, '')) LIKE LOWER(CONCAT('%', @normalized, '%'))
                -- Searched term contains the canonical term (substring)
                OR LOWER(@term) LIKE LOWER(CONCAT('%', term, '%'))
            ORDER BY
                -- Prefer exact canonical match
                CASE
                    WHEN LOWER(term) = LOWER(@term)       THEN 0
                    WHEN LOWER(term) = LOWER(@normalized) THEN 1
                    ELSE 2
                END
            LIMIT 3
        """

        rows = list(
            client.query(
                query,
                job_config=bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("term",       "STRING", term),
                        bigquery.ScalarQueryParameter("normalized", "STRING", normalized),
                    ]
                ),
            ).result()
        )

        if rows:
            return _build_result(term, dict(rows[0]), "bigquery_kaplan_metrics")

    except Exception as exc:
        return {
            "term":           term,
            "found":          False,
            "error":          str(exc),
            "agents_to_call": [],
            "agent_to_call":  None,
            "is_multi_source": False,
            "source_system":  None,
        }

    # Term genuinely not in semantic layer
    return {
        "term":           term,
        "found":          False,
        "definition":     "Term not found in Kaplan semantic layer.",
        "agents_to_call": [],
        "agent_to_call":  None,
        "is_multi_source": False,
        "source_system":  None,
    }


rag_tool = FunctionTool(func=lookup_fp_and_a_term)
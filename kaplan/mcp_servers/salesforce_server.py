# import sys, os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from mcp.server.fastmcp import FastMCP
# from mock_data import MOCK_SALESFORCE_DATA

# mcp = FastMCP("salesforce_mock_server")

# @mcp.tool()
# def query_salesforce(metric: str, period: str = None, filters: dict = None) -> dict:
#     """
#     Query Salesforce for pipeline and closed-won revenue (mock).
    
#     Args:
#         metric: One of 'pipeline'
#         period: Optional period filter e.g. 'Q3_2025'
#         filters: Optional field:value filters e.g. {"stage": "closed_won"}
#     """
#     if metric not in MOCK_SALESFORCE_DATA:
#         return {"error": f"Unknown metric '{metric}'. Available: {list(MOCK_SALESFORCE_DATA.keys())}"}
    
#     records = MOCK_SALESFORCE_DATA[metric]
#     if period:
#         records = [r for r in records if r.get("period") == period]
#     if filters:
#         for field, value in filters.items():
#             records = [r for r in records if str(r.get(field, "")).lower() == str(value).lower()]
    
#     return {"source": "salesforce", "metric": metric, "records": records, "count": len(records)}

# if __name__ == "__main__":
#     mcp.run(transport="stdio")

# mcp_servers/salesforce_server.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from simple_salesforce import Salesforce, SalesforceAuthenticationFailed
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("salesforce_server")

def get_connection():
    """Authenticates an External Client App using pure OAuth2 Client Credentials Flow."""
    import os
    import requests
    from simple_salesforce import Salesforce

    domain = os.getenv("SF_DOMAIN")
    client_id = os.getenv("SF_CLIENT_ID")
    client_secret = os.getenv("SF_CLIENT_SECRET")
    domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
    # 🌟 Manually hit the precise token endpoint for External Client Apps
    token_url = f"https://{domain}/services/oauth2/token"
    
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    response = requests.post(token_url, data=payload)
    
    if response.status_code != 200:
        raise Exception(f"OAuth Token Exchange Failed: {response.text}")
        
    token_data = response.json()
    access_token = token_data.get("access_token")
    instance_url = token_data.get("instance_url", f"https://{domain}")

    # Use the generated short-lived session token to securely instantiate the client
    return Salesforce(
        instance_url=instance_url,
        session_id=access_token
    )

@mcp.tool()
def query_salesforce_opportunities(
    stage: str = None,
    period_year: int = None,
    period_quarter: int = None,
    business_type: str = None,
    limit: int = 50
) -> dict:
    """
    Query Salesforce Opportunities for revenue and pipeline analysis.

    Args:
        stage: Filter by stage. Options:
               'Closed Won' - recognized revenue
               'Closed Lost' - lost deals
               'open' - all open pipeline (not closed)
               None - all opportunities
        period_year: Filter by close date year e.g. 2025
        period_quarter: Filter by close date quarter 1-4
        business_type: Filter by Type field e.g. 'New Customer',
                      'Existing Customer - Upgrade'. None = all.
        limit: Max records to return (default 50)

    Returns:
        Dictionary with opportunity records including Amount, StageName, CloseDate.
    """
    try:
        sf = get_connection()

        # Build SOQL query
        where_clauses = []

        if stage == "Closed Won":
            where_clauses.append("StageName = 'Closed Won'")
        elif stage == "Closed Lost":
            where_clauses.append("StageName = 'Closed Lost'")
        elif stage == "open":
            where_clauses.append("StageName NOT IN ('Closed Won', 'Closed Lost')")

        if period_year and period_quarter:
            quarter_months = {
                1: ("01-01", "03-31"),
                2: ("04-01", "06-30"),
                3: ("07-01", "09-30"),
                4: ("10-01", "12-31"),
            }
            start, end = quarter_months.get(period_quarter, ("01-01", "12-31"))
            where_clauses.append(
                f"CloseDate >= {period_year}-{start} AND CloseDate <= {period_year}-{end}"
            )
        elif period_year:
            where_clauses.append(
                f"CloseDate >= {period_year}-01-01 AND CloseDate <= {period_year}-12-31"
            )

        if business_type:
            where_clauses.append(f"Type = '{business_type}'")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        soql = f"""
            SELECT Id, Name, Amount, StageName, CloseDate,
                   Type, Probability, ExpectedRevenue,
                   AccountId, OwnerId, FiscalYear, FiscalQuarter
            FROM Opportunity
            {where_sql}
            ORDER BY CloseDate DESC
            LIMIT {limit}
        """

        result = sf.query(soql)
        records = result.get("records", [])

        clean_records = [
            {k: v for k, v in r.items() if k != "attributes"}
            for r in records
        ]

        total_amount = sum(
            r.get("Amount") or 0
            for r in clean_records
        )

        return {
            "source": "salesforce",
            "query": soql.strip(),
            "records": clean_records,
            "count": len(clean_records),
            "total_amount": total_amount,
            "total_size": result.get("totalSize", 0),
            "status": "success"
        }

    except SalesforceAuthenticationFailed as e:
        return {
            "source": "salesforce",
            "records": [],
            "count": 0,
            "status": "error",
            "error": f"Authentication failed: {str(e)}"
        }
    except Exception as e:
        return {
            "source": "salesforce",
            "records": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def query_salesforce_accounts(
    industry: str = None,
    limit: int = 50
) -> dict:
    """
    Query Salesforce Accounts for customer/institution data.

    Args:
        industry: Filter by industry e.g. 'Education', 'Technology'. None = all.
        limit: Max records to return (default 50)

    Returns:
        Dictionary with account records.
    """
    try:
        sf = get_connection()

        where_clauses = []
        if industry:
            where_clauses.append(f"Industry = '{industry}'")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        soql = f"""
            SELECT Id, Name, Industry, Type,
                   AnnualRevenue, NumberOfEmployees,
                   BillingCity, BillingCountry
            FROM Account
            {where_sql}
            ORDER BY Name
            LIMIT {limit}
        """

        result = sf.query(soql)
        records = result.get("records", [])
        clean_records = [
            {k: v for k, v in r.items() if k != "attributes"}
            for r in records
        ]

        return {
            "source": "salesforce",
            "records": clean_records,
            "count": len(clean_records),
            "status": "success"
        }

    except Exception as e:
        return {
            "source": "salesforce",
            "records": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def query_salesforce_leads(
    status: str = None,
    limit: int = 50
) -> dict:
    """
    Query Salesforce Leads for prospective student data.

    Args:
        status: Filter by lead status e.g. 'Open', 'Converted'. None = all.
        limit: Max records to return (default 50)

    Returns:
        Dictionary with lead records.
    """
    try:
        sf = get_connection()

        where_clauses = []
        if status:
            where_clauses.append(f"Status = '{status}'")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        soql = f"""
            SELECT Id, Name, Status, LeadSource,
                   Company, Industry, IsConverted
            FROM Lead
            {where_sql}
            ORDER BY CreatedDate DESC
            LIMIT {limit}
        """

        result = sf.query(soql)
        records = result.get("records", [])
        clean_records = [
            {k: v for k, v in r.items() if k != "attributes"}
            for r in records
        ]

        return {
            "source": "salesforce",
            "records": clean_records,
            "count": len(clean_records),
            "status": "success"
        }

    except Exception as e:
        return {
            "source": "salesforce",
            "records": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
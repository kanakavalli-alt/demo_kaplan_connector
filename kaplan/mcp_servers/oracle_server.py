# # mcp_servers/oracle_server.py
# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from mcp.server.fastmcp import FastMCP
# from mock_data import MOCK_ORACLE_DATA

# mcp = FastMCP("oracle_mock_server")

# @mcp.tool()
# def query_oracle(metric: str, period: str = None, filters: dict = None) -> dict:
#     """
#     Query Oracle for financial data (mock).
    
#     Args:
#         metric: One of 'revenue', 'new_starts'
#         period: Optional period filter e.g. 'Q3_2025', 'Q3_2024'
#         filters: Optional field:value filters e.g. {"business_unit": "Higher Education"}
    
#     Returns:
#         Matching records from Oracle mock data.
#     """
#     if metric not in MOCK_ORACLE_DATA:
#         return {"error": f"Unknown metric '{metric}'. Available: {list(MOCK_ORACLE_DATA.keys())}"}
    
#     records = MOCK_ORACLE_DATA[metric]
    
#     if period:
#         records = [r for r in records if r.get("period") == period]
    
#     if filters:
#         for field, value in filters.items():
#             records = [r for r in records if str(r.get(field, "")).lower() == str(value).lower()]
    
#     return {"source": "oracle", "metric": metric, "records": records, "count": len(records)}

# if __name__ == "__main__":
#     mcp.run(transport="stdio")

# mcp_servers/oracle_server.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import oracledb
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("oracle_server")

def get_connection():
    return oracledb.connect(
        user=os.getenv("ORACLE_USER", "kanaka"),
        password=os.getenv("ORACLE_PASSWORD", "kaplan04"),
        dsn=f"{os.getenv('ORACLE_HOST', 'localhost')}:{os.getenv('ORACLE_PORT', '1521')}/{os.getenv('ORACLE_SERVICE', 'FREEPDB1')}"
    )

@mcp.tool()
def query_oracle_revenue(
    period: str = None,
    business_unit: str = None,
    channel: str = None
) -> dict:
    """
    Query Oracle for GAAP revenue data from fp_revenue table.
    
    Args:
        period: Period filter e.g. 'Q1_2025', 'Q3_2024'. None returns all periods.
        business_unit: Filter by 'Higher Education' or 'Supplemental'. None returns all.
        channel: Filter by 'Direct' or 'Aggregator'. None returns all.
    
    Returns:
        Dictionary with revenue records.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT period, business_unit, channel, amount FROM fp_revenue WHERE 1=1"
        params = {}

        if period:
            query += " AND period = :period"
            params["period"] = period
        if business_unit:
            query += " AND LOWER(business_unit) = LOWER(:business_unit)"
            params["business_unit"] = business_unit
        if channel:
            query += " AND LOWER(channel) = LOWER(:channel)"
            params["channel"] = channel

        query += " ORDER BY period, business_unit, channel"

        cursor.execute(query, params)
        columns = [col[0].lower() for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return {
            "source": "oracle",
            "table": "fp_revenue",
            "records": rows,
            "count": len(rows),
            "status": "success"
        }
    except Exception as e:
        return {
            "source": "oracle",
            "table": "fp_revenue",
            "records": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def query_oracle_new_starts(
    period: str = None,
    business_unit: str = None,
    channel: str = None,
    segment: str = None
) -> dict:
    """
    Query Oracle for new student starts data from fp_new_starts table.

    Args:
        period: Period filter e.g. 'Q1_2025'. None returns all.
        business_unit: 'Higher Education' or 'Supplemental'. None returns all.
        channel: 'Direct' or 'Aggregator'. None returns all.
        segment: 'Degree' or 'Certificate'. None returns all.

    Returns:
        Dictionary with new starts records.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT period, business_unit, channel, segment, count FROM fp_new_starts WHERE 1=1"
        params = {}

        if period:
            query += " AND period = :period"
            params["period"] = period
        if business_unit:
            query += " AND LOWER(business_unit) = LOWER(:business_unit)"
            params["business_unit"] = business_unit
        if channel:
            query += " AND LOWER(channel) = LOWER(:channel)"
            params["channel"] = channel
        if segment:
            query += " AND LOWER(segment) = LOWER(:segment)"
            params["segment"] = segment

        query += " ORDER BY period, business_unit, channel"

        cursor.execute(query, params)
        columns = [col[0].lower() for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return {
            "source": "oracle",
            "table": "fp_new_starts",
            "records": rows,
            "count": len(rows),
            "status": "success"
        }
    except Exception as e:
        return {
            "source": "oracle",
            "table": "fp_new_starts",
            "records": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
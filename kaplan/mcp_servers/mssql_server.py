# import sys, os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from mcp.server.fastmcp import FastMCP
# from mock_data import MOCK_MSSQL_DATA

# mcp = FastMCP("mssql_mock_server")

# @mcp.tool()
# def query_mssql(metric: str, period: str = None, filters: dict = None) -> dict:
#     """
#     Query MS SQL Server for enrollment and program data (mock).
    
#     Args:
#         metric: One of 'enrollment'
#         period: Optional period filter e.g. 'Q3_2025'
#         filters: Optional field:value filters
#     """
#     if metric not in MOCK_MSSQL_DATA:
#         return {"error": f"Unknown metric '{metric}'. Available: {list(MOCK_MSSQL_DATA.keys())}"}
    
#     records = MOCK_MSSQL_DATA[metric]
#     if period:
#         records = [r for r in records if r.get("period") == period]
#     if filters:
#         for field, value in filters.items():
#             records = [r for r in records if str(r.get(field, "")).lower() == str(value).lower()]
    
#     return {"source": "mssql", "metric": metric, "records": records, "count": len(records)}

# if __name__ == "__main__":
#     mcp.run(transport="stdio")

# mcp_servers/mssql_server.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyodbc
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mssql_server")

def get_connection():
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.getenv('MSSQL_HOST', 'localhost')},{os.getenv('MSSQL_PORT', '1433')};"
        f"DATABASE={os.getenv('MSSQL_DB', 'kaplan_db')};"
        f"UID={os.getenv('MSSQL_USER', 'SA')};"
        f"PWD={os.getenv('MSSQL_PASSWORD', 'Kaplan@04')};"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


@mcp.tool()
def query_mssql_enrollment(
    period: str = None,
    program: str = None,
    business_unit: str = None
) -> dict:
    """
    Query MS SQL Server for enrollment and program performance data.

    Args:
        period: Period filter e.g. 'Q1_2025'. None returns all.
        program: Program name e.g. 'MBA Program', 'Bar Exam Prep'. None returns all.
        business_unit: 'Higher Education' or 'Supplemental'. None returns all.

    Returns:
        Dictionary with enrollment records including drop rates.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT period, program, business_unit, enrolled_count, drop_rate
            FROM fp_enrollment
            WHERE 1=1
        """
        params = []

        if period:
            query += " AND period = ?"
            params.append(period)
        if program:
            query += " AND LOWER(program) LIKE LOWER(?)"
            params.append(f"%{program}%")
        if business_unit:
            query += " AND LOWER(business_unit) = LOWER(?)"
            params.append(business_unit)

        query += " ORDER BY period, business_unit, program"

        cursor.execute(query, params)
        columns = [col[0].lower() for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return {
            "source": "mssql",
            "table": "fp_enrollment",
            "records": rows,
            "count": len(rows),
            "status": "success"
        }
    except Exception as e:
        return {
            "source": "mssql",
            "table": "fp_enrollment",
            "records": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
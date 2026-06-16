import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from mock_data import MOCK_REDSHIFT_DATA

mcp = FastMCP("redshift_mock_server")

@mcp.tool()
def query_redshift(metric: str, period: str = None, filters: dict = None) -> dict:
    """
    Query Redshift for census and headcount data (mock).
    
    Args:
        metric: One of 'census'
        period: Optional period filter e.g. 'Q3_2025'
        filters: Optional field:value filters e.g. {"status": "active"}
    """
    if metric not in MOCK_REDSHIFT_DATA:
        return {"error": f"Unknown metric '{metric}'. Available: {list(MOCK_REDSHIFT_DATA.keys())}"}
    
    records = MOCK_REDSHIFT_DATA[metric]
    if period:
        records = [r for r in records if r.get("period") == period]
    if filters:
        for field, value in filters.items():
            records = [r for r in records if str(r.get(field, "")).lower() == str(value).lower()]
    
    return {"source": "redshift", "metric": metric, "records": records, "count": len(records)}

if __name__ == "__main__":
    mcp.run(transport="stdio")
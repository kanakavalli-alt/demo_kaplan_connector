# mock_data.py

MOCK_ORACLE_DATA = {
    "revenue": [
        {"period": "Q3_2025", "business_unit": "Higher Education", "customer_type": "institutional", "amount": 4200000},
        {"period": "Q3_2025", "business_unit": "Higher Education", "customer_type": "retail", "amount": 1800000},
        {"period": "Q3_2025", "business_unit": "Supplemental Education", "customer_type": "institutional", "amount": 950000},
        {"period": "Q3_2025", "business_unit": "Supplemental Education", "customer_type": "retail", "amount": 620000},
        {"period": "Q3_2024", "business_unit": "Higher Education", "customer_type": "institutional", "amount": 3900000},
        {"period": "Q3_2024", "business_unit": "Higher Education", "customer_type": "retail", "amount": 1650000},
        {"period": "Q3_2024", "business_unit": "Supplemental Education", "customer_type": "institutional", "amount": 870000},
        {"period": "Q3_2024", "business_unit": "Supplemental Education", "customer_type": "retail", "amount": 580000},
    ],
    "new_starts": [
        {"period": "Q3_2025", "channel": "direct", "segment": "degree", "count": 1240},
        {"period": "Q3_2025", "channel": "aggregator", "segment": "degree", "count": 890},
        {"period": "Q3_2025", "channel": "direct", "segment": "certificate", "count": 530},
        {"period": "Q3_2024", "channel": "direct", "segment": "degree", "count": 1100},
        {"period": "Q3_2024", "channel": "aggregator", "segment": "degree", "count": 950},
        {"period": "Q3_2024", "channel": "direct", "segment": "certificate", "count": 480},
    ]
}

MOCK_REDSHIFT_DATA = {
    "census": [
        {"period": "Q3_2025", "status": "active", "count": 18400, "segment": "degree"},
        {"period": "Q3_2025", "status": "active", "count": 4200, "segment": "certificate"},
        {"period": "Q3_2025", "status": "graduated", "count": 1100, "segment": "degree"},
        {"period": "Q3_2025", "status": "dropped", "count": 620, "segment": "degree"},
        {"period": "Q3_2024", "status": "active", "count": 17200, "segment": "degree"},
        {"period": "Q3_2024", "status": "active", "count": 3900, "segment": "certificate"},
        {"period": "Q3_2024", "status": "graduated", "count": 980, "segment": "degree"},
        {"period": "Q3_2024", "status": "dropped", "count": 710, "segment": "degree"},
    ]
}

MOCK_MSSQL_DATA = {
    "enrollment": [
        {"period": "Q3_2025", "program": "MBA", "starts": 420, "drops": 38, "conversions": 0.91},
        {"period": "Q3_2025", "program": "Nursing", "starts": 310, "drops": 22, "conversions": 0.93},
        {"period": "Q3_2025", "program": "Bar Prep", "starts": 890, "drops": 95, "conversions": 0.89},
        {"period": "Q3_2024", "program": "MBA", "starts": 390, "drops": 41, "conversions": 0.89},
        {"period": "Q3_2024", "program": "Nursing", "starts": 280, "drops": 28, "conversions": 0.90},
        {"period": "Q3_2024", "program": "Bar Prep", "starts": 820, "drops": 102, "conversions": 0.88},
    ]
}

MOCK_SALESFORCE_DATA = {
    "pipeline": [
        {"period": "Q3_2025", "stage": "closed_won", "business_unit": "Higher Education", "amount": 5100000},
        {"period": "Q3_2025", "stage": "closed_won", "business_unit": "Supplemental Education", "amount": 1200000},
        {"period": "Q3_2025", "stage": "pipeline", "business_unit": "Higher Education", "amount": 3400000},
        {"period": "Q3_2024", "stage": "closed_won", "business_unit": "Higher Education", "amount": 4700000},
        {"period": "Q3_2024", "stage": "closed_won", "business_unit": "Supplemental Education", "amount": 1050000},
    ]
}

SEMANTIC_GLOSSARY = {
    "new starts": "Students enrolling for the first time in a given period. Source of record: Oracle. Decomposed by channel (direct vs aggregator), segment (degree vs certificate), and track-timing correction.",
    "census": "Total enrolled student headcount at a point in time. Measured in Redshift. Includes active, graduated, and dropped statuses.",
    "revenue per student": "Total closed-won GAAP revenue (Oracle) divided by active census count (Redshift). Military discounts create divergence between finance and enrollment figures.",
    "ytd": "Year-to-date. Fiscal year at Kaplan runs January through December.",
    "favorability": "A metric being favorable means actual performance exceeds plan or prior year. Unfavorable means below.",
    "channel mix shift": "Change in proportion of new starts coming from direct vs aggregator channels across periods.",
    "track-timing correction": "Adjustment for students who start mid-period and are counted in the following period's census.",
    "closed_won": "Salesforce opportunity stage representing confirmed revenue. Maps to GAAP revenue in Oracle.",
    "higher education": "Kaplan's degree-granting programs including MBA, Nursing, and professional certifications.",
    "supplemental education": "Test prep and bar exam preparation programs e.g. Bar Prep, MCAT, LSAT.",
    "variance": "Difference between actual and plan or prior year. Positive = favorable for revenue/starts. Negative = unfavorable.",
    "yoy": "Year-over-year comparison between the same period in current vs prior year.",
}
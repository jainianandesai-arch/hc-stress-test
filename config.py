"""
config.py
Standard Function → SOC Code Mapping
HC Transformation Intelligence Platform
Jaini Desai | jainidesai.com | June 2026

Defines the standard functions available in the tool.
Each function maps to O*NET SOC codes for live data pulls.
Company selects which functions apply to their org.
Custom functions mapped via O*NET keyword search.
"""

# ── Standard Functions ────────────────────────────────────────
# Each function contains standard roles pre-mapped to O*NET SOC codes.
# Headcount % split entered by user within each function.

STANDARD_FUNCTIONS = {

    "Finance & Accounting": {
        "description": "Financial planning, reporting, analysis, and control",
        "roles": [
            {"soc_code": "13-2051.00", "title": "Financial Analysts",               "default_pct": 30},
            {"soc_code": "13-2011.00", "title": "Accountants & Auditors",           "default_pct": 30},
            {"soc_code": "13-2061.00", "title": "Financial Examiners",              "default_pct": 20},
            {"soc_code": "43-3031.00", "title": "Bookkeeping & Accounting Clerks",  "default_pct": 20},
        ]
    },

    "HR & People Operations": {
        "description": "Talent acquisition, benefits, learning & development, HR operations",
        "roles": [
            {"soc_code": "13-1071.00", "title": "HR Specialists",                   "default_pct": 30},
            {"soc_code": "13-1141.00", "title": "Benefits & Compensation Specialists","default_pct": 25},
            {"soc_code": "13-1151.00", "title": "Training & Development Specialists","default_pct": 25},
            {"soc_code": "11-3121.00", "title": "HR Managers",                      "default_pct": 20},
        ]
    },

    "Technology & Engineering": {
        "description": "Software development, infrastructure, data, and systems",
        "roles": [
            {"soc_code": "15-1252.00", "title": "Software Developers",              "default_pct": 40},
            {"soc_code": "15-2051.00", "title": "Data Scientists",                  "default_pct": 25},
            {"soc_code": "15-1244.00", "title": "Network & Systems Administrators", "default_pct": 20},
            {"soc_code": "15-1299.00", "title": "Computer Occupations — Other",     "default_pct": 15},
        ]
    },

    "Operations & Supply Chain": {
        "description": "Planning, logistics, inventory, and process operations",
        "roles": [
            {"soc_code": "43-5071.00", "title": "Shipping & Inventory Clerks",      "default_pct": 35},
            {"soc_code": "43-5061.00", "title": "Production Planning Clerks",       "default_pct": 30},
            {"soc_code": "43-9021.00", "title": "Data Entry Keyers",                "default_pct": 20},
            {"soc_code": "13-1081.00", "title": "Logisticians",                     "default_pct": 15},
        ]
    },

    "Risk & Compliance": {
        "description": "Regulatory compliance, risk management, and legal operations",
        "roles": [
            {"soc_code": "13-1041.00", "title": "Compliance Officers",              "default_pct": 35},
            {"soc_code": "13-2061.00", "title": "Financial Examiners",              "default_pct": 25},
            {"soc_code": "23-2011.00", "title": "Paralegals",                       "default_pct": 25},
            {"soc_code": "13-2054.00", "title": "Financial Risk Specialists",       "default_pct": 15},
        ]
    },

    "Customer Service": {
        "description": "Customer support, service operations, and client relations",
        "roles": [
            {"soc_code": "43-4051.00", "title": "Customer Service Representatives", "default_pct": 50},
            {"soc_code": "43-4171.00", "title": "Receptionists",                    "default_pct": 25},
            {"soc_code": "41-3091.00", "title": "Sales Representatives",            "default_pct": 25},
        ]
    },

    "Sales & Business Development": {
        "description": "Revenue generation, account management, and market development",
        "roles": [
            {"soc_code": "41-4012.00", "title": "Sales Representatives — Wholesale","default_pct": 40},
            {"soc_code": "11-2022.00", "title": "Sales Managers",                   "default_pct": 30},
            {"soc_code": "41-2031.00", "title": "Retail Salespersons",              "default_pct": 30},
        ]
    },

    "Legal": {
        "description": "Legal counsel, contract management, and regulatory affairs",
        "roles": [
            {"soc_code": "23-1011.00", "title": "Lawyers",                          "default_pct": 50},
            {"soc_code": "23-2011.00", "title": "Paralegals",                       "default_pct": 30},
            {"soc_code": "13-1041.00", "title": "Compliance Officers",              "default_pct": 20},
        ]
    },

    "Marketing & Communications": {
        "description": "Brand, content, campaigns, and corporate communications",
        "roles": [
            {"soc_code": "11-2021.00", "title": "Marketing Managers",               "default_pct": 40},
            {"soc_code": "27-3031.00", "title": "Public Relations Specialists",     "default_pct": 30},
            {"soc_code": "13-1161.00", "title": "Market Research Analysts",         "default_pct": 30},
        ]
    },

    "Strategy & Corporate Development": {
        "description": "Corporate strategy, M&A, planning, and analytics",
        "roles": [
            {"soc_code": "13-1111.00", "title": "Management Analysts",              "default_pct": 40},
            {"soc_code": "15-2051.00", "title": "Data Scientists",                  "default_pct": 30},
            {"soc_code": "11-1021.00", "title": "General & Operations Managers",    "default_pct": 30},
        ]
    },
}

# ── Helper functions ──────────────────────────────────────────

def get_function_names():
    """Returns list of all standard function names."""
    return list(STANDARD_FUNCTIONS.keys())

def get_roles_for_function(function_name):
    """Returns role list for a given function."""
    return STANDARD_FUNCTIONS.get(function_name, {}).get("roles", [])

def get_all_soc_codes():
    """Returns all unique SOC codes across all functions."""
    codes = set()
    for fn in STANDARD_FUNCTIONS.values():
        for role in fn["roles"]:
            codes.add(role["soc_code"])
    return list(codes)

def build_role_list(function_name, headcount, pct_overrides=None):
    """
    Given a function name, total headcount for that function,
    and optional % overrides per role, returns a list of
    {soc_code, title, headcount} ready for the transformation engine.

    pct_overrides: dict of {soc_code: pct} — user-entered values.
    Falls back to default_pct if not provided.
    """
    roles = get_roles_for_function(function_name)
    result = []

    for role in roles:
        soc = role["soc_code"]
        pct = (pct_overrides or {}).get(soc, role["default_pct"]) / 100
        hc  = max(round(headcount * pct), 1)
        result.append({
            "soc_code":  soc,
            "title":     role["title"],
            "headcount": hc,
        })

    return result
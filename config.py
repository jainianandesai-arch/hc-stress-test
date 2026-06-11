"""
config.py
Standard Function → SOC Code Mapping + Capability Architecture
Workforce Transformation Intelligence™

© 2024–2026 Jaini Desai. All rights reserved.
Workforce Transformation Intelligence™ is an original methodology by Jaini Desai.
Employee Lifetime Value™ (ELV) and Leadership Momentum Index™ (LMI) are original
frameworks by Jaini Desai (2024). Unauthorized reproduction or commercial use
without written permission is prohibited.

Defines:
- Standard functions mapped to O*NET SOC codes
- Capability categories per function for Capability Gap Engine
- Helper functions for role list building
"""

# ── Standard Functions ────────────────────────────────────────
# Each function contains:
# - Standard roles pre-mapped to O*NET SOC codes
# - Capability categories required tomorrow (for Capability Gap Engine)
# Headcount % split entered by user within each function.

STANDARD_FUNCTIONS = {

    "Finance & Accounting": {
        "description": "Financial planning, reporting, analysis, and control",
        "roles": [
            {"soc_code": "13-2051.00", "title": "Financial Analysts",              "default_pct": 30},
            {"soc_code": "13-2011.00", "title": "Accountants & Auditors",          "default_pct": 30},
            {"soc_code": "13-2061.00", "title": "Financial Examiners",             "default_pct": 20},
            {"soc_code": "43-3031.00", "title": "Bookkeeping & Accounting Clerks", "default_pct": 20},
        ],
        "capabilities_tomorrow": [
            {"capability": "Data-driven financial decision making", "target_pct": 80, "current_pct": 35},
            {"capability": "AI-assisted forecasting and modelling", "target_pct": 75, "current_pct": 15},
            {"capability": "ESG and climate risk reporting",        "target_pct": 70, "current_pct": 20},
            {"capability": "Regulatory technology (RegTech)",       "target_pct": 65, "current_pct": 30},
            {"capability": "Financial data visualization",          "target_pct": 70, "current_pct": 40},
        ]
    },

    "HR & People Operations": {
        "description": "Talent acquisition, benefits, learning & development, HR operations",
        "roles": [
            {"soc_code": "13-1071.00", "title": "HR Specialists",                    "default_pct": 30},
            {"soc_code": "13-1141.00", "title": "Benefits & Compensation Specialists","default_pct": 25},
            {"soc_code": "13-1151.00", "title": "Training & Development Specialists", "default_pct": 25},
            {"soc_code": "11-3121.00", "title": "HR Managers",                       "default_pct": 20},
        ],
        "capabilities_tomorrow": [
            {"capability": "People analytics and workforce intelligence", "target_pct": 80, "current_pct": 20},
            {"capability": "AI-enabled talent acquisition",               "target_pct": 75, "current_pct": 15},
            {"capability": "Change management and transformation",         "target_pct": 80, "current_pct": 45},
            {"capability": "Workforce planning and scenario modelling",    "target_pct": 75, "current_pct": 25},
            {"capability": "Employee experience design",                   "target_pct": 70, "current_pct": 35},
        ]
    },

    "Technology & Engineering": {
        "description": "Software development, infrastructure, data, and systems",
        "roles": [
            {"soc_code": "15-1252.00", "title": "Software Developers",             "default_pct": 40},
            {"soc_code": "15-2051.00", "title": "Data Scientists",                 "default_pct": 25},
            {"soc_code": "15-1244.00", "title": "Network & Systems Administrators","default_pct": 20},
            {"soc_code": "15-1299.00", "title": "Computer Occupations — Other",    "default_pct": 15},
        ],
        "capabilities_tomorrow": [
            {"capability": "AI and machine learning engineering",    "target_pct": 85, "current_pct": 20},
            {"capability": "Cloud architecture and FinOps",          "target_pct": 80, "current_pct": 40},
            {"capability": "LLMOps and AI governance",               "target_pct": 75, "current_pct": 10},
            {"capability": "Prompt engineering and AI tooling",      "target_pct": 70, "current_pct": 15},
            {"capability": "Platform and product engineering",        "target_pct": 75, "current_pct": 45},
        ]
    },

    "Operations & Supply Chain": {
        "description": "Planning, logistics, inventory, and process operations",
        "roles": [
            {"soc_code": "43-5071.00", "title": "Shipping & Inventory Clerks", "default_pct": 35},
            {"soc_code": "43-5061.00", "title": "Production Planning Clerks",  "default_pct": 30},
            {"soc_code": "43-9021.00", "title": "Data Entry Keyers",           "default_pct": 20},
            {"soc_code": "13-1081.00", "title": "Logisticians",                "default_pct": 15},
        ],
        "capabilities_tomorrow": [
            {"capability": "AI-driven supply chain optimization", "target_pct": 80, "current_pct": 15},
            {"capability": "Process automation and RPA",          "target_pct": 75, "current_pct": 20},
            {"capability": "Predictive demand planning",          "target_pct": 70, "current_pct": 25},
            {"capability": "Sustainability and ESG operations",   "target_pct": 65, "current_pct": 20},
            {"capability": "Real-time data and analytics",        "target_pct": 75, "current_pct": 30},
        ]
    },

    "Risk & Compliance": {
        "description": "Regulatory compliance, risk management, and legal operations",
        "roles": [
            {"soc_code": "13-1041.00", "title": "Compliance Officers",        "default_pct": 35},
            {"soc_code": "13-2061.00", "title": "Financial Examiners",        "default_pct": 25},
            {"soc_code": "23-2011.00", "title": "Paralegals",                 "default_pct": 25},
            {"soc_code": "13-2054.00", "title": "Financial Risk Specialists", "default_pct": 15},
        ],
        "capabilities_tomorrow": [
            {"capability": "AI governance and model risk",          "target_pct": 85, "current_pct": 10},
            {"capability": "RegTech and automated compliance",      "target_pct": 80, "current_pct": 20},
            {"capability": "Cybersecurity risk management",         "target_pct": 75, "current_pct": 30},
            {"capability": "Data privacy and sovereign compliance", "target_pct": 80, "current_pct": 35},
            {"capability": "Climate and ESG risk frameworks",       "target_pct": 70, "current_pct": 15},
        ]
    },

    "Customer Service": {
        "description": "Customer support, service operations, and client relations",
        "roles": [
            {"soc_code": "43-4051.00", "title": "Customer Service Representatives","default_pct": 50},
            {"soc_code": "43-4171.00", "title": "Receptionists",                   "default_pct": 25},
            {"soc_code": "41-3091.00", "title": "Sales Representatives",           "default_pct": 25},
        ],
        "capabilities_tomorrow": [
            {"capability": "AI-assisted customer resolution",      "target_pct": 80, "current_pct": 15},
            {"capability": "Omnichannel service management",       "target_pct": 75, "current_pct": 30},
            {"capability": "Customer data and journey analytics",  "target_pct": 70, "current_pct": 20},
            {"capability": "Emotional intelligence and empathy",   "target_pct": 80, "current_pct": 60},
            {"capability": "Self-service platform management",     "target_pct": 70, "current_pct": 15},
        ]
    },

    "Sales & Business Development": {
        "description": "Revenue generation, account management, and market development",
        "roles": [
            {"soc_code": "41-4012.00", "title": "Sales Representatives — Wholesale","default_pct": 40},
            {"soc_code": "11-2022.00", "title": "Sales Managers",                   "default_pct": 30},
            {"soc_code": "41-2031.00", "title": "Retail Salespersons",              "default_pct": 30},
        ],
        "capabilities_tomorrow": [
            {"capability": "AI-powered sales intelligence",         "target_pct": 80, "current_pct": 15},
            {"capability": "Digital and social selling",            "target_pct": 75, "current_pct": 35},
            {"capability": "Revenue operations and analytics",      "target_pct": 75, "current_pct": 25},
            {"capability": "Consultative and solutions selling",    "target_pct": 80, "current_pct": 50},
            {"capability": "CRM and pipeline data discipline",      "target_pct": 70, "current_pct": 40},
        ]
    },

    "Legal": {
        "description": "Legal counsel, contract management, and regulatory affairs",
        "roles": [
            {"soc_code": "23-1011.00", "title": "Lawyers",            "default_pct": 50},
            {"soc_code": "23-2011.00", "title": "Paralegals",         "default_pct": 30},
            {"soc_code": "13-1041.00", "title": "Compliance Officers", "default_pct": 20},
        ],
        "capabilities_tomorrow": [
            {"capability": "Legal AI and contract automation",       "target_pct": 75, "current_pct": 10},
            {"capability": "AI ethics and governance counsel",       "target_pct": 80, "current_pct": 5},
            {"capability": "Data privacy law (PIPEDA, Law 25)",      "target_pct": 85, "current_pct": 40},
            {"capability": "Regulatory intelligence and monitoring", "target_pct": 75, "current_pct": 30},
            {"capability": "Cross-functional legal business partnering","target_pct": 70, "current_pct": 45},
        ]
    },

    "Marketing & Communications": {
        "description": "Brand, content, campaigns, and corporate communications",
        "roles": [
            {"soc_code": "11-2021.00", "title": "Marketing Managers",         "default_pct": 40},
            {"soc_code": "27-3031.00", "title": "Public Relations Specialists","default_pct": 30},
            {"soc_code": "13-1161.00", "title": "Market Research Analysts",   "default_pct": 30},
        ],
        "capabilities_tomorrow": [
            {"capability": "Generative AI content and campaigns",    "target_pct": 80, "current_pct": 20},
            {"capability": "Marketing data and attribution analytics","target_pct": 75, "current_pct": 30},
            {"capability": "Customer segmentation and personalization","target_pct": 75, "current_pct": 25},
            {"capability": "Brand trust in an AI world",             "target_pct": 70, "current_pct": 35},
            {"capability": "Digital and performance marketing",      "target_pct": 75, "current_pct": 40},
        ]
    },

    "Strategy & Corporate Development": {
        "description": "Corporate strategy, M&A, planning, and analytics",
        "roles": [
            {"soc_code": "13-1111.00", "title": "Management Analysts",           "default_pct": 40},
            {"soc_code": "15-2051.00", "title": "Data Scientists",               "default_pct": 30},
            {"soc_code": "11-1021.00", "title": "General & Operations Managers", "default_pct": 30},
        ],
        "capabilities_tomorrow": [
            {"capability": "AI strategy and transformation leadership","target_pct": 85, "current_pct": 15},
            {"capability": "Scenario planning and workforce forecasting","target_pct": 80, "current_pct": 25},
            {"capability": "M&A integration and capability assessment", "target_pct": 75, "current_pct": 30},
            {"capability": "Organizational design and operating model", "target_pct": 75, "current_pct": 25},
            {"capability": "Data literacy and evidence-based strategy", "target_pct": 80, "current_pct": 35},
        ]
    },
}

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_function_names():
    """Returns list of all standard function names."""
    return list(STANDARD_FUNCTIONS.keys())

def get_roles_for_function(function_name):
    """Returns role list for a given function."""
    return STANDARD_FUNCTIONS.get(function_name, {}).get("roles", [])

def get_capabilities_for_function(function_name):
    """
    Returns capability gap data for a given function.
    Used by Capability Gap Engine (Module 2).
    Each item: {capability, target_pct, current_pct, gap_pct, recommendation}
    Recommendation: Build / Buy / Partner based on gap size.
    """
    caps = STANDARD_FUNCTIONS.get(
        function_name, {}
    ).get("capabilities_tomorrow", [])

    result = []
    for cap in caps:
        gap_pct = cap["target_pct"] - cap["current_pct"]
        if gap_pct >= 50:
            recommendation = "Buy — hire externally"
        elif gap_pct >= 25:
            recommendation = "Build — reskill internally"
        else:
            recommendation = "Augment — coaching and tools"

        result.append({
            "capability":      cap["capability"],
            "target_pct":      cap["target_pct"],
            "current_pct":     cap["current_pct"],
            "gap_pct":         gap_pct,
            "recommendation":  recommendation,
        })

    return result

def get_all_soc_codes():
    """Returns all unique SOC codes across all functions."""
    codes = set()
    for fn in STANDARD_FUNCTIONS.values():
        for role in fn["roles"]:
            codes.add(role["soc_code"])
    return list(codes)

def build_role_list(function_name, headcount, pct_overrides=None):
    """
    Given a function name, total headcount, and optional % overrides,
    returns list of {soc_code, title, headcount} for transformation engine.
    Falls back to default_pct if overrides not provided.
    """
    roles  = get_roles_for_function(function_name)
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

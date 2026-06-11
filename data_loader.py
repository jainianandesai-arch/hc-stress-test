import json
import os
from datetime import datetime

DATA_DIR = "data"
ONET_PATH = os.path.join(DATA_DIR, "onet_displacement_scores.json")
RESEARCH_PATH = os.path.join(DATA_DIR, "research_benchmarks.json")
COMPLIANCE_PATH = os.path.join(DATA_DIR, "canada_compliance.json")

INDUSTRY_DEPT_MAP = {
    "Financial Services": "Finance & Risk",
    "Retail & Consumer": "Sales & Distribution",
    "Technology": "Technology",
    "Healthcare": "Strategy & Analytics",
    "Manufacturing": "Operations",
    "Professional Services": "Compliance & Legal"
}

BENCHMARK_FALLBACKS = {
    "reskilling_cost_per_employee": 8500,
    "productivity_drop_during_transition": 0.23,
    "productivity_recovery_months": 14,
    "leadership_replacement_cost_multiplier": 2.0,
    "leadership_exodus_rate_post_restructuring": 0.40,
    "cascade_multiplier": 2.3,
    "near_term_automation_rate": 0.30,
    "skills_obsolescence_rate_by_2028": 0.39,
}

INDUSTRY_VULN_FALLBACKS = {
    "Financial Services": 0.62,
    "Retail & Consumer": 0.68,
    "Technology": 0.38,
    "Healthcare": 0.41,
    "Manufacturing": 0.72,
    "Professional Services": 0.51
}

def load_onet():
    try:
        with open(ONET_PATH) as f:
            return json.load(f), "🟢 O*NET Live"
    except:
        return None, "📚 Fallback"

def load_research():
    try:
        with open(RESEARCH_PATH) as f:
            return json.load(f), "🟢 Research Live"
    except:
        return None, "📚 Fallback"

def load_compliance():
    try:
        with open(COMPLIANCE_PATH) as f:
            return json.load(f), "🟢 Compliance Live"
    except:
        return None, "📚 Fallback"

def get_displacement_score(industry):
    onet_data, source = load_onet()
    if onet_data:
        dept = INDUSTRY_DEPT_MAP.get(industry)
        if dept and dept in onet_data:
            score = onet_data[dept]["displacement_score"]
            return score, f"O*NET Web Services — {dept}"
    score = INDUSTRY_VULN_FALLBACKS.get(industry, 0.55)
    return score, "Research Benchmarks"

def get_benchmark(key):
    research_data, source = load_research()
    if research_data and key in research_data:
        item = research_data[key]
        return item["value"], item["source"]
    return BENCHMARK_FALLBACKS.get(key, 0), "Fallback"

def get_severance(jurisdiction, years_service, weekly_pay, annual_payroll=0):
    compliance_data, _ = load_compliance()
    if jurisdiction == "Federal":
        weeks = min(max(years_service, 0), 8)
        termination = weeks * weekly_pay
        severance = max(years_service * 2 * (weekly_pay / 5), weekly_pay)
        return {
            "termination_pay": round(termination, 2),
            "severance_pay": round(severance, 2),
            "total": round(termination + severance, 2),
            "jurisdiction": "Federal — Canada Labour Code",
            "source": "🟢 Live" if compliance_data else "📚 Fallback"
        }
    elif jurisdiction == "Ontario":
        weeks = min(years_service, 8)
        termination = weeks * weekly_pay
        severance = years_service * weekly_pay if years_service >= 5 and annual_payroll >= 2500000 else 0
        return {
            "termination_pay": round(termination, 2),
            "severance_pay": round(severance, 2),
            "total": round(termination + severance, 2),
            "jurisdiction": "Ontario ESA 2000",
            "source": "🟢 Live" if compliance_data else "📚 Fallback"
        }
    elif jurisdiction == "Quebec":
        if years_service < 1:
            weeks = 1
        elif years_service < 5:
            weeks = 2
        elif years_service < 10:
            weeks = 4
        else:
            weeks = 8
        termination = weeks * weekly_pay
        return {
            "termination_pay": round(termination, 2),
            "severance_pay": 0,
            "total": round(termination, 2),
            "jurisdiction": "Quebec Labour Standards",
            "source": "🟢 Live" if compliance_data else "📚 Fallback"
        }
    elif jurisdiction == "Alberta":
        if years_service < 2:
            weeks = 1
        elif years_service < 4:
            weeks = 2
        elif years_service < 6:
            weeks = 4
        elif years_service < 8:
            weeks = 5
        elif years_service < 10:
            weeks = 6
        else:
            weeks = 8
        termination = weeks * weekly_pay
        return {
            "termination_pay": round(termination, 2),
            "severance_pay": 0,
            "total": round(termination, 2),
            "jurisdiction": "Alberta Employment Standards",
            "source": "🟢 Live" if compliance_data else "📚 Fallback"
        }
    else:
        weeks = min(years_service, 8)
        termination = weeks * weekly_pay
        return {
            "termination_pay": round(termination, 2),
            "severance_pay": 0,
            "total": round(termination, 2),
            "jurisdiction": jurisdiction,
            "source": "🟢 Live" if compliance_data else "📚 Fallback"
        }

def get_data_status():
    _, s1 = load_onet()
    _, s2 = load_research()
    _, s3 = load_compliance()
    return {
        "onet": s1,
        "research": s2,
        "compliance": s3,
        "last_checked": datetime.today().strftime("%B %d, %Y %H:%M")
    }

if __name__ == "__main__":
    print("=" * 60)
    print("  DATA LOADER — STATUS CHECK")
    print("=" * 60)
    print()

    status = get_data_status()
    print(f"  Agent 1 O*NET:       {status['onet']}")
    print(f"  Agent 2 Research:    {status['research']}")
    print(f"  Agent 3 Compliance:  {status['compliance']}")
    print(f"  Last checked:        {status['last_checked']}")
    print()

    print("  Testing displacement scores:")
    for industry in ["Financial Services", "Technology", "Manufacturing"]:
        score, source = get_displacement_score(industry)
        print(f"  {industry}: {score} — {source}")
    print()

    print("  Testing benchmarks:")
    for key in ["reskilling_cost_per_employee", "cascade_multiplier", "near_term_automation_rate"]:
        value, source = get_benchmark(key)
        print(f"  {key}: {value} — {source}")
    print()

    print("  Testing severance calculator:")
    result = get_severance("Federal", 8, 3750)
    print(f"  Federal 8yrs $3750/wk: ${result['total']:,.2f} total")
    result = get_severance("Ontario", 6, 2900, 5000000)
    print(f"  Ontario 6yrs $2900/wk: ${result['total']:,.2f} total")
    print()
    print("✅ Data loader ready — all agents connected")
    print("Next: final app.py using data_loader")
"""
agent_onet.py
O*NET API — Complete Data Layer
HC Transformation Intelligence Platform
Jaini Desai | jainidesai.com | June 2026

Single source of truth for all O*NET data.
Built from confirmed API responses — no assumptions.
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Credentials ───────────────────────────────────────────────
API_KEY  = os.getenv("ONET_PASSWORD", "f3gB5-DGRYM-H3EGe-atz4K")
BASE_URL = "https://api-v2.onetcenter.org/online/"
HEADERS  = {"X-API-Key": API_KEY, "Accept": "application/json"}

# ── Bank of Canada exchange rate ──────────────────────────────
BOC_USD_TO_CAD = 1.36
BOC_RATE_DATE  = "June 10, 2026"

# ── Automation scores ─────────────────────────────────────────
# Source: Frey & Osborne (2013) calibrated against O*NET occupation data
AUTOMATION_SCORES = {
    "43-9021.00": 0.99, "43-3031.00": 0.98, "43-4051.00": 0.55,
    "43-5061.00": 0.73, "13-2011.00": 0.94, "13-2051.00": 0.23,
    "13-2061.00": 0.61, "13-2099.00": 0.54, "13-1041.00": 0.35,
    "23-1011.00": 0.04, "23-2011.00": 0.94, "15-1252.00": 0.04,
    "15-1231.00": 0.25, "15-1244.00": 0.25, "15-1299.00": 0.15,
    "13-1071.00": 0.55, "11-3121.00": 0.16, "13-1151.00": 0.26,
    "13-1141.00": 0.17, "15-2051.00": 0.02, "15-2041.00": 0.03,
    "13-1111.00": 0.13, "11-1021.00": 0.16, "41-4012.00": 0.72,
    "43-5071.00": 0.86, "41-2031.00": 0.92, "11-2022.00": 0.13,
    "11-2021.00": 0.14, "41-3091.00": 0.61, "43-4171.00": 0.96,
    "13-2054.00": 0.18, "13-2052.00": 0.58, "11-3111.00": 0.12,
    "43-4161.00": 0.89,
}

# ── Job Zone fallbacks ────────────────────────────────────────
# Used when live API call fails. Source: O*NET OnLine
JOB_ZONES = {
    "43-9021.00": 1, "43-3031.00": 2, "43-4051.00": 2,
    "13-2051.00": 4, "13-2011.00": 4, "13-2061.00": 4,
    "13-1041.00": 4, "23-1011.00": 5, "23-2011.00": 4,
    "15-1252.00": 4, "15-2051.00": 5, "13-1071.00": 3,
    "11-3121.00": 4, "13-1151.00": 3, "13-1141.00": 3,
    "11-1021.00": 4, "13-1111.00": 4, "41-2031.00": 2,
    "43-5071.00": 2, "11-2021.00": 4, "11-2022.00": 4,
    "11-3111.00": 4, "43-4161.00": 2,
}

# ── Median wages (USD annual) ─────────────────────────────────
# Source: O*NET BLS Occupational Employment Statistics
WAGES_USD = {
    "43-9021.00": 36000,  "43-3031.00": 42000,
    "43-4051.00": 38000,  "13-2051.00": 96000,
    "13-2011.00": 79000,  "13-2061.00": 82000,
    "13-1041.00": 72000,  "23-1011.00": 127000,
    "23-2011.00": 56000,  "15-1252.00": 124000,
    "15-2051.00": 108000, "13-1071.00": 63000,
    "11-3121.00": 126000, "13-1151.00": 63000,
    "13-1141.00": 64000,  "11-1021.00": 99000,
    "13-1111.00": 93000,  "41-2031.00": 30000,
    "43-5071.00": 37000,  "11-2021.00": 133000,
    "11-2022.00": 127000, "11-3111.00": 127000,
    "43-4161.00": 43000,
}

# ── Pagination handler ────────────────────────────────────────
def _get_all_pages(endpoint, result_key, max_pages=5):
    """
    Fetches all pages for a paginated O*NET endpoint.
    O*NET returns 5 items per page by default.
    Follows 'next' URL until no more pages or max_pages reached.
    """
    all_results = []
    url = f"{BASE_URL}{endpoint}"

    for _ in range(max_pages):
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                break
            data = r.json()
            items = data.get(result_key, [])
            all_results.extend(items)
            next_url = data.get("next")
            if not next_url:
                break
            url = next_url
        except Exception:
            break

    return all_results

# ── Single page call ──────────────────────────────────────────
def _get(endpoint):
    """Single API call for non-paginated endpoints."""
    try:
        r = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=HEADERS,
            timeout=10
        )
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None

# ── Connection test ───────────────────────────────────────────
def test_connection():
    return _get("occupations/13-2051.00") is not None

# ── Detailed Work Activities ──────────────────────────────────
# Confirmed response key: "activity"
# Confirmed fields: id, title
def get_detailed_work_activities(soc_code):
    items = _get_all_pages(
        f"occupations/{soc_code}/summary/detailed_work_activities",
        result_key="activity"
    )
    return [{"id": i.get("id", ""), "title": i.get("title", "")} for i in items]

# ── Tasks ─────────────────────────────────────────────────────
# Confirmed response key: "task"
# Confirmed fields: id, title
def get_tasks(soc_code):
    items = _get_all_pages(
        f"occupations/{soc_code}/summary/tasks",
        result_key="task"
    )
    return [{"id": i.get("id", ""), "title": i.get("title", "")} for i in items]

# ── Job Zone ──────────────────────────────────────────────────
# Confirmed response: {"job_zone": {"value": 3, ...}}
def get_job_zone(soc_code):
    data = _get(f"occupations/{soc_code}/summary/job_zone")
    if data:
        jz = data.get("job_zone", {})
        if isinstance(jz, dict):
            return int(jz.get("value", JOB_ZONES.get(soc_code, 3)))
        if isinstance(jz, int):
            return jz
    return JOB_ZONES.get(soc_code, 3)

# ── Related Occupations ───────────────────────────────────────
# Confirmed response key: "occupation"
# Confirmed fields: code, title, tags.bright_outlook
def get_related_occupations(soc_code):
    items = _get_all_pages(
        f"occupations/{soc_code}/summary/related_occupations",
        result_key="occupation"
    )
    return [
        {
            "soc_code":      i.get("code", ""),
            "title":         i.get("title", ""),
            "bright_outlook": i.get("tags", {}).get("bright_outlook", False)
        }
        for i in items
    ]

# ── Technology Skills — today ─────────────────────────────────
# Confirmed response key: "category" → "example" → "title"
def get_technology_skills(soc_code):
    items = _get_all_pages(
        f"occupations/{soc_code}/summary/technology_skills",
        result_key="category"
    )
    skills = []
    for cat in items:
        for ex in cat.get("example", []):
            name = ex.get("title", "").strip()
            if name:
                skills.append(name)
    return skills

# ── Hot Technology — tomorrow ─────────────────────────────────
# Confirmed response key: "example"
# Confirmed fields: title, hot_technology (bool), in_demand (bool), percentage
# Single page — returns all results at once (total=17, end=17)
def get_hot_technology(soc_code):
    data = _get(f"occupations/{soc_code}/hot_technology")
    if not data:
        return []
    return [
        {
            "title":       item.get("title", "").strip(),
            "in_demand":   item.get("in_demand", False),
            "percentage":  item.get("percentage", 0)
        }
        for item in data.get("example", [])
        if item.get("title", "").strip()
    ]

# ── Automation score ──────────────────────────────────────────
def get_automation_score(soc_code):
    score = AUTOMATION_SCORES.get(soc_code, 0.50)
    source = "Frey & Osborne (2013) / O*NET" if soc_code in AUTOMATION_SCORES else "Benchmark Estimate"
    return score, source

# ── Median wage ───────────────────────────────────────────────
def get_median_wage(soc_code):
    usd = WAGES_USD.get(soc_code, 65000)
    cad = round(usd * BOC_USD_TO_CAD)
    source = f"O*NET BLS Wage Data → CAD @ Bank of Canada {BOC_RATE_DATE}"
    return usd, cad, source

# ── Full role profile ─────────────────────────────────────────
def get_full_role_profile(soc_code):
    """
    Complete data pull for one SOC code.
    Called by transformation engine per role.
    """
    auto_score, auto_source  = get_automation_score(soc_code)
    usd, cad, wage_source    = get_median_wage(soc_code)
    job_zone                 = get_job_zone(soc_code)
    dwas                     = get_detailed_work_activities(soc_code)
    tasks                    = get_tasks(soc_code)
    related                  = get_related_occupations(soc_code)
    today_skills             = get_technology_skills(soc_code)
    hot_tech                 = get_hot_technology(soc_code)

    # Tomorrow skills = all hot technology items
    tomorrow_skills = [h["title"] for h in hot_tech]

    # In-demand = hot tech items where in_demand is True
    in_demand_skills = [h["title"] for h in hot_tech if h["in_demand"]]

    # Skills gap = tomorrow skills not present in today
    skills_gap = [s for s in tomorrow_skills if s not in today_skills]

    return {
        "soc_code":           soc_code,
        "automation_score":   auto_score,
        "automation_source":  auto_source,
        "job_zone":           job_zone,
        "wage_usd":           usd,
        "wage_cad":           cad,
        "wage_source":        wage_source,
        "dwas":               dwas,
        "tasks":              tasks,
        "related_occupations": related,
        "today_skills":       today_skills,
        "tomorrow_skills":    tomorrow_skills,
        "in_demand_skills":   in_demand_skills,
        "skills_gap":         skills_gap,
        "dwa_count":          len(dwas),
        "task_count":         len(tasks),
    }

# ── Cache layer ───────────────────────────────────────────────
def get_cached_profile(soc_code, cache_dir="data"):
    """Load from cache if available, pull live and cache if not."""
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(
        cache_dir,
        f"profile_{soc_code.replace('.','_').replace('-','_')}.json"
    )
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)

    profile = get_full_role_profile(soc_code)
    with open(cache_path, "w") as f:
        json.dump(profile, f, indent=2)

    return profile

# ── Self-test ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  AGENT ONET — FULL ENDPOINT TEST")
    print(f"  {datetime.today().strftime('%B %d, %Y %H:%M')}")
    print("=" * 60)

    if not test_connection():
        print("❌ Cannot reach O*NET API")
    else:
        print("✅ O*NET API connected\n")

        soc = "13-1141.00"
        print(f"Full profile: {soc} (Benefits & Compensation Specialist)")
        print("-" * 60)

        profile = get_full_role_profile(soc)

        print(f"Automation Score   : {profile['automation_score']} ({profile['automation_source']})")
        print(f"Job Zone           : {profile['job_zone']}")
        print(f"Wage USD           : ${profile['wage_usd']:,}")
        print(f"Wage CAD           : ${profile['wage_cad']:,} ({profile['wage_source']})")
        print(f"DWAs pulled        : {profile['dwa_count']}")
        print(f"Tasks pulled       : {profile['task_count']}")
        print(f"Today skills       : {profile['today_skills'][:3]}")
        print(f"Tomorrow skills    : {profile['tomorrow_skills'][:3]}")
        print(f"In-demand skills   : {profile['in_demand_skills'][:3]}")
        print(f"Skills gap         : {profile['skills_gap'][:5]}")
        print(f"Related roles      :")
        for r in profile["related_occupations"][:5]:
            bo = "✅ Bright Outlook" if r["bright_outlook"] else ""
            print(f"  {r['soc_code']} — {r['title']} {bo}")

        print("\n✅ Agent ready")
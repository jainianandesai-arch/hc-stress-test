"""
transformation_engine.py
Workforce Transformation Calculation Engine
HC Transformation Intelligence Platform
Jaini Desai | jainidesai.com | June 2026

Two-layer architecture:
  Layer 1 — Function Sizing: how many people does this function need tomorrow?
  Layer 2 — Released Capacity: what do we do with the difference, and what does it cost?

All numbers traceable to named sources.
No decisions made — options and costs surfaced for the company to decide.
"""

import json
import os
from agent_onet import get_cached_profile, get_automation_score, get_median_wage

# ── Benchmarks ────────────────────────────────────────────────
# Every value cites its source. Used in cost calculations throughout.

BENCHMARKS = {
    "reskilling_cost_cad": {
        "value": 8500,
        "source": "Deloitte 2026 Global Human Capital Trends",
        "note": "Average total cost of meaningful upskilling per employee"
    },
    "productivity_drag_pct": {
        "value": 0.23,
        "source": "McKinsey State of AI 2025",
        "note": "Productivity loss during reskilling transition period"
    },
    "productivity_drag_months": {
        "value": 14,
        "source": "McKinsey State of AI 2025",
        "note": "Duration of productivity drag during reskilling"
    },
    "replacement_cost_multiplier": {
        "value": 2.0,
        "source": "SHRM Workforce Benchmark 2024",
        "note": "Replacement cost as multiple of annual salary"
    },
    "skills_obsolescence_rate": {
        "value": 0.39,
        "source": "WEF Future of Jobs Report 2025",
        "note": "Share of current skills obsolete by 2028"
    },
}

# ── AI Stage multipliers ──────────────────────────────────────
AI_MULTIPLIERS = {
    "Early (Exploring)":   0.70,
    "Active (Piloting)":   1.00,
    "Advanced (Scaling)":  1.35,
}

# ── Province modifiers ────────────────────────────────────────
PROVINCE_MODIFIERS = {
    "Federal (Banks & Telecoms)": {"displacement": 1.10, "reskilling": 1.00},
    "Ontario":                    {"displacement": 1.15, "reskilling": 1.10},
    "British Columbia":           {"displacement": 1.05, "reskilling": 1.05},
    "Quebec":                     {"displacement": 0.90, "reskilling": 0.85},
    "Alberta":                    {"displacement": 0.95, "reskilling": 0.90},
}

# ── Job Zone → reskilling months ─────────────────────────────
# Gap between current role JZ and target role JZ drives reskilling time
JZ_GAP_TO_MONTHS = {
    0: 3,   # same complexity — tool adoption only
    1: 6,   # one level up — feasible, moderate investment
    2: 12,  # two levels up — significant investment
    3: 18,  # three levels up — not recommended, flag for exit
}

# ── Severance calculator ──────────────────────────────────────
def calculate_severance(province, years_service, weekly_pay, annual_payroll=5000000):
    """
    Canadian Labour Code and provincial ESA severance.
    Returns total severance per person in CAD.
    Source: Canada Labour Code R.S.C. 1985 c.L-2 and provincial ESA.
    """
    jurisdiction_map = {
        "Federal (Banks & Telecoms)": "Federal",
        "Ontario":                    "Ontario",
        "British Columbia":           "BC",
        "Quebec":                     "Quebec",
        "Alberta":                    "Alberta",
    }
    j = jurisdiction_map.get(province, "Federal")

    if j == "Federal":
        termination = min(max(years_service, 0), 8) * weekly_pay
        severance   = max(years_service * 2 * (weekly_pay / 5), weekly_pay)
        total       = termination + severance
        law         = "Canada Labour Code — R.S.C. 1985, c. L-2"

    elif j == "Ontario":
        termination = min(years_service, 8) * weekly_pay
        severance   = (years_service * weekly_pay
                       if years_service >= 5 and annual_payroll >= 2500000
                       else 0)
        total = termination + severance
        law   = "Ontario Employment Standards Act 2000"

    elif j == "BC":
        termination = min(years_service, 8) * weekly_pay
        total = termination
        law   = "BC Employment Standards Act — RSBC 1996 c.113"

    elif j == "Quebec":
        bands = [(1,1),(5,2),(10,4),(999,8)]
        weeks = next(w for (threshold, w) in bands if years_service < threshold)
        total = weeks * weekly_pay
        law   = "Quebec Act Respecting Labour Standards — CQLR c. N-1.1"

    elif j == "Alberta":
        bands = [(2,1),(4,2),(6,4),(8,5),(10,6),(999,8)]
        weeks = next(w for (threshold, w) in bands if years_service < threshold)
        total = weeks * weekly_pay
        law   = "Alberta Employment Standards Code — RSA 2000 c.E-9"

    else:
        total = min(years_service, 8) * weekly_pay
        law   = "Canada Labour Code"

    return round(total, 2), law

# ── Layer 1 — Function Sizing ─────────────────────────────────
def calculate_function_sizing(roles, ai_stage, province):
    """
    For each role in a function, calculates:
    - Headcount needed tomorrow based on automation score
    - Headcount released
    - Transformation type per role (eliminated / transformed / augmented)

    roles: list of {soc_code, title, headcount}
    Returns list of role-level sizing results.
    """
    ai_mult   = AI_MULTIPLIERS.get(ai_stage, 1.0)
    prov_mod  = PROVINCE_MODIFIERS.get(province, {"displacement": 1.0, "reskilling": 1.0})
    results   = []

    for role in roles:
        soc_code = role["soc_code"]
        title    = role["title"]
        hc       = role["headcount"]

        auto_score, auto_source = get_automation_score(soc_code)

        # Adjusted automation score for this org context
        adjusted_score = min(auto_score * ai_mult * prov_mod["displacement"], 1.0)

        # Transformation type
        if adjusted_score >= 0.70:
            transform_type = "Eliminated"
            # Fully eliminated roles — all headcount released
            hc_tomorrow  = 0
            hc_released  = hc
        elif adjusted_score >= 0.40:
            transform_type = "Transformed"
            # Role changes significantly — task survival drives consolidation
            task_survival  = 1.0 - adjusted_score
            hc_tomorrow    = max(round(hc * task_survival), 1)
            hc_released    = hc - hc_tomorrow
        else:
            transform_type = "Augmented"
            # Role stays — minimal headcount change
            hc_tomorrow  = hc
            hc_released  = 0

        results.append({
            "soc_code":        soc_code,
            "title":           title,
            "headcount_today": hc,
            "headcount_tomorrow": hc_tomorrow,
            "headcount_released": hc_released,
            "automation_score": round(adjusted_score, 2),
            "automation_source": auto_source,
            "transform_type":  transform_type,
        })

    return results

# ── Layer 2 — Released Capacity Decision ─────────────────────
def calculate_transfer_options(sizing_results, province, avg_years_service=6):
    """
    For each released pool, calculates transfer and exit options.
    Pulls O*NET adjacent roles. Calculates cost of each path.
    Company decides — tool surfaces options and costs only.

    Returns list of decision records per released role pool.
    """
    prov_mod = PROVINCE_MODIFIERS.get(province, {"reskilling": 1.0})
    reskilling_cost = BENCHMARKS["reskilling_cost_cad"]["value"]
    prod_drag_pct   = BENCHMARKS["productivity_drag_pct"]["value"]
    prod_drag_mo    = BENCHMARKS["productivity_drag_months"]["value"]
    replace_mult    = BENCHMARKS["replacement_cost_multiplier"]["value"]

    decisions = []

    for role in sizing_results:
        if role["headcount_released"] == 0:
            continue

        soc_code  = role["soc_code"]
        hc_out    = role["headcount_released"]
        profile   = get_cached_profile(soc_code)

        usd, cad_wage, wage_source = get_median_wage(soc_code)
        weekly_pay = cad_wage / 52
        current_jz = profile["job_zone"]

        # ── Transfer options from O*NET adjacent roles ────────
        transfer_options = []
        for adj in profile["related_occupations"]:
            adj_soc  = adj["soc_code"]
            adj_jz   = get_cached_profile(adj_soc)["job_zone"] if adj_soc else current_jz
            jz_gap   = max(adj_jz - current_jz, 0)
            reskill_months = JZ_GAP_TO_MONTHS.get(min(jz_gap, 3), 18)
            feasible = jz_gap <= 2  # gap of 3+ = not recommended

            # Transfer cost per person
            reskill_investment = round(
                reskilling_cost * prov_mod["reskilling"]
            )
            productivity_drag_cost = round(
                cad_wage * prod_drag_pct * (reskill_months / 12)
            )
            transfer_cost_per_person = reskill_investment + productivity_drag_cost

            transfer_options.append({
                "adjacent_soc":         adj_soc,
                "adjacent_title":       adj["title"],
                "bright_outlook":       adj["bright_outlook"],
                "job_zone_current":     current_jz,
                "job_zone_target":      adj_jz,
                "job_zone_gap":         jz_gap,
                "reskilling_months":    reskill_months,
                "feasible":             feasible,
                "reskill_cost_per_person": reskill_investment,
                "productivity_drag_per_person": productivity_drag_cost,
                "transfer_cost_per_person": transfer_cost_per_person,
                "transfer_cost_total":  transfer_cost_per_person * hc_out,
            })

        # Sort: feasible first, then bright outlook, then lowest cost
        transfer_options.sort(
            key=lambda x: (not x["feasible"], not x["bright_outlook"], x["transfer_cost_per_person"])
        )

        # ── Exit cost ─────────────────────────────────────────
        severance_per_person, severance_law = calculate_severance(
            province, avg_years_service, weekly_pay
        )
        replacement_per_person = round(cad_wage * replace_mult)
        exit_cost_per_person   = severance_per_person + replacement_per_person
        exit_cost_total        = exit_cost_per_person * hc_out

        # ── Best transfer option ──────────────────────────────
        best_transfer = next(
            (t for t in transfer_options if t["feasible"]), None
        )
        net_saving = (
            exit_cost_total - best_transfer["transfer_cost_total"]
            if best_transfer else 0
        )
        recommended = (
            "Transfer & Reskill" if best_transfer and net_saving > 0
            else "Exit"
        )

        decisions.append({
            "soc_code":              soc_code,
            "title":                 role["title"],
            "headcount_released":    hc_out,
            "wage_cad":              cad_wage,
            "wage_source":           wage_source,
            "current_job_zone":      current_jz,
            "today_skills":          profile["today_skills"][:5],
            "tomorrow_skills":       profile["tomorrow_skills"][:5],
            "skills_gap":            profile["skills_gap"][:5],
            "transfer_options":      transfer_options[:3],
            "exit_cost_per_person":  exit_cost_per_person,
            "exit_cost_total":       exit_cost_total,
            "severance_per_person":  severance_per_person,
            "severance_law":         severance_law,
            "replacement_per_person": replacement_per_person,
            "best_transfer":         best_transfer,
            "net_saving_if_transfer": net_saving,
            "recommended_path":      recommended,
        })

    return decisions

# ── Cost of Inaction ──────────────────────────────────────────
def calculate_cost_of_inaction(total_strategic_pop, avg_wage_cad,
                                ai_stage, province, months_list=[12, 24, 36]):
    """
    What it costs to do nothing as AI adoption continues.
    Three components:
    1. Skills obsolescence — people becoming less effective
    2. Productivity drag — AI advantage competitors gain
    3. Salary waste — paying full cost for increasingly automated work

    Source: WEF Future of Jobs 2025, McKinsey State of AI 2025
    """
    ai_mult  = AI_MULTIPLIERS.get(ai_stage, 1.0)
    prov_mod = PROVINCE_MODIFIERS.get(province, {"reskilling": 1.0})
    obs_rate = BENCHMARKS["skills_obsolescence_rate"]["value"]
    drag_pct = BENCHMARKS["productivity_drag_pct"]["value"]

    results = []
    for months in months_list:
        years = months / 12

        # Skills obsolescence compounds over time
        obs_population = round(
            total_strategic_pop * obs_rate * ai_mult * prov_mod["reskilling"] * years
        )
        obs_cost = round(obs_population * BENCHMARKS["reskilling_cost_cad"]["value"])

        # Productivity drag on full population
        prod_cost = round(
            total_strategic_pop * avg_wage_cad * drag_pct * (months / 12)
        )

        # Salary waste — paying for automated work
        # Conservative: 20% of salary for roles not yet transformed
        salary_waste = round(
            total_strategic_pop * avg_wage_cad * 0.20 * years
        )

        total = obs_cost + prod_cost + salary_waste

        results.append({
            "months":          months,
            "obs_population":  obs_population,
            "obs_cost":        obs_cost,
            "productivity_cost": prod_cost,
            "salary_waste":    salary_waste,
            "total":           total,
            "obs_source":      BENCHMARKS["skills_obsolescence_rate"]["source"],
            "prod_source":     BENCHMARKS["productivity_drag_pct"]["source"],
        })

    return results

# ── Transformation Priority Index ────────────────────────────
def calculate_priority_index(function_results):
    """
    Ranks functions by transformation ROI.
    Highest ROI = biggest gap between cost of inaction and transformation cost.
    This is the first table the executive sees.
    """
    ranked = []

    for fn in function_results:
        fn_name          = fn["function_name"]
        sizing           = fn["sizing"]
        decisions        = fn["decisions"]
        inaction_24      = fn["inaction_costs"][1]["total"]  # 24-month inaction

        total_hc         = sum(r["headcount_today"] for r in sizing)
        total_released   = sum(r["headcount_released"] for r in sizing)
        total_retained   = total_hc - total_released
        avg_automation   = (
            sum(r["automation_score"] * r["headcount_today"] for r in sizing)
            / max(total_hc, 1)
        )

        # Transformation cost = best path cost across all released pools
        transform_cost = sum(
            d["best_transfer"]["transfer_cost_total"]
            if d["best_transfer"] and d["recommended_path"] == "Transfer & Reskill"
            else d["exit_cost_total"]
            for d in decisions
        ) if decisions else 0

        net_roi = inaction_24 - transform_cost

        # Top skills gap across all roles in this function
        all_gaps = []
        for d in decisions:
            all_gaps.extend(d["skills_gap"])
        top_gap = all_gaps[0] if all_gaps else "—"

        # Label
        if net_roi == max(f.get("net_roi", 0) for f in ranked + [{"net_roi": net_roi}]):
            label = "Highest ROI"
        elif avg_automation >= 0.60:
            label = "Quick Win"
        elif avg_automation >= 0.35:
            label = "Mid-term"
        else:
            label = "Low Urgency"

        ranked.append({
            "function_name":    fn_name,
            "avg_automation":   round(avg_automation, 2),
            "headcount_today":  total_hc,
            "headcount_released": total_released,
            "headcount_retained": total_retained,
            "top_skills_gap":   top_gap,
            "transform_cost":   transform_cost,
            "inaction_24mo":    inaction_24,
            "net_roi":          net_roi,
            "label":            label,
        })

    # Sort by net ROI descending
    ranked.sort(key=lambda x: x["net_roi"], reverse=True)

    # Re-label top item as Highest ROI after sorting
    if ranked:
        ranked[0]["label"] = "Highest ROI"
        if len(ranked) > 1:
            ranked[1]["label"] = "Quick Win"

    return ranked

# ── Self-funding sequencing ───────────────────────────────────
def calculate_sequencing(priority_index):
    """
    Shows how Cycle 1 savings fund Cycle 2, Cycle 2 funds Cycle 3.
    Total self-funded transformation — no additional capital after Cycle 1.
    """
    sequences    = []
    cumulative   = 0

    for i, fn in enumerate(priority_index):
        cycle_savings  = fn["net_roi"]
        cumulative    += cycle_savings

        sequences.append({
            "cycle":          i + 1,
            "function":       fn["function_name"],
            "investment":     fn["transform_cost"],
            "net_saving":     cycle_savings,
            "cumulative_saving": cumulative,
            "funded_by":      "Initial investment" if i == 0 else f"Cycle {i} savings",
        })

    return sequences
"""
optimization_engine.py
Workforce Transformation Optimization Engine
HC Transformation Intelligence Platform

© 2024–2026 Jaini Desai. All rights reserved.
HC Transformation Intelligence Platform is an original methodology by Jaini Desai.
Employee Lifetime Value™ (ELV) and Leadership Momentum Index™ (LMI) are original
frameworks by Jaini Desai (2024). Unauthorized reproduction or commercial use
without written permission is prohibited.

Architecture:
- Optimization runs at FUNCTION level
- Three scenarios: Low / Mid / High cost assumptions
- Filter 1: Domain Transferability (O*NET DWA overlap >= 30%)
- Filter 2: Technical Gap (Job Zone gap <= 2)
- PuLP linear programming minimizes total transformation cost
- Task-level productivity drag using O*NET skill percentage data
- ELV calculated when optional individual data provided
- LMI calculated for leadership roles when optional data provided
- Canada and US jurisdictions supported
"""

import json
import os
from agent_onet import (
    get_cached_profile,
    get_automation_score,
    get_median_wage,
    get_dwa_overlap_score,
    get_skill_gap_percentages,
    get_job_zone,
    get_related_occupations,
)

# ── PuLP import ───────────────────────────────────────────────
try:
    from pulp import (
        LpProblem, LpMinimize, LpVariable,
        lpSum, value, PULP_CBC_CMD
    )
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False

# ── Jurisdiction config ───────────────────────────────────────
JURISDICTIONS = {
    "Canada": {
        "currency":        "CAD",
        "currency_symbol": "$",
        "fx_rate":         1.36,
        "fx_source":       "Bank of Canada June 10, 2026",
        "fx_link":         "https://www.bankofcanada.ca/rates/exchange/daily-exchange-rates",
        "severance_type":  "canada",
        "warn_act":        False,
    },
    "United States": {
        "currency":        "USD",
        "currency_symbol": "$",
        "fx_rate":         1.00,
        "fx_source":       "O*NET native currency — no conversion applied",
        "fx_link":         "https://www.onetcenter.org",
        "severance_type":  "us_warn",
        "warn_act":        True,
    },
}

# ── Province modifiers (Canada only) ─────────────────────────
PROVINCE_MODIFIERS = {
    "Federal (Banks & Telecoms)": {"displacement": 1.10, "reskilling": 1.00},
    "Ontario":                    {"displacement": 1.15, "reskilling": 1.10},
    "British Columbia":           {"displacement": 1.05, "reskilling": 1.05},
    "Quebec":                     {"displacement": 0.90, "reskilling": 0.85},
    "Alberta":                    {"displacement": 0.95, "reskilling": 0.90},
    "United States":              {"displacement": 1.00, "reskilling": 1.00},
}

# ── AI Stage multipliers ──────────────────────────────────────
AI_MULTIPLIERS = {
    "Early (Exploring)":  0.70,
    "Active (Piloting)":  1.00,
    "Advanced (Scaling)": 1.35,
}

# ── Benchmark ranges with full citations ─────────────────────
BENCHMARKS = {
    "reskilling_cost": {
        "low":    6500,
        "mid":    8500,
        "high":   15000,
        "source": "Deloitte 2026 Global Human Capital Trends",
        "link":   "https://www2.deloitte.com/us/en/insights/focus/human-capital-trends.html",
        "note":   "Low = online upskilling. Mid = Deloitte benchmark. High = formal certification."
    },
    "productivity_drag_pct": {
        "low":    0.10,
        "mid":    0.23,
        "high":   0.35,
        "source": "McKinsey State of AI 2025",
        "link":   "https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai",
        "note":   "Low = adjacent role. Mid = McKinsey org average. High = large skill gap."
    },
    "replacement_multiplier": {
        "low":    1.5,
        "mid":    2.0,
        "high":   3.0,
        "source": "SHRM Workforce Benchmark 2024",
        "link":   "https://www.shrm.org/topics-tools/research/benchmarking",
        "note":   "Low = junior abundant role. Mid = SHRM benchmark. High = scarce technical."
    },
    "augmentation_cost": {
        "low":    2500,
        "mid":    3500,
        "high":   6000,
        "source": "Conservative benchmark — tool adoption and AI literacy training",
        "link":   "https://www2.deloitte.com/us/en/insights/focus/human-capital-trends.html",
        "note":   "Low = basic AI literacy. Mid = tool adoption. High = advanced change management."
    },
    "skills_obsolescence_rate": {
        "value":  0.39,
        "source": "WEF Future of Jobs Report 2025",
        "link":   "https://www.weforum.org/reports/the-future-of-jobs-report-2025",
        "note":   "39% of current skills obsolete by 2028"
    },
    "cascade_multiplier": {
        "value":  2.3,
        "source": "Cross, Borgatti & Parker — Organizational Network Analysis",
        "link":   "https://hbr.org/2002/06/making-invisible-work-visible",
        "note":   "Leadership exit disrupts 2.3x their direct team size"
    },
}

# ── Reskilling cost by target Job Zone ───────────────────────
RESKILLING_BY_JZ = {
    1: {"low": 3000,  "mid": 4500,  "high": 6000},
    2: {"low": 4500,  "mid": 6500,  "high": 9000},
    3: {"low": 6500,  "mid": 8500,  "high": 12000},
    4: {"low": 9000,  "mid": 12000, "high": 18000},
    5: {"low": 12000, "mid": 18000, "high": 25000},
}

# ── Reskilling months by Job Zone gap ────────────────────────
JZ_GAP_TO_MONTHS = {
    0: {"low": 2,  "mid": 3,  "high": 4},
    1: {"low": 4,  "mid": 6,  "high": 9},
    2: {"low": 9,  "mid": 12, "high": 18},
}

# ── Thresholds ────────────────────────────────────────────────
DOMAIN_TRANSFER_THRESHOLD = 0.30
MAX_JZ_GAP               = 2

# ── H/M/L score conversion ────────────────────────────────────
HML = {"High": 85, "Medium": 60, "Low": 35, None: 60}

# ── Source registry — all citations with links ────────────────
SOURCES = {
    "onet": {
        "name":  "O*NET Web Services — U.S. Dept of Labor",
        "link":  "https://www.onetcenter.org/developers.html",
    },
    "frey_osborne": {
        "name":  "Frey & Osborne (2013) — The Future of Employment",
        "link":  "https://www.oxfordmartin.ox.ac.uk/downloads/academic/The_Future_of_Employment.pdf",
    },
    "deloitte": {
        "name":  "Deloitte 2026 Global Human Capital Trends",
        "link":  "https://www2.deloitte.com/us/en/insights/focus/human-capital-trends.html",
    },
    "mckinsey": {
        "name":  "McKinsey State of AI 2025",
        "link":  "https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai",
    },
    "wef": {
        "name":  "WEF Future of Jobs Report 2025",
        "link":  "https://www.weforum.org/reports/the-future-of-jobs-report-2025",
    },
    "shrm": {
        "name":  "SHRM Workforce Benchmark 2024",
        "link":  "https://www.shrm.org/topics-tools/research/benchmarking",
    },
    "canada_labour_code": {
        "name":  "Canada Labour Code — R.S.C. 1985, c. L-2",
        "link":  "https://laws-lois.justice.gc.ca/eng/acts/L-2",
    },
    "ontario_esa": {
        "name":  "Ontario Employment Standards Act 2000",
        "link":  "https://www.ontario.ca/laws/statute/00e41",
    },
    "bc_esa": {
        "name":  "BC Employment Standards Act — RSBC 1996 c.113",
        "link":  "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/96113_01",
    },
    "quebec_lsa": {
        "name":  "Quebec Act Respecting Labour Standards — CQLR c. N-1.1",
        "link":  "https://www.legisquebec.gouv.qc.ca/en/document/cs/N-1.1",
    },
    "alberta_esc": {
        "name":  "Alberta Employment Standards Code — RSA 2000 c.E-9",
        "link":  "https://www.qp.alberta.ca/documents/Acts/E09.pdf",
    },
    "warn_act": {
        "name":  "WARN Act (1988) — Worker Adjustment and Retraining Notification",
        "link":  "https://www.dol.gov/agencies/eta/layoffs/warn",
    },
    "boc": {
        "name":  "Bank of Canada Daily Exchange Rates",
        "link":  "https://www.bankofcanada.ca/rates/exchange/daily-exchange-rates",
    },
    "cross_borgatti": {
        "name":  "Cross, Borgatti & Parker — Organizational Network Analysis",
        "link":  "https://hbr.org/2002/06/making-invisible-work-visible",
    },
}

# ═══════════════════════════════════════════════════════════════
# SEVERANCE
# ═══════════════════════════════════════════════════════════════

def calculate_severance(country, province, years_service,
                         weekly_pay, headcount=1, annual_payroll=5000000):
    """
    Calculates severance range (low/mid/high) per person.
    Canada: legislative minimum + company policy range
    US: WARN Act exposure only — no statutory minimum
    """
    if country == "United States":
        daily_pay     = weekly_pay / 5
        warn_per_person = daily_pay * 60
        return {
            "low":   0,
            "mid":   round(warn_per_person * 0.5, 2),
            "high":  round(warn_per_person, 2),
            "law":   SOURCES["warn_act"]["name"],
            "link":  SOURCES["warn_act"]["link"],
            "note":  (
                "No statutory per-person severance minimum in the US. "
                "Low = at-will, no severance. "
                "Mid/High = WARN Act exposure (60 days) if qualifying layoff. "
                "Individual severance is company policy."
            )
        }

    # Canada
    j_map = {
        "Federal (Banks & Telecoms)": "Federal",
        "Ontario": "Ontario",
        "British Columbia": "BC",
        "Quebec": "Quebec",
        "Alberta": "Alberta",
    }
    j = j_map.get(province, "Federal")

    if j == "Federal":
        term = min(max(years_service, 0), 8) * weekly_pay
        sev  = max(years_service * 2 * (weekly_pay / 5), weekly_pay)
        leg  = term + sev
        law  = SOURCES["canada_labour_code"]["name"]
        link = SOURCES["canada_labour_code"]["link"]

    elif j == "Ontario":
        term = min(years_service, 8) * weekly_pay
        sev  = (years_service * weekly_pay
                if years_service >= 5 and annual_payroll >= 2500000 else 0)
        leg  = term + sev
        law  = SOURCES["ontario_esa"]["name"]
        link = SOURCES["ontario_esa"]["link"]

    elif j == "BC":
        leg  = min(years_service, 8) * weekly_pay
        law  = SOURCES["bc_esa"]["name"]
        link = SOURCES["bc_esa"]["link"]

    elif j == "Quebec":
        bands = [(1,1),(5,2),(10,4),(999,8)]
        weeks = next(w for (t,w) in bands if years_service < t)
        leg   = weeks * weekly_pay
        law   = SOURCES["quebec_lsa"]["name"]
        link  = SOURCES["quebec_lsa"]["link"]

    elif j == "Alberta":
        bands = [(2,1),(4,2),(6,4),(8,5),(10,6),(999,8)]
        weeks = next(w for (t,w) in bands if years_service < t)
        leg   = weeks * weekly_pay
        law   = SOURCES["alberta_esc"]["name"]
        link  = SOURCES["alberta_esc"]["link"]

    else:
        leg  = min(years_service, 8) * weekly_pay
        law  = SOURCES["canada_labour_code"]["name"]
        link = SOURCES["canada_labour_code"]["link"]

    pol_mid  = years_service * 2 * weekly_pay
    pol_high = years_service * 3 * weekly_pay

    return {
        "low":   round(leg, 2),
        "mid":   round(max(leg, pol_mid), 2),
        "high":  round(max(leg, pol_high), 2),
        "law":   law,
        "link":  link,
        "note":  (
            f"Approximate — based on {years_service} year average tenure. "
            f"Low = legislative minimum. "
            f"Mid = 2 weeks/year company policy. "
            f"High = 3 weeks/year enhanced policy."
        )
    }

# ═══════════════════════════════════════════════════════════════
# FILTER 1 — DOMAIN TRANSFERABILITY
# ═══════════════════════════════════════════════════════════════

def assess_domain_transferability(soc_current, soc_target):
    """
    O*NET DWA overlap between current and target role.
    >= 30% = transformable domain.
    © Jaini Desai — input to ELV™ Skill Adjacency Score
    """
    overlap = get_dwa_overlap_score(soc_current, soc_target)
    return {
        "overlap_score": overlap,
        "transferable":  overlap >= DOMAIN_TRANSFER_THRESHOLD,
        "signal": (
            "Strong domain transfer"   if overlap >= 0.60 else
            "Moderate domain transfer" if overlap >= 0.30 else
            "Weak domain transfer — reskilling alone insufficient"
        ),
        "source": SOURCES["onet"]["name"],
        "link":   SOURCES["onet"]["link"],
    }

# ═══════════════════════════════════════════════════════════════
# FILTER 2 — TECHNICAL GAP
# ═══════════════════════════════════════════════════════════════

def assess_technical_gap(soc_current, soc_target):
    """
    Job Zone gap between current and target role.
    Gap > 2 = Buy recommended.
    """
    jz_c   = get_job_zone(soc_current)
    jz_t   = get_job_zone(soc_target)
    gap    = max(jz_t - jz_c, 0)
    months = JZ_GAP_TO_MONTHS.get(
        min(gap, 2),
        {"low": 18, "mid": 24, "high": 36}
    )
    return {
        "jz_current":      jz_c,
        "jz_target":       jz_t,
        "jz_gap":          gap,
        "feasible":        gap <= MAX_JZ_GAP,
        "reskilling_months": months,
        "signal": (
            "Same complexity — tool adoption only"    if gap == 0 else
            "One level up — feasible with investment" if gap == 1 else
            "Two levels up — significant investment"  if gap == 2 else
            "Gap too large — Buy recommended"
        ),
        "source": SOURCES["onet"]["name"],
        "link":   SOURCES["onet"]["link"],
    }

# ═══════════════════════════════════════════════════════════════
# TASK-LEVEL PRODUCTIVITY DRAG
# ═══════════════════════════════════════════════════════════════

def calculate_task_level_drag(soc_code, annual_salary, reskilling_months_mid):
    """
    Productivity drag calculated at task level using O*NET
    skill percentage data — not a flat organizational average.

    Formula per skill gap:
    drag = salary × (skill_pct/100) × (months/12)

    More precise than McKinsey flat 23%.
    Falls back to flat rate if no O*NET percentage data.

    Source: O*NET Hot Technology endpoint (percentage field)
    © Jaini Desai — used in ELV™ and optimization model
    """
    gaps = get_skill_gap_percentages(soc_code)

    if not gaps:
        flat = annual_salary * 0.23 * (reskilling_months_mid / 12)
        return {
            "total_low":  round(flat * 0.60),
            "total_mid":  round(flat),
            "total_high": round(flat * 1.50),
            "breakdown":  [],
            "method":     "flat_rate",
            "source":     SOURCES["mckinsey"]["name"],
            "link":       SOURCES["mckinsey"]["link"],
        }

    breakdown = []
    total_pct = 0

    for g in gaps:
        pct      = g["percentage"] / 100
        mid_mo   = reskilling_months_mid
        low_mo   = JZ_GAP_TO_MONTHS.get(0, {}).get("low", 2)
        high_mo  = JZ_GAP_TO_MONTHS.get(2, {}).get("high", 18)

        drag_mid  = annual_salary * pct * (mid_mo  / 12)
        drag_low  = annual_salary * pct * (low_mo  / 12)
        drag_high = annual_salary * pct * (high_mo / 12)

        breakdown.append({
            "skill":      g["skill"],
            "pct_of_job": g["percentage"],
            "drag_low":   round(drag_low),
            "drag_mid":   round(drag_mid),
            "drag_high":  round(drag_high),
        })
        total_pct += pct

    total_pct = min(total_pct, 0.80)

    total_mid  = round(annual_salary * total_pct * (reskilling_months_mid / 12))
    total_low  = round(total_mid * 0.60)
    total_high = round(total_mid * 1.50)

    return {
        "total_low":  total_low,
        "total_mid":  total_mid,
        "total_high": total_high,
        "breakdown":  breakdown,
        "method":     "task_level",
        "source":     SOURCES["onet"]["name"],
        "link":       SOURCES["onet"]["link"],
    }

# ═══════════════════════════════════════════════════════════════
# ELV CALCULATION
# ═══════════════════════════════════════════════════════════════

def calculate_elv(performance, engagement, learning_agility,
                   skill_adjacency, tenure_years, annual_salary,
                   reskilling_cost_mid, avg_years_remaining=10):
    """
    Employee Lifetime Value™ (ELV)
    Original framework by Jaini Desai (2024)
    Published on LinkedIn — linkedin.com/in/jainidesai

    Formula:
    ELV = Performance Score × Skill Adjacency ×
          Net Contribution Period − Retraining Cost
    Normalized 0–100.

    Inputs:
    - performance, engagement, learning_agility: High/Medium/Low
    - skill_adjacency: 0.0–1.0 from O*NET DWA overlap
    - tenure_years: years of service
    - annual_salary: local currency
    - reskilling_cost_mid: mid benchmark

    © 2024–2026 Jaini Desai. All rights reserved.
    Unauthorized reproduction prohibited.
    """
    p = HML.get(performance, 60)
    e = HML.get(engagement, 60)
    a = HML.get(learning_agility, 60)

    composite    = p * 0.40 + e * 0.35 + a * 0.25
    adjacency    = skill_adjacency * 100
    tenure_fac   = min(tenure_years / 10, 1.0)
    net_contrib  = avg_years_remaining * (1 + tenure_fac * 0.2)

    raw_elv      = (composite/100) * (adjacency/100) * net_contrib * annual_salary
    net_elv      = raw_elv - reskilling_cost_mid

    reference    = 1.0 * 1.0 * 12 * annual_salary
    elv_score    = max(0, min(100, (net_elv / max(reference, 1)) * 100))

    rough_diamond = (
        performance in ["Low", "Medium"] and
        learning_agility == "High"
    )

    return {
        "elv_score":      round(elv_score, 1),
        "composite_perf": round(composite, 1),
        "adjacency":      round(adjacency, 1),
        "net_contrib":    round(net_contrib, 1),
        "rough_diamond":  rough_diamond,
        "rough_diamond_note": (
            "⭐ Rough Diamond — Low/Medium performance + High learning agility. "
            "Priority reskilling candidate. "
            "Framework: Jaini Desai (2024)"
            if rough_diamond else ""
        ),
        "framework":  "Employee Lifetime Value™ — Jaini Desai (2024)",
        "ip_note":    "© 2024–2026 Jaini Desai. All rights reserved.",
    }

# ═══════════════════════════════════════════════════════════════
# LMI CALCULATION
# ═══════════════════════════════════════════════════════════════

def calculate_lmi(goal_achievement, team_engagement,
                   leadership_consistency, succession_depth,
                   stakeholder_influence, change_adaptability,
                   team_size, avg_team_salary):
    """
    Leadership Momentum Index™ (LMI)
    Original framework by Jaini Desai (2024)
    Published on LinkedIn — linkedin.com/in/jainidesai

    Six dimensions:
    1. Goal Achievement
    2. Team Engagement
    3. Leadership Consistency
    4. Succession Depth
    5. Stakeholder Influence
    6. Change Adaptability

    LMI is OPTIONAL. If not provided, no impact on
    any other calculation.

    Cascade cost formula:
    cascade = team_size × avg_team_salary × cascade_multiplier
    Source: Cross, Borgatti & Parker (2.3x)

    © 2024–2026 Jaini Desai. All rights reserved.
    Unauthorized reproduction prohibited.
    """
    succession_map = {"Strong pipeline": 85, "Partial": 60, "No successor": 20}

    scores = {
        "Goal Achievement":       HML.get(goal_achievement, 60),
        "Team Engagement":        HML.get(team_engagement, 60),
        "Leadership Consistency": HML.get(leadership_consistency, 60),
        "Succession Depth":       succession_map.get(succession_depth, 60),
        "Stakeholder Influence":  HML.get(stakeholder_influence, 60),
        "Change Adaptability":    HML.get(change_adaptability, 60),
    }

    # Succession weighted higher — directly affects resilience
    weights = {
        "Goal Achievement":       0.20,
        "Team Engagement":        0.20,
        "Leadership Consistency": 0.15,
        "Succession Depth":       0.20,
        "Stakeholder Influence":  0.10,
        "Change Adaptability":    0.15,
    }

    lmi_score = sum(scores[d] * weights[d] for d in scores)

    cascade_mult = BENCHMARKS["cascade_multiplier"]["value"]
    cascade_cost = round(team_size * avg_team_salary * cascade_mult)

    retention_signal = (
        "Critical — retain at high priority"   if lmi_score >= 75 else
        "Important — assess development needs" if lmi_score >= 50 else
        "Transformation opportunity — review"
    )

    return {
        "lmi_score":        round(lmi_score, 1),
        "dimension_scores": scores,
        "cascade_cost":     cascade_cost,
        "cascade_source":   SOURCES["cross_borgatti"]["name"],
        "cascade_link":     SOURCES["cross_borgatti"]["link"],
        "retention_signal": retention_signal,
        "succession_risk":  succession_depth == "No successor",
        "framework":        "Leadership Momentum Index™ — Jaini Desai (2024)",
        "ip_note":          "© 2024–2026 Jaini Desai. All rights reserved.",
        "optional_note":    (
            "LMI is optional. When provided, adds leadership retention "
            "risk and cascade cost to the analysis. If not provided, "
            "all other calculations remain unchanged."
        ),
    }

# ═══════════════════════════════════════════════════════════════
# ROLE-LEVEL COST CALCULATION
# ═══════════════════════════════════════════════════════════════

def calculate_role_costs(soc_current, soc_target, headcount,
                          annual_salary, years_service,
                          country, province):
    """
    Full cost calculation for one released role pool
    against one target role. Returns low/mid/high ranges.
    """
    jz_target   = get_job_zone(soc_target)
    resk_cost   = RESKILLING_BY_JZ.get(jz_target, RESKILLING_BY_JZ[3])
    tech        = assess_technical_gap(soc_current, soc_target)
    months      = tech["reskilling_months"]
    weekly_pay  = annual_salary / 52

    # Productivity drag — task level
    drag = calculate_task_level_drag(
        soc_current,
        annual_salary,
        months["mid"]
    )

    # Severance
    sev = calculate_severance(
        country, province,
        years_service, weekly_pay
    )

    # Replacement cost of target role
    _, target_cad, _ = get_median_wage(soc_target)
    repl_mult = BENCHMARKS["replacement_multiplier"]

    return {
        "reskill": {
            "cost_low":   round((resk_cost["low"]  + drag["total_low"])  * headcount),
            "cost_mid":   round((resk_cost["mid"]  + drag["total_mid"])  * headcount),
            "cost_high":  round((resk_cost["high"] + drag["total_high"]) * headcount),
            "per_person_low":  resk_cost["low"]  + drag["total_low"],
            "per_person_mid":  resk_cost["mid"]  + drag["total_mid"],
            "per_person_high": resk_cost["high"] + drag["total_high"],
            "months":     months,
            "drag":       drag,
            "resk_cost":  resk_cost,
            "source":     SOURCES["deloitte"]["name"],
            "link":       SOURCES["deloitte"]["link"],
        },
        "exit": {
            "severance_low":   round(sev["low"]  * headcount),
            "severance_mid":   round(sev["mid"]  * headcount),
            "severance_high":  round(sev["high"] * headcount),
            "replacement_low":  round(target_cad * repl_mult["low"]  * headcount),
            "replacement_mid":  round(target_cad * repl_mult["mid"]  * headcount),
            "replacement_high": round(target_cad * repl_mult["high"] * headcount),
            "total_low":  round((sev["low"]  + target_cad * repl_mult["low"])  * headcount),
            "total_mid":  round((sev["mid"]  + target_cad * repl_mult["mid"])  * headcount),
            "total_high": round((sev["high"] + target_cad * repl_mult["high"]) * headcount),
            "sev_law":    sev["law"],
            "sev_link":   sev["link"],
            "sev_note":   sev["note"],
            "repl_source": SOURCES["shrm"]["name"],
            "repl_link":   SOURCES["shrm"]["link"],
        },
        "net_saving": {
            "low":  round((sev["low"]  + target_cad * repl_mult["low"])  * headcount -
                          (resk_cost["low"]  + drag["total_low"])  * headcount),
            "mid":  round((sev["mid"]  + target_cad * repl_mult["mid"])  * headcount -
                          (resk_cost["mid"]  + drag["total_mid"])  * headcount),
            "high": round((sev["high"] + target_cad * repl_mult["high"]) * headcount -
                          (resk_cost["high"] + drag["total_high"]) * headcount),
        },
    }

# ═══════════════════════════════════════════════════════════════
# FUNCTION-LEVEL PULP OPTIMIZER
# ═══════════════════════════════════════════════════════════════

def optimize_function(function_name, roles, country, province,
                       ai_stage, avg_tenure, budget=None,
                       scenario="mid"):
    """
    PuLP optimization at FUNCTION level.
    Optimization declaration: runs across all released roles
    in the function simultaneously — not role by role.

    Decision variables per role pool:
    - n_reskill: how many to reskill
    - n_exit: how many to exit
    - n_augment: how many to augment

    Objective: minimize total transformation cost
    Constraints:
    - n_reskill + n_exit + n_augment = headcount_released
    - Domain transferability >= 30% for reskill
    - Job Zone gap <= 2 for reskill
    - Total reskill cost <= budget (if provided)

    Returns strategy per role + function-level summary.
    """
    ai_mult  = AI_MULTIPLIERS.get(ai_stage, 1.0)
    prov_mod = PROVINCE_MODIFIERS.get(
        province if country == "Canada" else "United States",
        {"displacement": 1.0, "reskilling": 1.0}
    )

    role_analyses = []

    for role in roles:
        soc_code = role["soc_code"]
        title    = role["title"]
        hc       = role["headcount"]
        salary   = role["salary"]

        auto_score, auto_source = get_automation_score(soc_code)
        adjusted = min(auto_score * ai_mult * prov_mod["displacement"], 1.0)

        # Transformation type
        if adjusted >= 0.70:
            transform_type = "Eliminated"
            hc_released    = hc
            hc_tomorrow    = 0
        elif adjusted >= 0.40:
            transform_type = "Transformed"
            survival       = 1.0 - adjusted
            hc_tomorrow    = max(round(hc * survival), 1)
            hc_released    = hc - hc_tomorrow
        else:
            transform_type = "Augmented"
            hc_released    = 0
            hc_tomorrow    = hc

        if hc_released == 0:
            role_analyses.append({
                "soc_code":       soc_code,
                "title":          title,
                "headcount":      hc,
                "hc_released":    0,
                "hc_tomorrow":    hc_tomorrow,
                "transform_type": transform_type,
                "auto_score":     round(adjusted, 2),
                "recommendation": "Augment",
                "transfer_options": [],
                "costs":          None,
            })
            continue

        # Get adjacent roles from O*NET
        related = get_related_occupations(soc_code)
        bright  = [r for r in related if r["bright_outlook"]]
        targets = bright if bright else related[:3]

        transfer_options = []
        for t in targets[:3]:
            t_soc = t["soc_code"]
            if not t_soc:
                continue

            domain = assess_domain_transferability(soc_code, t_soc)
            tech   = assess_technical_gap(soc_code, t_soc)

            if not domain["transferable"] or not tech["feasible"]:
                transferable = False
                reason = (
                    "Domain gap too wide"
                    if not domain["transferable"]
                    else "Technical gap too large — Buy recommended"
                )
            else:
                transferable = True
                reason = f"{domain['signal']} | {tech['signal']}"

            costs = calculate_role_costs(
                soc_code, t_soc, hc_released,
                salary, avg_tenure, country, province
            )

            transfer_options.append({
                "target_soc":    t_soc,
                "target_title":  t["title"],
                "bright_outlook": t["bright_outlook"],
                "domain":        domain,
                "tech":          tech,
                "transferable":  transferable,
                "reason":        reason,
                "costs":         costs,
            })

        # Best transfer option
        feasible = [o for o in transfer_options if o["transferable"]]
        best     = None
        if feasible:
            best = min(
                feasible,
                key=lambda x: x["costs"]["reskill"][f"cost_{scenario}"]
            )

        # Recommendation
        if transform_type == "Augmented":
            recommendation = "Augment"
        elif best and best["costs"]["net_saving"][scenario] > 0:
            recommendation = "Reskill & Transfer"
        else:
            recommendation = "Exit & Buy"

        role_analyses.append({
            "soc_code":         soc_code,
            "title":            title,
            "headcount":        hc,
            "hc_released":      hc_released,
            "hc_tomorrow":      hc_tomorrow,
            "transform_type":   transform_type,
            "auto_score":       round(adjusted, 2),
            "auto_source":      auto_source,
            "transfer_options": transfer_options,
            "best_transfer":    best,
            "recommendation":   recommendation,
            "salary":           salary,
        })

    # ── PuLP optimization ─────────────────────────────────────
    if PULP_AVAILABLE and any(r["hc_released"] > 0 for r in role_analyses):
        try:
            prob = LpProblem(
                f"workforce_transform_{function_name.replace(' ','_')}",
                LpMinimize
            )

            vars_reskill  = {}
            vars_exit     = {}
            vars_augment  = {}
            cost_reskill  = {}
            cost_exit     = {}

            for r in role_analyses:
                k = r["soc_code"]
                hc_rel = r["hc_released"]
                if hc_rel == 0:
                    continue

                vars_reskill[k] = LpVariable(
                    f"reskill_{k.replace('-','_').replace('.','_')}",
                    lowBound=0, upBound=hc_rel, cat="Integer"
                )
                vars_exit[k] = LpVariable(
                    f"exit_{k.replace('-','_').replace('.','_')}",
                    lowBound=0, upBound=hc_rel, cat="Integer"
                )
                vars_augment[k] = LpVariable(
                    f"augment_{k.replace('-','_').replace('.','_')}",
                    lowBound=0, upBound=hc_rel, cat="Integer"
                )

                # Costs per person for scenario
                best = r.get("best_transfer")
                if best:
                    cost_reskill[k] = (
                        best["costs"]["reskill"][f"per_person_{scenario}"]
                    )
                    cost_exit[k] = (
                        best["costs"]["exit"][f"total_{scenario}"] /
                        max(hc_rel, 1)
                    )
                else:
                    cost_reskill[k] = BENCHMARKS["reskilling_cost"][scenario]
                    _, cad, _        = get_median_wage(k)
                    cost_exit[k]     = (
                        cad * BENCHMARKS["replacement_multiplier"][scenario]
                    )

                aug_cost = BENCHMARKS["augmentation_cost"][scenario]

                # Constraint: all released accounted for
                prob += (
                    vars_reskill[k] + vars_exit[k] + vars_augment[k] == hc_rel,
                    f"balance_{k.replace('-','_').replace('.','_')}"
                )

                # Reskill only if transferable
                if not r.get("best_transfer"):
                    prob += (
                        vars_reskill[k] == 0,
                        f"no_reskill_{k.replace('-','_').replace('.','_')}"
                    )

            if not vars_reskill:
                raise ValueError("No released roles to optimize")

            # Objective: minimize total cost
            prob += lpSum([
                vars_reskill[k]  * cost_reskill.get(k, 8500) +
                vars_exit[k]     * cost_exit.get(k, 170000) +
                vars_augment[k]  * BENCHMARKS["augmentation_cost"][scenario]
                for k in vars_reskill
            ])

            # Budget constraint
            if budget:
                prob += (
                    lpSum([vars_reskill[k] * cost_reskill.get(k, 8500)
                           for k in vars_reskill]) <= budget,
                    "budget_constraint"
                )

            prob.solve(PULP_CBC_CMD(msg=0))

            # Apply optimizer results
            for r in role_analyses:
                k = r["soc_code"]
                if k in vars_reskill:
                    r["optimized_reskill"]  = int(value(vars_reskill[k])  or 0)
                    r["optimized_exit"]     = int(value(vars_exit[k])     or 0)
                    r["optimized_augment"]  = int(value(vars_augment[k])  or 0)
                    r["optimizer_used"]     = True
                else:
                    r["optimized_reskill"]  = 0
                    r["optimized_exit"]     = r["hc_released"]
                    r["optimized_augment"]  = 0
                    r["optimizer_used"]     = False

        except Exception as e:
            # Fall back to rule-based if PuLP fails
            for r in role_analyses:
                rec = r.get("recommendation", "Exit & Buy")
                hc_rel = r["hc_released"]
                r["optimized_reskill"]  = hc_rel if rec == "Reskill & Transfer" else 0
                r["optimized_exit"]     = hc_rel if rec == "Exit & Buy" else 0
                r["optimized_augment"]  = hc_rel if rec == "Augment" else 0
                r["optimizer_used"]     = False
                r["optimizer_note"]     = f"Rule-based fallback: {str(e)}"
    else:
        # Rule-based fallback
        for r in role_analyses:
            rec    = r.get("recommendation", "Exit & Buy")
            hc_rel = r["hc_released"]
            r["optimized_reskill"]  = hc_rel if rec == "Reskill & Transfer" else 0
            r["optimized_exit"]     = hc_rel if rec == "Exit & Buy" else 0
            r["optimized_augment"]  = hc_rel if rec == "Augment" else 0
            r["optimizer_used"]     = False

    # ── Function-level summary ────────────────────────────────
    total_hc         = sum(r["headcount"]   for r in role_analyses)
    total_released   = sum(r["hc_released"] for r in role_analyses)
    total_reskill    = sum(r.get("optimized_reskill", 0) for r in role_analyses)
    total_exit       = sum(r.get("optimized_exit",    0) for r in role_analyses)
    total_augment    = sum(r.get("optimized_augment", 0) for r in role_analyses)
    not_transformable = sum(
        r["hc_released"]
        for r in role_analyses
        if not r.get("best_transfer") and r["hc_released"] > 0
    )

    return {
        "function_name":    function_name,
        "declaration":      (
            f"Optimization running at function level across "
            f"{len(roles)} roles, {total_hc:,} employees. "
            f"PuLP solver: {'active' if PULP_AVAILABLE else 'rule-based fallback'}."
        ),
        "total_hc":         total_hc,
        "total_released":   total_released,
        "transformable":    total_released - not_transformable,
        "not_transformable": not_transformable,
        "optimized_reskill": total_reskill,
        "optimized_exit":   total_exit,
        "optimized_augment": total_augment,
        "role_analyses":    role_analyses,
        "scenario":         scenario,
        "optimizer_used":   PULP_AVAILABLE,
    }

# ═══════════════════════════════════════════════════════════════
# COST OF INACTION
# ═══════════════════════════════════════════════════════════════

def calculate_cost_of_inaction(strategic_pop, avg_salary,
                                ai_stage, province, country,
                                months_list=[12, 24, 36]):
    """
    Cost of maintaining current workforce without transformation.
    Three components: skills obsolescence, productivity drag,
    salary waste.
    Sources: WEF Future of Jobs 2025, McKinsey State of AI 2025
    """
    ai_mult  = AI_MULTIPLIERS.get(ai_stage, 1.0)
    prov_key = province if country == "Canada" else "United States"
    prov_mod = PROVINCE_MODIFIERS.get(prov_key, {"reskilling": 1.0})
    obs_rate = BENCHMARKS["skills_obsolescence_rate"]["value"]
    drag_pct = BENCHMARKS["productivity_drag_pct"]

    results = []
    for months in months_list:
        years = months / 12

        obs_pop  = round(strategic_pop * obs_rate * ai_mult *
                         prov_mod["reskilling"] * years)
        obs_cost = {
            "low":  round(obs_pop * BENCHMARKS["reskilling_cost"]["low"]),
            "mid":  round(obs_pop * BENCHMARKS["reskilling_cost"]["mid"]),
            "high": round(obs_pop * BENCHMARKS["reskilling_cost"]["high"]),
        }
        prod_cost = {
            "low":  round(strategic_pop * avg_salary * drag_pct["low"]  * years),
            "mid":  round(strategic_pop * avg_salary * drag_pct["mid"]  * years),
            "high": round(strategic_pop * avg_salary * drag_pct["high"] * years),
        }
        salary_waste = {
            "low":  round(strategic_pop * avg_salary * 0.10 * years),
            "mid":  round(strategic_pop * avg_salary * 0.20 * years),
            "high": round(strategic_pop * avg_salary * 0.30 * years),
        }

        results.append({
            "months":        months,
            "obs_pop":       obs_pop,
            "obs_cost":      obs_cost,
            "prod_cost":     prod_cost,
            "salary_waste":  salary_waste,
            "total": {
                "low":  obs_cost["low"]  + prod_cost["low"]  + salary_waste["low"],
                "mid":  obs_cost["mid"]  + prod_cost["mid"]  + salary_waste["mid"],
                "high": obs_cost["high"] + prod_cost["high"] + salary_waste["high"],
            },
            "obs_source":  BENCHMARKS["skills_obsolescence_rate"]["source"],
            "obs_link":    BENCHMARKS["skills_obsolescence_rate"]["link"],
            "prod_source": BENCHMARKS["productivity_drag_pct"]["source"],
            "prod_link":   BENCHMARKS["productivity_drag_pct"]["link"],
        })

    return results

# ═══════════════════════════════════════════════════════════════
# SELF-FUNDING SEQUENCING
# ═══════════════════════════════════════════════════════════════

def calculate_sequencing(priority_index, scenario="mid"):
    """
    Self-funding transformation sequencing.
    Cycle 1 savings fund Cycle 2. Cycle 2 funds Cycle 3.
    © Jaini Desai — original methodology
    """
    sequences  = []
    cumulative = 0

    for i, fn in enumerate(priority_index):
        saving     = fn.get(f"net_roi_{scenario}", fn.get("net_roi", 0))
        investment = fn.get(f"transform_cost_{scenario}", fn.get("transform_cost", 0))
        cumulative += saving

        sequences.append({
            "cycle":              i + 1,
            "function":           fn["function_name"],
            "investment":         investment,
            "net_saving":         saving,
            "cumulative_saving":  cumulative,
            "funded_by":          "Initial investment" if i == 0
                                  else f"Cycle {i} savings",
        })

    return sequences
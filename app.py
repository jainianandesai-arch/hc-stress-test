"""
app.py
HC Transformation Intelligence Platform
Jaini Desai | jainidesai.com | June 2026

© 2024–2026 Jaini Desai. All rights reserved.
HC Transformation Intelligence Platform is an original
methodology by Jaini Desai. Unauthorized reproduction or
commercial use without written permission is prohibited.

Answers one board-level question:
"Do we have the workforce we need to operate tomorrow
— and what will it cost to get there?"

Version 1 — Public Demo
No agents. No charts. Clean numbers. Every figure cited.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from config import (
    get_function_names,
    get_roles_for_function,
    build_role_list,
)
from agent_onet import get_cached_profile, get_median_wage, test_connection
from transformation_engine import (
    BENCHMARKS,
    calculate_function_sizing,
    calculate_transfer_options,
    calculate_cost_of_inaction,
    calculate_priority_index,
    calculate_sequencing,
    AI_MULTIPLIERS,
    PROVINCE_MODIFIERS,
)

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="HC Transformation Intelligence",
    page_icon="⚡",
    layout="wide"
)

# ── Styling ───────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .citation {
        font-size: 11px;
        color: #888;
        margin-top: 2px;
        font-style: italic;
    }
    .boundary-note {
        background: #f8f9fa;
        border-left: 3px solid #2454a6;
        padding: 12px 16px;
        font-size: 13px;
        color: #444;
        margin: 16px 0;
    }
    .reasoning-box {
        background: #f0f4ff;
        border-left: 3px solid #2454a6;
        padding: 10px 14px;
        font-size: 13px;
        color: #333;
        margin: 8px 0;
    }
    .header-ip {
        font-size: 11px;
        color: #666;
        margin-top: 4px;
        padding: 8px 0;
        border-top: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────
st.markdown("## HC Transformation Intelligence Platform")
st.markdown(
    "Workforce economics for the AI era — "
    "built on live O\*NET data, Canadian labour law, "
    "and published research benchmarks."
)
st.markdown(
    f"**Jaini Desai** | "
    f"[jainidesai.com](https://jainidesai.com) | "
    f"{datetime.today().strftime('%B %d, %Y')}"
)
st.markdown(
    '<p class="header-ip">'
    '© 2024–2026 Jaini Desai. All rights reserved. '
    'HC Transformation Intelligence Platform is an original methodology by Jaini Desai. '
    'Unauthorized reproduction or commercial use without written permission is prohibited. '
    '| O*NET® is a trademark of the U.S. Department of Labor, '
    'Employment and Training Administration.'
    '</p>',
    unsafe_allow_html=True
)

onet_live = test_connection()
st.caption(
    f"O\*NET API: {'🟢 Live' if onet_live else '🔴 Offline — using cached data'}"
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# SECTION 1 — ORG PROFILE
# ═══════════════════════════════════════════════════════════════
st.markdown("### 1 — Organization Profile")
st.caption("No company name required. All analysis is anonymous.")

col1, col2, col3 = st.columns(3)

with col1:
    industry = st.selectbox("Industry", [
        "Financial Services",
        "Retail & Consumer",
        "Technology",
        "Healthcare",
        "Manufacturing",
        "Professional Services",
    ])
    province = st.selectbox("Province / Jurisdiction", [
        "Federal (Banks & Telecoms)",
        "Ontario",
        "British Columbia",
        "Quebec",
        "Alberta",
    ])

with col2:
    ai_stage = st.selectbox("AI Adoption Stage", [
        "Early (Exploring)",
        "Active (Piloting)",
        "Advanced (Scaling)",
    ])
    strategic_population = st.number_input(
        "Strategic Population (headcount)",
        min_value=50,
        max_value=500000,
        value=4500,
        step=50,
        help=(
            "Total employees in roles affected by AI transformation. "
            "Exclude frontline and store floor workers."
        )
    )

with col3:
    avg_tenure = st.number_input(
        "Average Tenure (years)",
        min_value=1,
        max_value=30,
        value=6,
        step=1,
        help=(
            "Used for approximate severance calculation only. "
            "Your HR and legal teams should calculate "
            "precise individual obligations."
        )
    )
    st.caption(
        "Tenure is used only for severance estimation "
        "under Canadian labour law. It does not affect "
        "any other calculation or decision in this tool."
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# SECTION 2 — FUNCTION CONFIGURATION
# ═══════════════════════════════════════════════════════════════
st.markdown("### 2 — Function Configuration")
st.caption(
    "Select the functions in your organization. "
    "Enter each function's share of your strategic population as a percentage. "
    "Total must equal 100%."
)

all_functions = get_function_names()
selected_fns  = st.multiselect(
    "Select functions",
    options=all_functions,
    default=[
        "Finance & Accounting",
        "HR & People Operations",
        "Technology & Engineering"
    ]
)

with st.expander("+ Add a custom function"):
    custom_name  = st.text_input(
        "Custom function name (e.g. Procurement, Corporate Banking)"
    )
    custom_soc   = st.text_input(
        "Closest O*NET SOC code (e.g. 13-1081.00)"
    )
    custom_title = st.text_input(
        "Role title for that SOC code"
    )
    if custom_name and custom_soc and custom_title:
        st.caption(
            f"Will be added as: {custom_name} → "
            f"{custom_soc} — {custom_title}"
        )

if not selected_fns:
    st.warning("Select at least one function to continue.")
    st.stop()

# ── Function % inputs ─────────────────────────────────────────
st.markdown(
    "**What percentage of your strategic population "
    "works in each function?**"
)
st.caption(
    "Enter a number between 0 and 100 for each function. "
    "Total must equal 100%."
)

fn_pcts = {}
n_fns   = len(selected_fns)
fn_cols = st.columns(min(n_fns, 4))

for i, fn in enumerate(selected_fns):
    with fn_cols[i % 4]:
        fn_pcts[fn] = st.number_input(
            f"{fn} (%)",
            min_value=0,
            max_value=100,
            value=0,
            step=1,
            key=f"fnpct_{fn}"
        )

total_pct = sum(fn_pcts.values())
remaining = 100 - total_pct

if total_pct == 0:
    st.caption(
        "Enter percentage per function. Total must equal 100%."
    )
elif total_pct < 100:
    st.warning(
        f"Total: {total_pct}% — {remaining}% still to allocate."
    )
elif total_pct == 100:
    st.success("Total: 100% ✓")
else:
    st.error(
        f"Total: {total_pct}% — reduce by {total_pct - 100}%."
    )

# ── Headcount preview ─────────────────────────────────────────
if total_pct > 0:
    hc_rows = []
    for fn in selected_fns:
        hc = round(strategic_population * fn_pcts[fn] / 100)
        hc_rows.append({
            "Function":              fn,
            "% of Strategic Pop":    f"{fn_pcts[fn]}%",
            "Headcount":             f"{hc:,}",
        })
    st.dataframe(
        pd.DataFrame(hc_rows),
        use_container_width=True,
        hide_index=True
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# SECTION 3 — ASSESSMENT MODE
# ═══════════════════════════════════════════════════════════════
st.markdown("### 3 — Assessment Mode")
st.caption(
    "Quick Assessment uses O*NET weighted averages per function — "
    "fast and directional. "
    "Deep Dive breaks down by role within each function — "
    "precise and board-ready."
)

mode      = st.radio(
    "Choose assessment depth",
    options=[
        "Quick Assessment — function level",
        "Deep Dive — role level within each function",
    ],
    index=0
)
deep_dive = "Deep Dive" in mode

# ── Role % inputs (Deep Dive only) ───────────────────────────
role_overrides = {}

if deep_dive:
    st.markdown("**Enter role distribution within each function.**")
    st.caption(
        "Default splits are pre-filled from O*NET job family data. "
        "Adjust to match your organization. "
        "Each function must total 100%."
    )

    for fn in selected_fns:
        fn_hc = round(strategic_population * fn_pcts.get(fn, 0) / 100)
        with st.expander(f"{fn} — {fn_hc:,} people"):
            roles        = get_roles_for_function(fn)
            r_cols       = st.columns(len(roles))
            fn_role_pcts = {}

            for j, role in enumerate(roles):
                with r_cols[j]:
                    fn_role_pcts[role["soc_code"]] = st.number_input(
                        f"{role['title']} (%)",
                        min_value=0,
                        max_value=100,
                        value=role["default_pct"],
                        step=1,
                        key=f"role_{fn}_{role['soc_code']}"
                    )

            role_total = sum(fn_role_pcts.values())
            if role_total == 100:
                st.success("Total: 100% ✓")
            else:
                st.warning(
                    f"Total: {role_total}% — must equal 100%"
                )

            # Headcount preview per role
            role_hc_rows = []
            for role in roles:
                rh = round(fn_hc * fn_role_pcts.get(role["soc_code"], 0) / 100)
                role_hc_rows.append({
                    "Role":       role["title"],
                    "SOC Code":   role["soc_code"],
                    "%":          f"{fn_role_pcts.get(role['soc_code'], 0)}%",
                    "Headcount":  f"{rh:,}",
                })
            st.dataframe(
                pd.DataFrame(role_hc_rows),
                use_container_width=True,
                hide_index=True
            )

            role_overrides[fn] = fn_role_pcts

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# RUN BUTTON
# ═══════════════════════════════════════════════════════════════
run = st.button(
    "▶  Run Transformation Analysis",
    use_container_width=True,
    type="primary"
)

if not run:
    st.stop()

if total_pct != 100:
    st.error(
        "Function percentages must total exactly 100% before running."
    )
    st.stop()

# ═══════════════════════════════════════════════════════════════
# ENGINE
# ═══════════════════════════════════════════════════════════════
with st.spinner(
    "Pulling live O\*NET data and running transformation analysis..."
):
    all_function_results = []
    avg_wages_list       = []

    for fn in selected_fns:
        fn_hc     = round(strategic_population * fn_pcts[fn] / 100)
        overrides = role_overrides.get(fn) if deep_dive else None
        roles     = build_role_list(fn, fn_hc, overrides)

        sizing    = calculate_function_sizing(
            roles, ai_stage, province
        )
        decisions = calculate_transfer_options(
            sizing, province,
            avg_years_service=avg_tenure
        )

        fn_wages    = [
            get_median_wage(r["soc_code"])[1] for r in roles
        ]
        fn_avg_wage = (
            round(sum(fn_wages) / len(fn_wages))
            if fn_wages else 75000
        )
        avg_wages_list.append(fn_avg_wage)

        inaction = calculate_cost_of_inaction(
            fn_hc, fn_avg_wage, ai_stage, province
        )

        all_function_results.append({
            "function_name":  fn,
            "headcount":      fn_hc,
            "sizing":         sizing,
            "decisions":      decisions,
            "inaction_costs": inaction,
            "avg_wage_cad":   fn_avg_wage,
        })

    priority_index = calculate_priority_index(all_function_results)
    sequencing     = calculate_sequencing(priority_index)

    total_released = sum(
        sum(r["headcount_released"] for r in fn["sizing"])
        for fn in all_function_results
    )
    total_transform_cost = sum(
        p["transform_cost"] for p in priority_index
    )
    total_inaction_24 = sum(
        fn["inaction_costs"][1]["total"]
        for fn in all_function_results
    )

# ═══════════════════════════════════════════════════════════════
# OUTPUT HEADER
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## Transformation Analysis Results")
st.markdown(
    f"*{industry} | "
    f"{strategic_population:,} strategic population | "
    f"{ai_stage} | {province} | "
    f"Average tenure: {avg_tenure} years | "
    f"{datetime.today().strftime('%B %d, %Y')}*"
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Strategic Population",       f"{strategic_population:,}")
m2.metric("Total HC Released",          f"{total_released:,}")
m3.metric("Transformation Investment",  f"${total_transform_cost:,.0f}")
m4.metric("Cost of Inaction (24mo)",    f"${total_inaction_24:,.0f}")

# ═══════════════════════════════════════════════════════════════
# TABLE 0 — PRIORITY INDEX
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Where to Start — Transformation Priority Index")
st.caption(
    "Functions ranked by net ROI. "
    "Highest ROI = biggest gap between cost of inaction "
    "and transformation investment required. "
    "Start here — Cycle 1 savings fund Cycle 2."
)

priority_rows = []
for i, p in enumerate(priority_index):
    priority_rows.append({
        "Priority":                   i + 1,
        "Function":                   p["function_name"],
        "Avg Automation Rate":        f"{p['avg_automation']*100:.0f}%",
        "HC Today":                   f"{p['headcount_today']:,}",
        "HC Released":                f"{p['headcount_released']:,}",
        "Transformation Investment":  f"${p['transform_cost']:,.0f}",
        "Cost of Inaction (24mo)":    f"${p['inaction_24mo']:,.0f}",
        "Net ROI":                    f"${p['net_roi']:,.0f}",
        "Start Here":                 p["label"],
    })

st.dataframe(
    pd.DataFrame(priority_rows),
    use_container_width=True,
    hide_index=True
)
st.markdown(
    '<p class="citation">'
    'Automation rates: O*NET / Frey & Osborne (2013) | '
    'Inaction cost: WEF Future of Jobs 2025 + McKinsey State of AI 2025'
    '</p>',
    unsafe_allow_html=True
)

# ═══════════════════════════════════════════════════════════════
# TABLE 1 — FUNCTION SUMMARY
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Function Transformation Summary")

fn_summary_rows = []
for fn in all_function_results:
    sizing   = fn["sizing"]
    hc_today = sum(r["headcount_today"]    for r in sizing)
    hc_tom   = sum(r["headcount_tomorrow"] for r in sizing)
    hc_rel   = sum(r["headcount_released"] for r in sizing)
    all_gaps = []
    for d in fn["decisions"]:
        all_gaps.extend(d.get("skills_gap", []))
    top_gap = all_gaps[0] if all_gaps else "No gap identified"

    fn_summary_rows.append({
        "Function":        fn["function_name"],
        "HC Today":        f"{hc_today:,}",
        "HC Tomorrow":     f"{hc_tom:,}",
        "HC Released":     f"{hc_rel:,}",
        "Avg Wage (CAD)":  f"${fn['avg_wage_cad']:,}",
        "Top Skills Gap":  top_gap,
        "Exposure (24mo)": f"${fn['inaction_costs'][1]['total']:,.0f}",
    })

st.dataframe(
    pd.DataFrame(fn_summary_rows),
    use_container_width=True,
    hide_index=True
)

# ═══════════════════════════════════════════════════════════════
# TABLE 2 — ROLE-LEVEL DETAIL
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Role-Level Detail")
st.caption("Expandable per function. Median wage in CAD per role.")

for fn in all_function_results:
    with st.expander(
        f"{fn['function_name']} — {fn['headcount']:,} people"
    ):
        role_rows = []
        for r in fn["sizing"]:
            _, cad, _ = get_median_wage(r["soc_code"])
            role_rows.append({
                "Role":              r["title"],
                "SOC Code":          r["soc_code"],
                "Median Wage (CAD)": f"${cad:,}",
                "Automation Rate":   f"{r['automation_score']*100:.0f}%",
                "Transform Type":    r["transform_type"],
                "HC Today":          f"{r['headcount_today']:,}",
                "HC Tomorrow":       f"{r['headcount_tomorrow']:,}",
                "HC Released":       f"{r['headcount_released']:,}",
            })
        st.dataframe(
            pd.DataFrame(role_rows),
            use_container_width=True,
            hide_index=True
        )
        st.markdown(
            '<p class="citation">'
            'Automation: O*NET / Frey & Osborne (2013) | '
            'Wages: O*NET BLS Data → CAD @ Bank of Canada '
            'June 10, 2026 (1 USD = 1.36 CAD)'
            '</p>',
            unsafe_allow_html=True
        )

# ═══════════════════════════════════════════════════════════════
# TABLE 3 — OPTIMIZATION MODEL
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Optimization Model — Reskill / Buy / Augment")
st.caption(
    "Three paths evaluated per released pool. "
    "Job Zone gap drives feasibility. "
    "Median salary drives all cost calculations. "
    "Company decides — tool surfaces economics and reasoning only."
)

for fn in all_function_results:
    if not fn["decisions"]:
        continue

    st.markdown(f"**{fn['function_name']}**")

    decision_rows = []
    for d in fn["decisions"]:
        best = d.get("best_transfer")
        path = d["recommended_path"]

        decision_rows.append({
            "Role Pool":             d["title"],
            "HC Released":           f"{d['headcount_released']:,}",
            "Median Wage (CAD)":     f"${d['wage_cad']:,}",
            "Recommended Path":      path,
            "Adjacent Role":         best["adjacent_title"] if best else "—",
            "Job Zone Gap":          best["job_zone_gap"] if best else "—",
            "Reskill Time":          f"{best['reskilling_months']} months" if best else "—",
            "Reskill Cost (total)":  f"${best['transfer_cost_total']:,.0f}" if best else "—",
            "Productivity Drag":     (
                f"${best['productivity_drag_per_person'] * d['headcount_released']:,.0f}"
                if best else "—"
            ),
            "Severance (total)":     f"${d['severance_per_person'] * d['headcount_released']:,.0f}",
            "Replacement (total)":   f"${d['replacement_per_person'] * d['headcount_released']:,.0f}",
            "Exit Cost (total)":     f"${d['exit_cost_total']:,.0f}",
            "Net Saving if Reskill": f"${d['net_saving_if_transfer']:,.0f}" if best else "—",
        })

    st.dataframe(
        pd.DataFrame(decision_rows),
        use_container_width=True,
        hide_index=True
    )

    # Reasoning per pool
    for d in fn["decisions"]:
        best = d.get("best_transfer")
        path = d["recommended_path"]

        if path == "Augment":
            reasoning = (
                f"<b>{d['title']}</b> — Augment. "
                f"Automation rate {d['automation_score']*100:.0f}% — role survives intact. "
                f"Skills gap: "
                f"{', '.join(d['skills_gap'][:3]) if d['skills_gap'] else 'none identified'}. "
                f"Tool adoption training recommended. "
                f"Estimated cost: $3,500 per person."
            )
        elif path == "Transfer & Reskill" and best:
            reasoning = (
                f"<b>{d['title']}</b> — Reskill and Transfer. "
                f"Job Zone gap {best['job_zone_gap']} — transfer feasible. "
                f"Adjacent role: {best['adjacent_title']} "
                f"({'Bright Outlook ✓' if best['bright_outlook'] else 'stable role'}). "
                f"Reskilling time: {best['reskilling_months']} months. "
                f"Transfer saves ${d['net_saving_if_transfer']:,.0f} "
                f"vs full exit and replacement."
            )
        else:
            reasoning = (
                f"<b>{d['title']}</b> — Buy. "
                f"Job Zone gap too large for viable reskilling — "
                f"target role requires significantly more preparation. "
                f"Exit with severance "
                f"(${d['severance_per_person']:,.0f} per person "
                f"under {d['severance_law']} — "
                f"approximate based on {avg_tenure} year average tenure). "
                f"Replace with skilled external hire "
                f"(${d['replacement_per_person']:,.0f} per person)."
            )

        st.markdown(
            f'<div class="reasoning-box">{reasoning}</div>',
            unsafe_allow_html=True
        )

    st.markdown(
        '<p class="citation">'
        'Reskilling: $8,500 CAD — Deloitte 2026 Global Human Capital Trends | '
        'Productivity drag: varies by Job Zone gap — '
        'McKinsey State of AI 2025 (20–25% organizational average) | '
        'Replacement: 2× median salary — SHRM Workforce Benchmark 2024 | '
        f'Severance: {province} labour law — '
        f'approximate based on {avg_tenure} year average tenure'
        '</p>',
        unsafe_allow_html=True
    )

st.markdown("""
<div class="boundary-note">
<strong>On individual decisions:</strong>
Which employees within each released pool to reskill vs exit
is an internal decision based on your organization's performance data,
learning agility assessments, and manager input.
The above reflects population-level economics only.
Your HR and legal teams should calculate precise individual
severance obligations before any action is taken.
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# TABLE 4 — 0–36 MONTH COST TIMELINE
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 0–36 Month Cost Timeline")
st.caption(
    "When each dollar lands. "
    "Augmentation costs hit first (0–6 months). "
    "Reskilling and productivity drag run through mid-term (6–18 months). "
    "Exit and replacement costs land in the final phase (18–36 months)."
)

timeline_rows = []
for fn in all_function_results:
    augment_hc   = sum(
        r["headcount_today"] for r in fn["sizing"]
        if r["transform_type"] == "Augmented"
    )
    transform_hc = sum(
        r["headcount_released"] for r in fn["sizing"]
        if r["transform_type"] == "Transformed"
    )
    exit_hc      = sum(
        r["headcount_released"] for r in fn["sizing"]
        if r["transform_type"] == "Eliminated"
    )

    augment_cost   = augment_hc * 3500
    reskill_cost   = transform_hc * BENCHMARKS["reskilling_cost_cad"]["value"]
    prod_drag_cost = round(
        transform_hc * fn["avg_wage_cad"]
        * BENCHMARKS["productivity_drag_pct"]["value"]
    )
    exit_cost      = sum(
        d["exit_cost_total"] for d in fn["decisions"]
        if d["recommended_path"] != "Transfer & Reskill"
    )

    timeline_rows.append({
        "Function":                   fn["function_name"],
        "0–6 mo: Augmentation":       f"${augment_cost:,.0f}",
        "HC Augmented":               f"{augment_hc:,}",
        "6–18 mo: Reskilling":        f"${reskill_cost:,.0f}",
        "6–18 mo: Productivity Drag": f"${prod_drag_cost:,.0f}",
        "HC Reskilling":              f"{transform_hc:,}",
        "18–36 mo: Exit + Replace":   f"${exit_cost:,.0f}",
        "HC Exited":                  f"{exit_hc:,}",
    })

st.dataframe(
    pd.DataFrame(timeline_rows),
    use_container_width=True,
    hide_index=True
)
st.markdown(
    '<p class="citation">'
    'Augmentation training: $3,500/person (conservative benchmark) | '
    'Reskilling: $8,500/person — Deloitte 2026 | '
    'Productivity drag: McKinsey State of AI 2025 | '
    'Exit timing: Canada Labour Code notice periods'
    '</p>',
    unsafe_allow_html=True
)

# ═══════════════════════════════════════════════════════════════
# TABLE 5 — SKILLS GAP
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Skills Gap by Role")
st.caption(
    "Today's skills vs tomorrow's required skills. "
    "Gap = skills needed tomorrow not present today. "
    "Source: O*NET Hot Technology endpoint."
)

skills_rows = []
for fn in all_function_results:
    for d in fn["decisions"]:
        today    = ", ".join(d["today_skills"][:4])    if d["today_skills"]    else "—"
        tomorrow = ", ".join(d["tomorrow_skills"][:4]) if d["tomorrow_skills"] else "—"
        gap      = ", ".join(d["skills_gap"][:4])      if d["skills_gap"]      else "No gap identified"
        skills_rows.append({
            "Function":          fn["function_name"],
            "Role":              d["title"],
            "Today's Skills":    today,
            "Tomorrow's Skills": tomorrow,
            "Skills Gap":        gap,
        })

if skills_rows:
    st.dataframe(
        pd.DataFrame(skills_rows),
        use_container_width=True,
        hide_index=True
    )
    st.markdown(
        '<p class="citation">'
        'Source: O*NET Technology Skills + Hot Technology endpoints — '
        'U.S. Dept of Labor, Employment and Training Administration'
        '</p>',
        unsafe_allow_html=True
    )

# ═══════════════════════════════════════════════════════════════
# TABLE 6 — COST OF INACTION
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Cost of Inaction")
st.caption(
    "What it costs to maintain the current workforce "
    "without transformation as AI adoption continues."
)

inaction_rows = []
for fn in all_function_results:
    for ic in fn["inaction_costs"]:
        inaction_rows.append({
            "Function":            fn["function_name"],
            "Timeframe":           f"{ic['months']} months",
            "Skills Obsolescence": f"${ic['obs_cost']:,.0f}",
            "Productivity Drag":   f"${ic['productivity_cost']:,.0f}",
            "Salary Waste":        f"${ic['salary_waste']:,.0f}",
            "Total":               f"${ic['total']:,.0f}",
        })

st.dataframe(
    pd.DataFrame(inaction_rows),
    use_container_width=True,
    hide_index=True
)
st.markdown(
    '<p class="citation">'
    'Skills obsolescence 39%: WEF Future of Jobs Report 2025 | '
    'Productivity drag 23%: McKinsey State of AI 2025 | '
    'Salary waste: 20% of salary for unrestructured roles '
    '(conservative estimate)'
    '</p>',
    unsafe_allow_html=True
)

# ═══════════════════════════════════════════════════════════════
# TABLE 7 — SELF-FUNDING SEQUENCING
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Self-Funding Transformation Sequencing")
st.caption(
    "Cycle 1 savings fund Cycle 2. "
    "Cycle 2 savings fund Cycle 3. "
    "Additional capital required after Cycle 1: $0."
)

seq_rows = []
for s in sequencing:
    seq_rows.append({
        "Cycle":               s["cycle"],
        "Function":            s["function"],
        "Investment Required": f"${s['investment']:,.0f}",
        "Net Saving":          f"${s['net_saving']:,.0f}",
        "Cumulative Saving":   f"${s['cumulative_saving']:,.0f}",
        "Funded By":           s["funded_by"],
    })

st.dataframe(
    pd.DataFrame(seq_rows),
    use_container_width=True,
    hide_index=True
)

# ═══════════════════════════════════════════════════════════════
# TABLE 8 — DATA SOURCES & CITATIONS
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Data Sources & Citations")
st.caption(
    "Every number in this analysis is traceable to a named source. "
    "Nothing assumed without citation."
)

citations = [
    {
        "Data Point":  "Automation probabilities by occupation",
        "Value":       "Per SOC code (0.02–0.99)",
        "Source":      "Frey & Osborne (2013) / O*NET Web Services, U.S. Dept of Labor",
        "Formula":     "base_score × AI_multiplier × province_modifier",
    },
    {
        "Data Point":  "Reskilling cost per employee",
        "Value":       "$8,500 CAD",
        "Source":      "Deloitte 2026 Global Human Capital Trends",
        "Formula":     "Fixed benchmark × province reskilling modifier",
    },
    {
        "Data Point":  "Productivity drag during transition",
        "Value":       "10–35% depending on Job Zone gap",
        "Source":      "McKinsey State of AI 2025 (20–25% organizational average)",
        "Formula":     "annual_wage × drag_pct × (reskilling_months / 12)",
    },
    {
        "Data Point":  "Skills obsolescence rate",
        "Value":       "39% by 2028",
        "Source":      "WEF Future of Jobs Report 2025",
        "Formula":     "strategic_pop × 0.39 × AI_multiplier × province_modifier × years",
    },
    {
        "Data Point":  "Replacement cost",
        "Value":       "2× annual median salary",
        "Source":      "SHRM Workforce Benchmark 2024",
        "Formula":     "median_wage_CAD × 2.0",
    },
    {
        "Data Point":  "Median wages (USD to CAD)",
        "Value":       "Per SOC code",
        "Source":      "O*NET BLS Occupational Employment Statistics → Bank of Canada June 10, 2026",
        "Formula":     "onet_wage_usd × 1.36",
    },
    {
        "Data Point":  "Severance calculations",
        "Value":       f"Approximate — based on {avg_tenure} year average tenure",
        "Source":      "Canada Labour Code R.S.C. 1985 c.L-2 | Ontario ESA 2000 | BC ESA RSBC 1996 | Quebec CQLR c.N-1.1 | Alberta ESC RSA 2000",
        "Formula":     "Per jurisdiction formula. Precise individual calculations must be done by your HR and legal teams.",
    },
    {
        "Data Point":  "Job Zone (reskilling complexity)",
        "Value":       "1–5 per occupation",
        "Source":      "O*NET Web Services — Job Zone endpoint",
        "Formula":     "JZ gap 0-1 = 3-6 months | gap 2 = 12 months | gap 3+ = Buy recommended",
    },
    {
        "Data Point":  "Adjacent roles (transfer options)",
        "Value":       "Per occupation",
        "Source":      "O*NET Web Services — Related Occupations endpoint",
        "Formula":     "Filtered by Bright Outlook flag + Job Zone gap <= 2",
    },
    {
        "Data Point":  "Augmentation training cost",
        "Value":       "$3,500 per person",
        "Source":      "Conservative benchmark — tool adoption and AI literacy training",
        "Formula":     "Fixed per augmented employee",
    },
]

st.dataframe(
    pd.DataFrame(citations),
    use_container_width=True,
    hide_index=True
)

# ── Footer ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray; font-size:12px;'>"
    "HC Transformation Intelligence Platform | "
    "© 2024–2026 Jaini Desai | "
    "jainidesai.com | "
    "Original methodology — unauthorized reproduction prohibited"
    "</p>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align:center; color:gray; font-size:11px;'>"
    "This application incorporates information from "
    "<a href='https://www.onetcenter.org' target='_blank'>"
    "O*NET Web Services</a> by the U.S. Department of Labor, "
    "Employment and Training Administration (USDOL/ETA). "
    "O*NET® is a trademark of USDOL/ETA."
    "</p>",
    unsafe_allow_html=True
)
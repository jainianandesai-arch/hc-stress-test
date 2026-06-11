"""
app.py
Workforce Transformation Intelligence™
Jaini Desai | jainidesai.com | June 2026

© 2024–2026 Jaini Desai. All rights reserved.
Workforce Transformation Intelligence™ is an original methodology by Jaini Desai.
Employee Lifetime Value™ (ELV) and Leadership Momentum Index™ (LMI) are original
frameworks by Jaini Desai (2024). Unauthorized reproduction or commercial use
without written permission is prohibited.

Tabs:
1. Transformation Analysis — organization-level workforce transformation
2. Optimization Model — function-level PuLP optimization with ranges
3. Custom Calculator — individual, function builder, or CSV upload
4. Reference & Glossary — plain language explanations with citations
5. How It Works — worked example, step by step
6. Methodology & Sources — full citation table with links
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime

from config import (
    get_function_names,
    get_roles_for_function,
    build_role_list,
    get_capabilities_for_function,
)
from agent_onet import (
    get_cached_profile,
    get_median_wage,
    get_automation_score,
    get_job_zone,
    get_tasks,
    get_hot_technology,
    get_technology_skills,
    get_related_occupations,
    get_dwa_overlap_score,
    test_connection,
    AUTOMATION_SCORES,
)
from transformation_engine import (
    calculate_function_sizing,
    calculate_transfer_options,
    calculate_cost_of_inaction as legacy_inaction,
    calculate_priority_index,
    calculate_sequencing as legacy_sequencing,
    BENCHMARKS as LEGACY_BENCHMARKS,
    AI_MULTIPLIERS,
    PROVINCE_MODIFIERS,
)
from optimization_engine import (
    optimize_function,
    calculate_elv,
    calculate_lmi,
    calculate_cost_of_inaction,
    calculate_sequencing,
    calculate_severance,
    BENCHMARKS,
    SOURCES,
    JURISDICTIONS,
    JZ_GAP_TO_MONTHS,
    RESKILLING_BY_JZ,
    calculate_task_level_drag,
)

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Workforce Transformation Intelligence™",
    page_icon="⚡",
    layout="wide"
)

# ── Styling ───────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }

    /* Button — cobalt blue — force override Streamlit theme */
    .stButton > button,
    .stButton > button:focus,
    .stButton > button[kind="primary"],
    .stButton > button[kind="secondary"],
    div.stButton > button {
        background-color: #2454a6 !important;
        color: white !important;
        border: 1px solid #2454a6 !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover,
    div.stButton > button:hover {
        background-color: #1a3d7c !important;
        color: white !important;
        border: 1px solid #1a3d7c !important;
    }

    .citation {
        font-size: 11px;
        color: #888;
        font-style: italic;
        margin-top: 2px;
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
    .redesign-box {
        background: #f0fff4;
        border-left: 3px solid #28a745;
        padding: 10px 14px;
        font-size: 13px;
        color: #333;
        margin: 8px 0;
    }
    .resilience-box {
        background: #fff8f0;
        border-left: 3px solid #fd7e14;
        padding: 12px 16px;
        font-size: 13px;
        color: #444;
        margin: 16px 0;
    }
    .range-note {
        font-size: 12px;
        color: #666;
        font-style: italic;
    }
    .ip-note {
        font-size: 11px;
        color: #666;
        padding: 8px 0;
        border-top: 1px solid #eee;
        margin-top: 4px;
    }
    .nav-bar {
        font-size: 12px;
        color: #2454a6;
        padding: 8px 0;
        border-top: 1px solid #eee;
        margin-top: 24px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────
st.markdown("## Workforce Transformation Intelligence™")
st.markdown(
    "Workforce transformation decision intelligence — "
    "powered by live O\*NET data, Canadian and US labour law, "
    "and published research benchmarks."
)
st.markdown(
    f"**Jaini Desai** | "
    f"[jainidesai.com](https://jainidesai.com) | "
    f"{datetime.today().strftime('%B %d, %Y')}"
)
st.markdown(
    '<p class="ip-note">'
    '© 2024–2026 Jaini Desai. All rights reserved. '
    'Workforce Transformation Intelligence™ is an original methodology by Jaini Desai. '
    'Employee Lifetime Value™ and Leadership Momentum Index™ are original frameworks '
    'by Jaini Desai (2024). Unauthorized reproduction or commercial use without '
    'written permission is prohibited. | '
    'O*NET® is a trademark of the U.S. Department of Labor, '
    'Employment and Training Administration.'
    '</p>',
    unsafe_allow_html=True
)

onet_live = test_connection()
st.caption(
    f"O\*NET API: {'🟢 Live' if onet_live else '🔴 Offline — using cached data'}"
)

# ── About expander ────────────────────────────────────────────
with st.expander("ℹ️ About This Platform & The Builder"):
    st.markdown("""
**Workforce Transformation Intelligence™**

This platform answers one board-level question:
*"Do we have the workforce we need to operate tomorrow — and what will it cost to get there?"*

It starts with tomorrow's work requirements — driven by live O\*NET data — and works
backwards to today's workforce to calculate the transformation gap, the cost of closing
it, and the cost of doing nothing.

---

**The Builder**

**Jaini Desai**
Workforce Intelligence & AI Enablement Leader | Workforce Transformation Strategist

Jaini is a senior workforce intelligence professional with experience at Walmart Canada
and Starbucks Canada, specializing in workforce transformation, AI enablement, and
strategic workforce planning. She built this platform to demonstrate that workforce
transformation decisions deserve the same analytical rigor applied to financial risk —
grounded in data, defensible at the board level, and actionable for HR and finance
leaders simultaneously.

🌐 [jainidesai.com](https://jainidesai.com)
💼 [LinkedIn](https://www.linkedin.com/in/jainidesai)

---

**Original Frameworks & IP**

**Employee Lifetime Value™ (ELV)** — Jaini Desai (2024)
Measures the total economic and organizational value of an employee over their
remaining tenure. Formula: Performance Score × Skill Adjacency Score ×
Net Contribution Period − Retraining Cost.

**Leadership Momentum Index™ (LMI)** — Jaini Desai (2024)
Measures leadership effectiveness across six dimensions: Goal Achievement,
Team Engagement, Leadership Consistency, Succession Depth, Stakeholder
Influence, and Change Adaptability.

**Broken Pipeline Principle** — Jaini Desai
*"Workforce transformation without pipeline strategy is just delayed organizational damage."*

**Rough Diamond Framework** — Jaini Desai
Low performance + High learning agility = most valuable junior employee
for transformation investment.

---

**Privacy**
This tool does not collect, store, or transmit any uploaded organizational data.
All calculations are performed in-session. Closing the browser clears all data.
Upload masked data only — no names, no employee IDs, no personal identifiers.
    """)

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Transformation Analysis",
    "⚙️ Optimization Model",
    "🧮 Custom Calculator",
    "📖 Reference & Glossary",
    "💡 How It Works",
    "📚 Methodology & Sources",
])

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════
def nav_bar():
    st.markdown(
        '<p class="nav-bar">'
        '↑ <a href="#workforce-transformation-intelligence">Back to top</a> | '
        '📊 Transformation Analysis | ⚙️ Optimization Model | '
        '🧮 Custom Calculator | 📖 Reference | '
        '💡 How It Works | 📚 Sources'
        '</p>',
        unsafe_allow_html=True
    )

def fmt(n, currency="$"):
    if n is None:
        return "—"
    return f"{currency}{n:,.0f}"

def range_str(low, mid, high, currency="$"):
    return f"{fmt(low, currency)} — {fmt(mid, currency)} — {fmt(high, currency)}"

# ── Work redesign path logic ──────────────────────────────────
def get_work_redesign_path(automation_score, task_title=""):
    """
    Determines work redesign recommendation per task based on
    automation probability.
    Five paths: Automate / Self-service / Shared Services /
                Centralize / Keep
    © Jaini Desai — Work Redesign Engine
    """
    if automation_score >= 0.85:
        return "🤖 Automate", "AI or software handles entirely"
    elif automation_score >= 0.65:
        return "🔄 Self-service", "Employee or customer performs directly"
    elif automation_score >= 0.45:
        return "🏢 Shared Services", "Centralize across the organization"
    elif automation_score >= 0.25:
        return "📦 Centralize", "Pool with similar work — reduce duplication"
    else:
        return "✅ Keep", "Human judgment required — retain in role"

# ── Workforce Resilience Score ────────────────────────────────
def calculate_resilience_score(all_fn_results, avg_tenure):
    """
    Workforce Resilience Score — single number 0–100.
    Answers: if 20% of the workforce left tomorrow,
    could the organization still operate?

    Five components:
    1. Automation exposure — lower is more resilient
    2. Transferability — higher overlap = more resilient
    3. Skill redundancy — more functions = more resilient
    4. Tenure stability — longer average tenure = more resilient
    5. Succession signal — HC retained ratio

    © Jaini Desai — original methodology
    """
    if not all_fn_results:
        return 50, []

    total_hc      = sum(
        sum(r["headcount_today"] for r in fn["sizing"])
        for fn in all_fn_results
    )
    total_released = sum(
        sum(r["headcount_released"] for r in fn["sizing"])
        for fn in all_fn_results
    )
    total_retained = total_hc - total_released

    # Component 1 — Automation exposure (inverted — lower auto = better)
    avg_auto = sum(
        r["automation_score"] * r["headcount_today"]
        for fn in all_fn_results
        for r in fn["sizing"]
    ) / max(total_hc, 1)
    auto_score = round((1 - avg_auto) * 100)

    # Component 2 — Transferability (% of released with a transfer option)
    total_decisions = sum(len(fn["decisions"]) for fn in all_fn_results)
    transferable    = sum(
        1 for fn in all_fn_results
        for d in fn["decisions"]
        if d.get("best_transfer")
    )
    transfer_score = round((transferable / max(total_decisions, 1)) * 100)

    # Component 3 — Skill redundancy (number of functions covered)
    fn_count       = len(all_fn_results)
    redundancy_score = min(round((fn_count / 10) * 100), 100)

    # Component 4 — Tenure stability (longer tenure = more resilient)
    tenure_score = min(round((avg_tenure / 15) * 100), 100)

    # Component 5 — HC retained ratio
    retention_score = round((total_retained / max(total_hc, 1)) * 100)

    # Weighted composite
    resilience = round(
        auto_score      * 0.25 +
        transfer_score  * 0.25 +
        redundancy_score * 0.15 +
        tenure_score    * 0.15 +
        retention_score * 0.20
    )

    # Risk signals
    signals = []
    if avg_auto >= 0.60:
        signals.append("🔴 High automation exposure — significant portion of workforce at risk")
    if transfer_score < 40:
        signals.append("🔴 Low transferability — limited internal transfer paths identified")
    if fn_count < 3:
        signals.append("🟡 Limited function coverage — skill redundancy risk")
    if avg_tenure < 4:
        signals.append("🟡 Low average tenure — higher flight risk during transformation")
    if retention_score < 60:
        signals.append("🔴 More than 40% of workforce released — critical resilience risk")
    if not signals:
        signals.append("🟢 No critical resilience risks identified")

    return resilience, signals

# ═══════════════════════════════════════════════════════════════
# TAB 1 — TRANSFORMATION ANALYSIS
# ═══════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### 1 — Organization Profile")
    st.caption("No company name required. All analysis is anonymous.")

    col1, col2, col3 = st.columns(3)

    with col1:
        country = st.selectbox(
            "Country", ["Canada", "United States"], key="t1_country"
        )
        industry = st.selectbox("Industry", [
            "Financial Services", "Retail & Consumer", "Technology",
            "Healthcare", "Manufacturing", "Professional Services",
        ], key="t1_industry")

    with col2:
        if country == "Canada":
            province = st.selectbox("Province / Jurisdiction", [
                "Federal (Banks & Telecoms)", "Ontario",
                "British Columbia", "Quebec", "Alberta",
            ], key="t1_province")
        else:
            province = "United States"
            st.info(
                "🇺🇸 United States — WARN Act severance applies. "
                "No statutory per-person minimum."
            )
        ai_stage = st.selectbox("AI Adoption Stage", [
            "Early (Exploring)", "Active (Piloting)", "Advanced (Scaling)",
        ], key="t1_ai")

    with col3:
        strategic_population = st.number_input(
            "Strategic Population (headcount)",
            min_value=50, max_value=500000,
            value=4500, step=50, key="t1_pop"
        )
        avg_tenure = st.number_input(
            "Average Tenure (years)",
            min_value=1, max_value=30,
            value=6, step=1, key="t1_tenure",
            help="Used for approximate severance only."
        )
        st.caption(
            "Tenure used for severance estimation only. "
            "Does not affect any other calculation."
        )

    st.markdown("---")
    st.markdown("### 2 — Function Configuration")
    st.caption(
        "Select functions. Enter each function's % of strategic population. "
        "Total must equal 100%."
    )

    all_fns      = get_function_names()
    selected_fns = st.multiselect(
        "Select functions",
        options=all_fns,
        default=["Finance & Accounting", "HR & People Operations",
                 "Technology & Engineering"],
        key="t1_fns"
    )

    with st.expander("+ Add a custom function"):
        c_name  = st.text_input("Custom function name", key="t1_cname")
        c_soc   = st.text_input("O*NET SOC code", key="t1_csoc")
        c_title = st.text_input("Role title", key="t1_ctitle")
        if c_name and c_soc and c_title:
            st.caption(f"Will map: {c_name} → {c_soc} — {c_title}")

    if not selected_fns:
        st.warning("Select at least one function.")
        st.stop()

    st.markdown("**% of strategic population per function:**")
    fn_pcts = {}
    fn_cols = st.columns(min(len(selected_fns), 4))
    for i, fn in enumerate(selected_fns):
        with fn_cols[i % 4]:
            fn_pcts[fn] = st.number_input(
                f"{fn} (%)", min_value=0, max_value=100,
                value=0, step=1, key=f"t1_pct_{fn}"
            )

    total_pct = sum(fn_pcts.values())
    if total_pct == 0:
        st.caption("Enter % per function. Total must equal 100%.")
    elif total_pct < 100:
        st.warning(f"Total: {total_pct}% — {100-total_pct}% remaining.")
    elif total_pct == 100:
        st.success("Total: 100% ✓")
    else:
        st.error(f"Total: {total_pct}% — reduce by {total_pct-100}%.")

    if total_pct > 0:
        hc_rows = []
        for fn in selected_fns:
            hc = round(strategic_population * fn_pcts[fn] / 100)
            hc_rows.append({
                "Function":          fn,
                "% of Strategic Pop": f"{fn_pcts[fn]}%",
                "Headcount":         f"{hc:,}"
            })
        st.dataframe(
            pd.DataFrame(hc_rows),
            use_container_width=True, hide_index=True
        )

    st.markdown("---")
    st.markdown("### 3 — Assessment Mode")

    mode      = st.radio(
        "Choose depth",
        ["Quick Assessment — function level",
         "Deep Dive — role level within each function"],
        key="t1_mode"
    )
    deep_dive = "Deep Dive" in mode

    role_overrides = {}
    if deep_dive:
        st.caption(
            "Default role splits sourced from BLS Occupational Employment and Wage Statistics "
            "(OEWS), May 2023, NAICS Sector 52 — Finance and Insurance. "
            "Adjust percentages below to match your organization's actual distribution."
        )
        for fn in selected_fns:
            fn_hc = round(strategic_population * fn_pcts.get(fn, 0) / 100)
            with st.expander(f"{fn} — {fn_hc:,} people"):
                roles  = get_roles_for_function(fn)
                r_cols = st.columns(len(roles))
                fn_rp  = {}
                for j, role in enumerate(roles):
                    with r_cols[j]:
                        fn_rp[role["soc_code"]] = st.number_input(
                            f"{role['title']} (%)",
                            min_value=0, max_value=100,
                            value=role["default_pct"], step=1,
                            key=f"t1_role_{fn}_{role['soc_code']}"
                        )
                rt = sum(fn_rp.values())
                if rt == 100:
                    st.success("100% ✓")
                else:
                    st.warning(f"{rt}%")
                role_overrides[fn] = fn_rp

    st.markdown("---")

    run = st.button(
        "▶  Run Transformation Analysis",
        use_container_width=True, key="t1_run"
    )

    if not run:
        st.markdown("Configure your organization above and click **▶ Run Transformation Analysis** to see results.")

    if run and total_pct != 100:
        st.error("Function percentages must total 100%.")

    if run and total_pct == 100:
        with st.spinner("Pulling live O*NET data and running analysis..."):
            all_fn_results = []
            avg_wages_list = []

        for fn in selected_fns:
            fn_hc     = round(strategic_population * fn_pcts[fn] / 100)
            overrides = role_overrides.get(fn) if deep_dive else None
            roles     = build_role_list(fn, fn_hc, overrides)

            sizing    = calculate_function_sizing(roles, ai_stage, province)
            decisions = calculate_transfer_options(
                sizing, province, avg_years_service=avg_tenure
            )

            fn_wages    = [get_median_wage(r["soc_code"])[1] for r in roles]
            fn_avg_wage = round(sum(fn_wages)/len(fn_wages)) if fn_wages else 75000
            avg_wages_list.append(fn_avg_wage)

            inaction = legacy_inaction(fn_hc, fn_avg_wage, ai_stage, province)

            all_fn_results.append({
                "function_name":  fn,
                "headcount":      fn_hc,
                "sizing":         sizing,
                "decisions":      decisions,
                "inaction_costs": inaction,
                "avg_wage_cad":   fn_avg_wage,
            })

        priority_index = calculate_priority_index(all_fn_results)
        sequencing     = legacy_sequencing(priority_index)

        total_released       = sum(
            sum(r["headcount_released"] for r in fn["sizing"])
            for fn in all_fn_results
        )
        total_transform_cost = sum(p["transform_cost"] for p in priority_index)
        total_inaction_24    = sum(
            fn["inaction_costs"][1]["total"] for fn in all_fn_results
        )

        # Workforce Resilience Score
        resilience_score, resilience_signals = calculate_resilience_score(
            all_fn_results, avg_tenure
        )

        # ── Results header ────────────────────────────────────────
        st.markdown("---")
        st.markdown("## Transformation Analysis Results")
        st.markdown(
            f"*{industry} | {strategic_population:,} strategic population | "
            f"{ai_stage} | {province} | "
            f"Avg tenure: {avg_tenure} yrs | "
            f"{datetime.today().strftime('%B %d, %Y')}*"
        )

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Strategic Population",      f"{strategic_population:,}")
        m2.metric("Total HC Released",         f"{total_released:,}")
        m3.metric("Transformation Investment", fmt(total_transform_cost))
        m4.metric("Cost of Inaction (24mo)",   fmt(total_inaction_24))
        m5.metric("Resilience Score",          f"{resilience_score} / 100")

        # ── Workforce Resilience Score ────────────────────────────
        st.markdown("---")
        st.markdown("### Workforce Resilience Score")
        st.caption(
            "If 20% of the workforce left tomorrow — "
            "could the organization still operate? "
            "Score 0–100. Higher = more resilient."
        )

        res_col1, res_col2 = st.columns([1, 3])
        with res_col1:
            color = (
                "#28a745" if resilience_score >= 70 else
                "#fd7e14" if resilience_score >= 45 else
                "#dc3545"
            )
            label = (
                "🟢 Resilient"     if resilience_score >= 70 else
                "🟡 Moderate Risk" if resilience_score >= 45 else
                "🔴 Critical Risk"
            )
            st.markdown(
                f'<div style="text-align:center; padding:20px; '
                f'border: 2px solid {color}; border-radius:8px;">'
                f'<h1 style="color:{color}; margin:0;">{resilience_score}</h1>'
                f'<p style="margin:4px 0 0 0; font-weight:600;">{label}</p>'
                f'</div>',
                unsafe_allow_html=True
            )

        with res_col2:
            st.markdown("**Risk Signals:**")
            for signal in resilience_signals:
                st.markdown(f"- {signal}")

        st.markdown(
            '<p class="citation">'
            'Workforce Resilience Score — original methodology by Jaini Desai. '
            '© 2024–2026 Jaini Desai. All rights reserved.'
            '</p>',
            unsafe_allow_html=True
        )

        # ── Priority Index ────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Where to Start — Transformation Priority Index")
        st.caption(
            "Ranked by net ROI. Highest ROI = biggest gap between "
            "cost of inaction and transformation investment. "
            "Cycle 1 savings fund Cycle 2."
        )

        p_rows = []
        for i, p in enumerate(priority_index):
            p_rows.append({
                "Priority":                  i + 1,
                "Function":                  p["function_name"],
                "Avg Automation Rate":       f"{p['avg_automation']*100:.0f}%",
                "HC Today":                  f"{p['headcount_today']:,}",
                "HC Released":               f"{p['headcount_released']:,}",
                "Transformation Investment": fmt(p["transform_cost"]),
                "Cost of Inaction (24mo)":   fmt(p["inaction_24mo"]),
                "Net ROI":                   fmt(p["net_roi"]),
                "Recommendation":            p["label"],
            })
        st.dataframe(
            pd.DataFrame(p_rows),
            use_container_width=True, hide_index=True
        )
        st.markdown(
            f'<p class="citation">'
            f'Automation: <a href="{SOURCES["frey_osborne"]["link"]}" target="_blank">'
            f'Frey & Osborne (2013)</a> / '
            f'<a href="{SOURCES["onet"]["link"]}" target="_blank">O*NET</a> | '
            f'Inaction: <a href="{SOURCES["wef"]["link"]}" target="_blank">'
            f'WEF 2025</a> + '
            f'<a href="{SOURCES["mckinsey"]["link"]}" target="_blank">'
            f'McKinsey 2025</a>'
            f'</p>',
            unsafe_allow_html=True
        )

        # ── Function Summary ──────────────────────────────────────
        st.markdown("---")
        st.markdown("### Function Transformation Summary")

        fn_rows = []
        for fn in all_fn_results:
            sizing   = fn["sizing"]
            hc_today = sum(r["headcount_today"]    for r in sizing)
            hc_tom   = sum(r["headcount_tomorrow"] for r in sizing)
            hc_rel   = sum(r["headcount_released"] for r in sizing)
            gaps     = []
            for d in fn["decisions"]:
                gaps.extend(d.get("skills_gap", []))
            fn_rows.append({
                "Function":        fn["function_name"],
                "HC Today":        f"{hc_today:,}",
                "HC Tomorrow":     f"{hc_tom:,}",
                "HC Released":     f"{hc_rel:,}",
                "Avg Wage":        fmt(fn["avg_wage_cad"]),
                "Top Skills Gap":  gaps[0] if gaps else "No gap identified",
                "Exposure (24mo)": fmt(fn["inaction_costs"][1]["total"]),
            })
        st.dataframe(
            pd.DataFrame(fn_rows),
            use_container_width=True, hide_index=True
        )

        # ── Capability Gap ───────────────────────────────────────
        st.markdown("---")
        st.markdown("### Capability Gap Analysis")
        st.caption(
            "Required capabilities tomorrow vs available today. "
            "Gap drives Build / Buy / Partner recommendation per function."
        )

        for fn in all_fn_results:
            fn_name = fn["function_name"]
            caps    = get_capabilities_for_function(fn_name)

            if not caps:
                continue

            # Summarise Build / Buy / Partner counts for header
            build_count   = sum(1 for c in caps if c["recommendation"].startswith("Build"))
            buy_count     = sum(1 for c in caps if c["recommendation"].startswith("Buy"))
            partner_count = sum(1 for c in caps if c["recommendation"].startswith("Partner"))

            summary_parts = []
            if build_count:
                summary_parts.append(f"Build: {build_count}")
            if buy_count:
                summary_parts.append(f"Buy: {buy_count}")
            if partner_count:
                summary_parts.append(f"Partner: {partner_count}")
            summary_str = " · ".join(summary_parts) if summary_parts else "No gaps identified"

            with st.expander(f"{fn_name} — {summary_str}"):
                cap_rows = []
                for c in caps:
                    gap = c["target_pct"] - c["current_pct"]
                    cap_rows.append({
                        "Capability":     c["capability"],
                        "Current":        f"{c['current_pct']}%",
                        "Target":         f"{c['target_pct']}%",
                        "Gap":            f"{gap}%",
                        "Recommendation": c["recommendation"],
                    })
                st.dataframe(
                    pd.DataFrame(cap_rows),
                    use_container_width=True,
                    hide_index=True
                )

        st.markdown(
            '<p class="citation">'
            'Capability Gap Analysis — Workforce Transformation Intelligence™ | '
            '© 2024–2026 Jaini Desai. All rights reserved.'
            '</p>',
            unsafe_allow_html=True
        )

        # ── Role-Level Detail ─────────────────────────────────────
        st.markdown("---")
        st.markdown("### Role-Level Detail")
        for fn in all_fn_results:
            with st.expander(f"{fn['function_name']} — {fn['headcount']:,} people"):
                r_rows = []
                for r in fn["sizing"]:
                    _, cad, _ = get_median_wage(r["soc_code"])
                    r_rows.append({
                        "Role":            r["title"],
                        "SOC Code":        r["soc_code"],
                        "Median Wage":     fmt(cad),
                        "Automation Rate": f"{r['automation_score']*100:.0f}%",
                        "Transform Type":  r["transform_type"],
                        "HC Today":        f"{r['headcount_today']:,}",
                        "HC Tomorrow":     f"{r['headcount_tomorrow']:,}",
                        "HC Released":     f"{r['headcount_released']:,}",
                    })
                st.dataframe(
                    pd.DataFrame(r_rows),
                    use_container_width=True, hide_index=True
                )

        # ── Reskill / Buy / Augment / Redesign ────────────────────
        st.markdown("---")
        st.markdown("### Transformation Path — Reskill / Buy / Augment / Redesign")
        st.caption(
            "Four paths per released pool. "
            "Work Redesign Engine evaluates whether tasks should be "
            "automated, self-served, centralized, or kept. "
            "Company decides — tool surfaces economics and options only."
        )

        for fn in all_fn_results:
            if not fn["decisions"]:
                continue
            st.markdown(f"**{fn['function_name']}**")

            d_rows = []
            for d in fn["decisions"]:
                best = d.get("best_transfer")
                d_rows.append({
                    "Role Pool":        d["title"],
                    "HC Released":      f"{d['headcount_released']:,}",
                    "Median Wage":      fmt(d["wage_cad"]),
                    "Recommended Path": d["recommended_path"],
                    "Adjacent Role":    best["adjacent_title"] if best else "—",
                    "JZ Gap":           best["job_zone_gap"] if best else "—",
                    "Reskill Time":     f"{best['reskilling_months']} mo" if best else "—",
                    "Reskill Cost":     fmt(best["transfer_cost_total"]) if best else "—",
                    "Prod Drag":        fmt(
                        best["productivity_drag_per_person"] *
                        d["headcount_released"]
                    ) if best else "—",
                    "Severance":        fmt(
                        d["severance_per_person"] * d["headcount_released"]
                    ),
                    "Replacement":      fmt(
                        d["replacement_per_person"] * d["headcount_released"]
                    ),
                    "Exit Cost":        fmt(d["exit_cost_total"]),
                    "Net Saving":       fmt(d["net_saving_if_transfer"]) if best else "—",
                })

            st.dataframe(
                pd.DataFrame(d_rows),
                use_container_width=True, hide_index=True
            )

            # Reasoning + Work Redesign per pool
            for d in fn["decisions"]:
                best = d.get("best_transfer")
                path = d["recommended_path"]

                if path == "Augment":
                    r = (
                        f"<b>{d['title']}</b> — Augment. "
                        f"Automation {d['automation_score']*100:.0f}%. "
                        f"Role survives. Skills gap: "
                        f"{', '.join(d['skills_gap'][:3]) if d['skills_gap'] else 'none'}."
                    )
                    st.markdown(
                        f'<div class="reasoning-box">{r}</div>',
                        unsafe_allow_html=True
                    )
                elif path == "Transfer & Reskill" and best:
                    r = (
                        f"<b>{d['title']}</b> — Reskill & Transfer. "
                        f"JZ gap {best['job_zone_gap']} → {best['adjacent_title']} "
                        f"({'Bright Outlook ✓' if best['bright_outlook'] else 'stable'}). "
                        f"{best['reskilling_months']} months. "
                        f"Saves {fmt(d['net_saving_if_transfer'])} vs exit."
                    )
                    st.markdown(
                        f'<div class="reasoning-box">{r}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    r = (
                        f"<b>{d['title']}</b> — Buy. "
                        f"JZ gap too large. "
                        f"Severance {fmt(d['severance_per_person'])}/person "
                        f"({d['severance_law']}). "
                        f"Replace at {fmt(d['replacement_per_person'])}/person."
                    )
                    st.markdown(
                        f'<div class="reasoning-box">{r}</div>',
                        unsafe_allow_html=True
                    )

                # Work Redesign Engine output
                auto_score = d.get("automation_score", 0.50)
                redesign_path, redesign_desc = get_work_redesign_path(auto_score)
                st.markdown(
                    f'<div class="redesign-box">'
                    f'<b>Work Redesign Engine — {d["title"]}:</b> '
                    f'{redesign_path} — {redesign_desc}. '
                    f'Automation rate {auto_score*100:.0f}% suggests this work '
                    f'{"can be fully automated — eliminate the role category" if auto_score >= 0.85 else "is a strong candidate for self-service or shared services" if auto_score >= 0.45 else "requires human judgment — redesign the role, do not eliminate it"}.'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.markdown(
                f'<p class="citation">'
                f'Reskilling: <a href="{SOURCES["deloitte"]["link"]}" target="_blank">'
                f'Deloitte 2026</a> | '
                f'Drag: <a href="{SOURCES["mckinsey"]["link"]}" target="_blank">'
                f'McKinsey 2025</a> | '
                f'Replacement: <a href="{SOURCES["shrm"]["link"]}" target="_blank">'
                f'SHRM 2024</a> | '
                f'Severance: {province} — approx based on {avg_tenure} yr avg tenure | '
                f'Work Redesign Engine © Jaini Desai 2024'
                f'</p>',
                unsafe_allow_html=True
            )

        st.markdown("""
    <div class="boundary-note">
    <strong>On individual decisions:</strong> Which employees to reskill vs exit
    is an internal decision based on your organization's performance data,
    learning agility assessments, and manager input. The above reflects
    population-level economics only. Your HR and legal teams must calculate
    precise individual severance obligations before any action is taken.
    </div>
    """, unsafe_allow_html=True)

        # ── 0-36 Month Timeline ───────────────────────────────────
        st.markdown("---")
        st.markdown("### 0–36 Month Cost Timeline")
        st.caption("When each dollar lands.")

        tl_rows = []
        for fn in all_fn_results:
            aug_hc  = sum(
                r["headcount_today"] for r in fn["sizing"]
                if r["transform_type"] == "Augmented"
            )
            tr_hc   = sum(
                r["headcount_released"] for r in fn["sizing"]
                if r["transform_type"] == "Transformed"
            )
            ex_hc   = sum(
                r["headcount_released"] for r in fn["sizing"]
                if r["transform_type"] == "Eliminated"
            )
            ex_cost = sum(
                d["exit_cost_total"] for d in fn["decisions"]
                if d["recommended_path"] != "Transfer & Reskill"
            )
            tl_rows.append({
                "Function":                   fn["function_name"],
                "0–6 mo: Augmentation":       fmt(aug_hc * 3500),
                "HC Augmented":               f"{aug_hc:,}",
                "6–18 mo: Reskilling":        fmt(tr_hc * 8500),
                "6–18 mo: Productivity Drag": fmt(round(tr_hc * fn["avg_wage_cad"] * 0.23)),
                "HC Reskilling":              f"{tr_hc:,}",
                "18–36 mo: Exit + Replace":   fmt(ex_cost),
                "HC Exited":                  f"{ex_hc:,}",
            })
        st.dataframe(
            pd.DataFrame(tl_rows),
            use_container_width=True, hide_index=True
        )

        # ── Skills Gap ────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Skills Gap by Role")

        sg_rows = []
        for fn in all_fn_results:
            for d in fn["decisions"]:
                sg_rows.append({
                    "Function":          fn["function_name"],
                    "Role":              d["title"],
                    "Today's Skills":    ", ".join(d["today_skills"][:4])    or "—",
                    "Tomorrow's Skills": ", ".join(d["tomorrow_skills"][:4]) or "—",
                    "Skills Gap":        ", ".join(d["skills_gap"][:4])      or "No gap",
                })
        if sg_rows:
            st.dataframe(
                pd.DataFrame(sg_rows),
                use_container_width=True, hide_index=True
            )
            st.markdown(
                f'<p class="citation">'
                f'Source: <a href="{SOURCES["onet"]["link"]}" target="_blank">'
                f'O*NET Technology Skills + Hot Technology endpoints</a>'
                f'</p>',
                unsafe_allow_html=True
            )

        # ── Cost of Inaction ──────────────────────────────────────
        st.markdown("---")
        st.markdown("### Cost of Inaction")
        st.caption("What it costs to do nothing as AI adoption continues.")

        ci_rows = []
        for fn in all_fn_results:
            for ic in fn["inaction_costs"]:
                ci_rows.append({
                    "Function":            fn["function_name"],
                    "Timeframe":           f"{ic['months']} months",
                    "Skills Obsolescence": fmt(ic["obs_cost"]),
                    "Productivity Drag":   fmt(ic["productivity_cost"]),
                    "Salary Waste":        fmt(ic["salary_waste"]),
                    "Total":               fmt(ic["total"]),
                })
        st.dataframe(
            pd.DataFrame(ci_rows),
            use_container_width=True, hide_index=True
        )
        st.markdown(
            f'<p class="citation">'
            f'Skills obsolescence 39%: <a href="{SOURCES["wef"]["link"]}" target="_blank">'
            f'WEF Future of Jobs 2025</a> | '
            f'Productivity drag 23%: <a href="{SOURCES["mckinsey"]["link"]}" target="_blank">'
            f'McKinsey State of AI 2025</a>'
            f'</p>',
            unsafe_allow_html=True
        )

        # ── Self-Funding Sequencing ───────────────────────────────
        st.markdown("---")
        st.markdown("### Self-Funding Transformation Sequencing")
        st.caption("Cycle 1 savings fund Cycle 2. Additional capital after Cycle 1: $0.")

        seq_rows = []
        for s in sequencing:
            seq_rows.append({
                "Cycle":               s["cycle"],
                "Function":            s["function"],
                "Investment Required": fmt(s["investment"]),
                "Net Saving":          fmt(s["net_saving"]),
                "Cumulative Saving":   fmt(s["cumulative_saving"]),
                "Funded By":           s["funded_by"],
            })
        st.dataframe(
            pd.DataFrame(seq_rows),
            use_container_width=True, hide_index=True
        )

        nav_bar()

# ═══════════════════════════════════════════════════════════════
# TAB 2 — OPTIMIZATION MODEL
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Optimization Model")
    st.caption(
        "Function-level PuLP optimization. "
        "Two filters: Domain Transferability (DWA overlap ≥ 30%) "
        "and Technical Gap (Job Zone gap ≤ 2). "
        "Results shown as Low / Mid / High ranges."
    )

    st.markdown("#### Configure")
    o_col1, o_col2, o_col3 = st.columns(3)

    with o_col1:
        o_country = st.selectbox(
            "Country", ["Canada", "United States"], key="o_country"
        )
        o_fn = st.selectbox(
            "Select Function to Optimize",
            get_function_names(), key="o_fn"
        )

    with o_col2:
        if o_country == "Canada":
            o_province = st.selectbox("Province", [
                "Federal (Banks & Telecoms)", "Ontario",
                "British Columbia", "Quebec", "Alberta",
            ], key="o_province")
        else:
            o_province = "United States"
            st.info("🇺🇸 WARN Act applies.")

        o_ai = st.selectbox("AI Adoption Stage", [
            "Early (Exploring)", "Active (Piloting)", "Advanced (Scaling)",
        ], key="o_ai")

    with o_col3:
        o_hc = st.number_input(
            "Function Headcount",
            min_value=10, max_value=50000,
            value=500, step=10, key="o_hc"
        )
        o_tenure = st.number_input(
            "Average Tenure (years)",
            min_value=1, max_value=30,
            value=6, step=1, key="o_tenure"
        )
        o_budget = st.number_input(
            "Reskilling Budget (0 = no constraint)",
            min_value=0, max_value=50000000,
            value=0, step=50000, key="o_budget"
        )

    st.markdown("#### Role Distribution")
    st.caption("Adjust % per role. Must total 100%.")

    o_roles_config = get_roles_for_function(o_fn)
    o_role_cols    = st.columns(len(o_roles_config))
    o_role_pcts    = {}

    for j, role in enumerate(o_roles_config):
        with o_role_cols[j]:
            o_role_pcts[role["soc_code"]] = st.number_input(
                f"{role['title']} (%)",
                min_value=0, max_value=100,
                value=role["default_pct"], step=1,
                key=f"o_role_{role['soc_code']}"
            )

    o_role_total = sum(o_role_pcts.values())
    if o_role_total == 100:
        st.success("100% ✓")
    else:
        st.warning(f"Total: {o_role_total}%")

    o_scenario = st.radio(
        "Cost scenario",
        ["low", "mid", "high"],
        index=1, horizontal=True, key="o_scenario"
    )

    o_run = st.button(
        "▶  Run Optimization",
        use_container_width=True, key="o_run"
    )

    if o_run and o_role_total == 100:
        with st.spinner(f"Running PuLP optimization for {o_fn}..."):
            o_roles = []
            for role in o_roles_config:
                soc       = role["soc_code"]
                hc        = round(o_hc * o_role_pcts[soc] / 100)
                _, cad, _ = get_median_wage(soc)
                o_roles.append({
                    "soc_code":  soc,
                    "title":     role["title"],
                    "headcount": hc,
                    "salary":    cad,
                })

            result = optimize_function(
                o_fn, o_roles,
                o_country, o_province,
                o_ai, o_tenure,
                budget=o_budget if o_budget > 0 else None,
                scenario=o_scenario
            )

        st.markdown("---")
        st.markdown(f"### {o_fn} — Transformation Strategy")
        st.info(result["declaration"])

        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Total HC",          f"{result['total_hc']:,}")
        s2.metric("HC Released",       f"{result['total_released']:,}")
        s3.metric("Transformable",     f"{result['transformable']:,}")
        s4.metric("Optimized Reskill", f"{result['optimized_reskill']:,}")
        s5.metric("Optimized Exit",    f"{result['optimized_exit']:,}")

        st.markdown("---")
        st.markdown("#### Role-Level Optimization Results")
        st.caption(
            f"Scenario: **{o_scenario.upper()}** | "
            f"Optimizer: {'PuLP CBC' if result['optimizer_used'] else 'Rule-based fallback'}"
        )

        for r in result["role_analyses"]:
            with st.expander(
                f"{r['title']} — {r['headcount']:,} people | "
                f"{r['transform_type']} | Released: {r['hc_released']:,}"
            ):
                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown("**Transformation Profile**")
                    st.write(f"Automation Rate: {r['auto_score']*100:.0f}%")
                    st.write(f"Transform Type: {r['transform_type']}")
                    st.write(f"HC Today: {r['headcount']:,}")
                    st.write(f"HC Tomorrow: {r['hc_tomorrow']:,}")
                    st.write(f"HC Released: {r['hc_released']:,}")
                    st.write(f"Recommendation: {r['recommendation']}")

                    if r.get("optimizer_used") is not None:
                        st.markdown("**Optimized Allocation**")
                        st.write(f"Reskill: {r.get('optimized_reskill', 0):,}")
                        st.write(f"Exit: {r.get('optimized_exit', 0):,}")
                        st.write(f"Augment: {r.get('optimized_augment', 0):,}")

                    # Work Redesign
                    redesign_path, redesign_desc = get_work_redesign_path(
                        r.get("auto_score", 0.5)
                    )
                    st.markdown("**Work Redesign Recommendation**")
                    st.write(f"{redesign_path} — {redesign_desc}")

                with col_b:
                    best = r.get("best_transfer")
                    if best:
                        st.markdown("**Best Transfer Option**")
                        st.write(f"Target: {best['target_title']}")
                        st.write(
                            f"Bright Outlook: "
                            f"{'✅' if best['bright_outlook'] else '—'}"
                        )
                        st.write(
                            f"Domain Transfer: "
                            f"{best['domain']['overlap_score']:.0%} — "
                            f"{best['domain']['signal']}"
                        )
                        st.write(
                            f"Technical Gap: JZ {best['tech']['jz_gap']} — "
                            f"{best['tech']['signal']}"
                        )

                        costs = best["costs"]
                        st.markdown("**Cost Range (Low / Mid / High)**")
                        st.write(
                            f"Reskill: {range_str(costs['reskill']['cost_low'], costs['reskill']['cost_mid'], costs['reskill']['cost_high'])}"
                        )
                        st.write(
                            f"Exit: {range_str(costs['exit']['total_low'], costs['exit']['total_mid'], costs['exit']['total_high'])}"
                        )
                        st.write(
                            f"Net saving: {range_str(costs['net_saving']['low'], costs['net_saving']['mid'], costs['net_saving']['high'])}"
                        )

                        drag = costs["reskill"]["drag"]
                        if drag["method"] == "task_level" and drag["breakdown"]:
                            st.markdown("**Task-Level Productivity Drag**")
                            drag_rows = []
                            for db in drag["breakdown"][:5]:
                                drag_rows.append({
                                    "Skill":      db["skill"],
                                    "% of Job":   f"{db['pct_of_job']}%",
                                    "Drag (Mid)": fmt(db["drag_mid"]),
                                })
                            st.dataframe(
                                pd.DataFrame(drag_rows),
                                use_container_width=True,
                                hide_index=True
                            )
                    else:
                        st.markdown("**No feasible transfer option**")
                        st.write(
                            "Domain gap too wide or technical gap too large. "
                            "Exit & Buy recommended."
                        )

        st.markdown("""
<div class="boundary-note">
<strong>Optimization declaration:</strong>
This optimization runs at function level — all released roles optimized
simultaneously. PuLP solver minimizes total transformation cost subject
to domain transferability, technical gap, and budget constraints.
</div>
""", unsafe_allow_html=True)

    nav_bar()

# ═══════════════════════════════════════════════════════════════
# TAB 3 — CUSTOM CALCULATOR
# ═══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Custom Calculator")
    st.caption(
        "Three modes: Upload a spreadsheet, build by function, "
        "or assess one individual. ELV and LMI are optional."
    )

    calc_mode = st.radio(
        "Input mode",
        [
            "📥 Upload spreadsheet (CSV)",
            "🏗️ Build by function",
            "👤 Individual assessment",
        ],
        key="calc_mode"
    )

    template_csv = """# Workforce Transformation Intelligence™ — Data Template
# © 2024–2026 Jaini Desai. All rights reserved.
# masked_id: sequential numbers only — no real employee IDs, names, or PII
# salary: annual in local currency — leave blank to use O*NET median
# performance/engagement/learning_agility: High, Medium, or Low
# is_leadership: Yes or No
# province: Federal, Ontario, BC, Quebec, Alberta (Canada) or blank (US)
masked_id,function,role_title,tenure_years,province,salary,performance,engagement,learning_agility,is_leadership
1,Finance & Accounting,Financial Analysts,8,Ontario,112000,High,Medium,High,No
2,HR & People Operations,Benefits & Compensation Specialists,3,Federal,64000,Medium,High,High,No
3,Technology & Engineering,Software Developers,5,Ontario,124000,High,High,Medium,No
4,Risk & Compliance,Compliance Officers,12,Federal,95000,High,Medium,Medium,Yes
5,Finance & Accounting,Bookkeeping & Accounting Clerks,4,Ontario,52000,Medium,Medium,Low,No
"""

    st.download_button(
        label="📥 Download CSV Template",
        data=template_csv,
        file_name="wti_data_template.csv",
        mime="text/csv",
        key="dl_template"
    )
    st.caption(
        "Download → fill in Excel or Google Sheets → upload back. "
        "Use masked_id only — sequential numbers. "
        "No names, no employee IDs, no personal identifiers."
    )

    st.markdown("---")

    with st.expander("📋 Standard Function & Role Reference"):
        ref_rows = []
        for fn in get_function_names():
            for role in get_roles_for_function(fn):
                ref_rows.append({
                    "Function":   fn,
                    "Role Title": role["title"],
                    "SOC Code":   role["soc_code"],
                })
        st.dataframe(
            pd.DataFrame(ref_rows),
            use_container_width=True, hide_index=True
        )

    st.markdown("---")

    # ── MODE A: UPLOAD ────────────────────────────────────────
    if "Upload" in calc_mode:
        st.markdown("#### Upload Your Data")
        st.info(
            "🔒 Privacy: Data is processed in-session only. "
            "Nothing stored or transmitted. "
            "Use masked IDs only."
        )

        upload_type = st.radio(
            "Data type",
            ["Raw (one row per employee)",
             "Aggregated (one row per role)"],
            key="upload_type"
        )

        uploaded = st.file_uploader(
            "Upload CSV", type=["csv"], key="csv_upload"
        )

        if uploaded:
            try:
                df = pd.read_csv(uploaded, comment="#")
                st.success(f"✅ Loaded {len(df)} rows")
                st.dataframe(df.head(10),
                             use_container_width=True, hide_index=True)

                role_map = {}
                for fn in get_function_names():
                    for role in get_roles_for_function(fn):
                        role_map[role["title"].lower()] = {
                            "soc_code": role["soc_code"],
                            "function": fn,
                            "title":    role["title"],
                        }

                df["role_lower"] = df["role_title"].str.lower().str.strip()
                df["soc_code"]   = df["role_lower"].map(
                    lambda x: role_map.get(x, {}).get("soc_code", "UNKNOWN")
                )
                unmapped = df[df["soc_code"] == "UNKNOWN"]["role_title"].unique()

                if len(unmapped) > 0:
                    st.warning(
                        f"Could not map: {list(unmapped)}. "
                        f"Check spelling against reference table."
                    )

                mapped = df[df["soc_code"] != "UNKNOWN"]

                if len(mapped) == 0:
                    st.error("No rows mapped. Check role titles.")
                else:
                    st.success(f"✅ {len(mapped)} rows mapped to O*NET")

                    has_optional = all(
                        c in df.columns
                        for c in ["performance", "engagement", "learning_agility"]
                    )

                    results_rows = []
                    for _, row in mapped.iterrows():
                        soc         = row["soc_code"]
                        _, cad, _   = get_median_wage(soc)
                        salary      = float(row.get("salary", cad) or cad)
                        tenure      = float(row.get("tenure_years", 6) or 6)
                        prov        = str(
                            row.get("province", "Federal (Banks & Telecoms)")
                            or "Federal (Banks & Telecoms)"
                        )
                        country_row = "Canada" if prov != "United States" else "United States"
                        auto, _     = get_automation_score(soc)
                        weekly      = salary / 52
                        sev         = calculate_severance(
                            country_row, prov, tenure, weekly
                        )

                        result_row = {
                            "masked_id":  row.get("masked_id", "—"),
                            "function":   row.get("function", "—"),
                            "role_title": row["role_title"],
                            "soc_code":   soc,
                            "salary":     fmt(salary),
                            "tenure_yrs": tenure,
                            "automation": f"{auto*100:.0f}%",
                            "sev_low":    fmt(sev["low"]),
                            "sev_mid":    fmt(sev["mid"]),
                            "sev_high":   fmt(sev["high"]),
                        }

                        if has_optional:
                            related   = get_related_occupations(soc)
                            bright    = [r for r in related if r["bright_outlook"]]
                            best_t    = bright[0] if bright else (
                                related[0] if related else None
                            )
                            adjacency = 0.0
                            if best_t:
                                adjacency = get_dwa_overlap_score(
                                    soc, best_t["soc_code"]
                                )
                            elv = calculate_elv(
                                performance=str(row.get("performance", "Medium")),
                                engagement=str(row.get("engagement", "Medium")),
                                learning_agility=str(
                                    row.get("learning_agility", "Medium")
                                ),
                                skill_adjacency=adjacency,
                                tenure_years=tenure,
                                annual_salary=salary,
                                reskilling_cost_mid=BENCHMARKS["reskilling_cost"]["mid"],
                            )
                            result_row["elv_score"]     = elv["elv_score"]
                            result_row["rough_diamond"] = (
                                "⭐" if elv["rough_diamond"] else ""
                            )

                        results_rows.append(result_row)

                    st.markdown("#### Results")
                    st.dataframe(
                        pd.DataFrame(results_rows),
                        use_container_width=True,
                        hide_index=True
                    )

                    if has_optional:
                        st.markdown(
                            '<p class="citation">'
                            'ELV™ — Employee Lifetime Value™ — '
                            'Original framework by Jaini Desai (2024). '
                            '© 2024–2026 Jaini Desai.'
                            '</p>',
                            unsafe_allow_html=True
                        )

            except Exception as e:
                st.error(f"Error reading CSV: {e}")

    # ── MODE B: FUNCTION BUILDER ──────────────────────────────
    elif "Build" in calc_mode:
        st.markdown("#### Build by Function")

        b_country = st.selectbox(
            "Country", ["Canada", "United States"], key="b_country"
        )
        b_fn = st.selectbox(
            "Select Function", get_function_names(), key="b_fn"
        )

        if b_country == "Canada":
            b_province = st.selectbox("Province", [
                "Federal (Banks & Telecoms)", "Ontario",
                "British Columbia", "Quebec", "Alberta",
            ], key="b_province")
        else:
            b_province = "United States"

        b_tenure = st.number_input(
            "Average Tenure (years)",
            min_value=1, max_value=30,
            value=6, step=1, key="b_tenure"
        )

        st.markdown(f"**Roles in {b_fn}**")
        st.caption("Pre-populated from O*NET.")

        b_roles_config = get_roles_for_function(b_fn)
        b_role_data    = []

        for role in b_roles_config:
            soc       = role["soc_code"]
            _, cad, _ = get_median_wage(soc)
            auto, _   = get_automation_score(soc)
            jz        = get_job_zone(soc)

            with st.expander(
                f"{role['title']} — SOC {soc} | "
                f"JZ {jz} | Auto {auto*100:.0f}% | "
                f"O*NET: {fmt(cad)}/yr"
            ):
                bc1, bc2, bc3 = st.columns(3)
                with bc1:
                    hc = st.number_input(
                        "Headcount", min_value=0, max_value=10000,
                        value=0, step=1, key=f"b_hc_{soc}"
                    )
                    sal = st.number_input(
                        f"Avg Salary (0 = O*NET median)",
                        min_value=0, max_value=1000000,
                        value=0, step=1000, key=f"b_sal_{soc}"
                    )
                with bc2:
                    perf = st.selectbox(
                        "Avg Performance (optional)",
                        ["—", "High", "Medium", "Low"],
                        key=f"b_perf_{soc}"
                    )
                    eng = st.selectbox(
                        "Avg Engagement (optional)",
                        ["—", "High", "Medium", "Low"],
                        key=f"b_eng_{soc}"
                    )
                with bc3:
                    agility = st.selectbox(
                        "Avg Learning Agility (optional)",
                        ["—", "High", "Medium", "Low"],
                        key=f"b_agility_{soc}"
                    )
                    is_lead = st.selectbox(
                        "Leadership roles?",
                        ["No", "Yes"],
                        key=f"b_lead_{soc}"
                    )

                b_role_data.append({
                    "soc_code":  soc,
                    "title":     role["title"],
                    "headcount": hc,
                    "salary":    sal if sal > 0 else cad,
                    "perf":      None if perf == "—" else perf,
                    "eng":       None if eng  == "—" else eng,
                    "agility":   None if agility == "—" else agility,
                    "is_lead":   is_lead == "Yes",
                    "jz":        jz,
                    "auto":      auto,
                })

        b_run = st.button(
            "▶  Calculate", use_container_width=True, key="b_run"
        )

        if b_run:
            active = [r for r in b_role_data if r["headcount"] > 0]
            if not active:
                st.warning("Enter headcount for at least one role.")
            else:
                with st.spinner("Calculating..."):
                    b_results = []
                    for r in active:
                        auto   = r["auto"]
                        hc     = r["headcount"]
                        salary = r["salary"]
                        weekly = salary / 52

                        if auto >= 0.70:
                            transform = "Eliminated"
                            hc_rel    = hc
                        elif auto >= 0.40:
                            transform = "Transformed"
                            hc_rel    = round(hc * auto)
                        else:
                            transform = "Augmented"
                            hc_rel    = 0

                        sev = calculate_severance(
                            b_country, b_province, b_tenure, weekly
                        )

                        redesign_path, redesign_desc = get_work_redesign_path(auto)

                        elv_score     = None
                        rough_diamond = False
                        if all(x is not None for x in [r["perf"], r["eng"], r["agility"]]):
                            related = get_related_occupations(r["soc_code"])
                            bright  = [x for x in related if x["bright_outlook"]]
                            best_t  = bright[0] if bright else (
                                related[0] if related else None
                            )
                            adj = 0.0
                            if best_t:
                                adj = get_dwa_overlap_score(
                                    r["soc_code"], best_t["soc_code"]
                                )
                            elv = calculate_elv(
                                r["perf"], r["eng"], r["agility"],
                                adj, b_tenure, salary,
                                BENCHMARKS["reskilling_cost"]["mid"]
                            )
                            elv_score     = elv["elv_score"]
                            rough_diamond = elv["rough_diamond"]

                        row = {
                            "Role":           r["title"],
                            "HC":             hc,
                            "Transform":      transform,
                            "HC Released":    hc_rel,
                            "Salary":         fmt(salary),
                            "Work Redesign":  redesign_path,
                            "Sev Low":        fmt(sev["low"]  * hc_rel),
                            "Sev Mid":        fmt(sev["mid"]  * hc_rel),
                            "Sev High":       fmt(sev["high"] * hc_rel),
                            "Repl Low":       fmt(salary * 1.5 * hc_rel),
                            "Repl Mid":       fmt(salary * 2.0 * hc_rel),
                            "Repl High":      fmt(salary * 3.0 * hc_rel),
                        }
                        if elv_score is not None:
                            row["ELV Score"]     = elv_score
                            row["Rough Diamond"] = "⭐" if rough_diamond else ""

                        b_results.append(row)

                st.markdown("#### Results")
                st.dataframe(
                    pd.DataFrame(b_results),
                    use_container_width=True,
                    hide_index=True
                )

    # ── MODE C: INDIVIDUAL ────────────────────────────────────
    elif "Individual" in calc_mode:
        st.markdown("#### Individual Assessment")

        i_col1, i_col2 = st.columns(2)

        with i_col1:
            i_country = st.selectbox(
                "Country", ["Canada", "United States"], key="i_country"
            )
            i_fn    = st.selectbox(
                "Function", get_function_names(), key="i_fn"
            )
            i_roles = get_roles_for_function(i_fn)
            i_role  = st.selectbox(
                "Role",
                options=[r["title"] for r in i_roles],
                key="i_role"
            )
            i_soc     = next(
                r["soc_code"] for r in i_roles if r["title"] == i_role
            )
            _, i_cad, _ = get_median_wage(i_soc)
            i_salary = st.number_input(
                f"Annual Salary (O*NET median: {fmt(i_cad)})",
                min_value=0, max_value=1000000,
                value=int(i_cad), step=1000, key="i_salary"
            )
            if i_country == "Canada":
                i_province = st.selectbox("Province", [
                    "Federal (Banks & Telecoms)", "Ontario",
                    "British Columbia", "Quebec", "Alberta",
                ], key="i_province")
            else:
                i_province = "United States"

            i_tenure = st.number_input(
                "Tenure (years)",
                min_value=0, max_value=40,
                value=6, step=1, key="i_tenure"
            )

        with i_col2:
            st.markdown("**Optional — unlocks ELV™**")
            i_perf    = st.selectbox(
                "Performance", ["—", "High", "Medium", "Low"], key="i_perf"
            )
            i_eng     = st.selectbox(
                "Engagement (EME)", ["—", "High", "Medium", "Low"], key="i_eng"
            )
            i_agility = st.selectbox(
                "Learning Agility", ["—", "High", "Medium", "Low"], key="i_agility"
            )

            st.markdown("**Optional — unlocks LMI™ (leadership only)**")
            i_is_lead = st.selectbox(
                "Leadership role?", ["No", "Yes"], key="i_is_lead"
            )

            if i_is_lead == "Yes":
                i_goal    = st.selectbox("Goal Achievement",        ["High","Medium","Low"], key="i_goal")
                i_teng    = st.selectbox("Team Engagement",         ["High","Medium","Low"], key="i_teng")
                i_cons    = st.selectbox("Leadership Consistency",  ["High","Medium","Low"], key="i_cons")
                i_succ    = st.selectbox("Succession Depth",
                    ["Strong pipeline","Partial","No successor"], key="i_succ")
                i_stk     = st.selectbox("Stakeholder Influence",   ["High","Medium","Low"], key="i_stk")
                i_adapt   = st.selectbox("Change Adaptability",     ["High","Medium","Low"], key="i_adapt")
                i_team_sz = st.number_input(
                    "Team Size", min_value=1, max_value=500,
                    value=10, step=1, key="i_team_sz"
                )
                i_team_sal = st.number_input(
                    "Avg Team Salary",
                    min_value=0, max_value=500000,
                    value=75000, step=1000, key="i_team_sal"
                )

        i_run = st.button(
            "▶  Calculate Individual Assessment",
            use_container_width=True, key="i_run"
        )

        if i_run:
            with st.spinner("Running assessment..."):
                auto, _  = get_automation_score(i_soc)
                jz       = get_job_zone(i_soc)
                weekly   = i_salary / 52

                sev = calculate_severance(
                    i_country, i_province, i_tenure, weekly
                )

                related = get_related_occupations(i_soc)
                bright  = [r for r in related if r["bright_outlook"]]
                best_t  = bright[0] if bright else (
                    related[0] if related else None
                )
                adj = 0.0
                if best_t:
                    adj = get_dwa_overlap_score(i_soc, best_t["soc_code"])

                resk_mid  = BENCHMARKS["reskilling_cost"]["mid"]
                redesign_path, redesign_desc = get_work_redesign_path(auto)

            st.markdown("---")
            st.markdown(f"### Assessment: {i_role}")

            r1, r2, r3, r4, r5 = st.columns(5)
            r1.metric("Automation Risk", f"{auto*100:.0f}%")
            r2.metric("Job Zone",        jz)
            r3.metric("Annual Salary",   fmt(i_salary))
            r4.metric("Tenure",          f"{i_tenure} years")
            r5.metric("Work Redesign",   redesign_path)

            st.markdown("#### Severance if Exited (Low / Mid / High)")
            sv1, sv2, sv3 = st.columns(3)
            sv1.metric("Low (legislative min)",  fmt(sev["low"]))
            sv2.metric("Mid (2 wks/yr policy)",  fmt(sev["mid"]))
            sv3.metric("High (3 wks/yr policy)", fmt(sev["high"]))
            st.caption(
                f"{sev['law']} — [View legislation]({sev['link']}) | "
                f"{sev['note']}"
            )

            st.markdown("#### Replacement Cost (Low / Mid / High)")
            rp1, rp2, rp3 = st.columns(3)
            rp1.metric("Low (1.5×)", fmt(i_salary * 1.5))
            rp2.metric("Mid (2×)",   fmt(i_salary * 2.0))
            rp3.metric("High (3×)",  fmt(i_salary * 3.0))

            if best_t:
                st.markdown("#### Best Transfer Option (O*NET)")
                t1, t2, t3 = st.columns(3)
                t1.metric("Adjacent Role",  best_t["title"])
                t2.metric("Domain Overlap", f"{adj:.0%}")
                t3.metric("Bright Outlook", "✅" if best_t["bright_outlook"] else "—")

            if all(x != "—" for x in [i_perf, i_eng, i_agility]):
                elv = calculate_elv(
                    i_perf, i_eng, i_agility,
                    adj, i_tenure, i_salary, resk_mid
                )
                st.markdown("#### Employee Lifetime Value™ (ELV)")
                e1, e2, e3 = st.columns(3)
                e1.metric("ELV Score",            f"{elv['elv_score']} / 100")
                e2.metric("Composite Performance", f"{elv['composite_perf']:.0f}")
                e3.metric("Skill Adjacency",       f"{elv['adjacency']:.0f}")

                if elv["rough_diamond"]:
                    st.success(
                        "⭐ Rough Diamond — Low/Medium performance + "
                        "High learning agility. Priority reskilling candidate."
                    )
                st.markdown(
                    '<p class="citation">'
                    'Employee Lifetime Value™ — Jaini Desai (2024). '
                    '© 2024–2026 Jaini Desai.'
                    '</p>',
                    unsafe_allow_html=True
                )

            if i_is_lead == "Yes":
                lmi = calculate_lmi(
                    i_goal, i_teng, i_cons, i_succ,
                    i_stk, i_adapt, i_team_sz, i_team_sal
                )
                st.markdown("#### Leadership Momentum Index™ (LMI)")
                l1, l2, l3 = st.columns(3)
                l1.metric("LMI Score",        f"{lmi['lmi_score']} / 100")
                l2.metric("Retention Signal",  lmi["retention_signal"])
                l3.metric("Cascade Cost",      fmt(lmi["cascade_cost"]))

                st.markdown("**Dimension Scores**")
                dim_rows = [
                    {"Dimension": k, "Score": v}
                    for k, v in lmi["dimension_scores"].items()
                ]
                st.dataframe(
                    pd.DataFrame(dim_rows),
                    use_container_width=True, hide_index=True
                )

                if lmi["succession_risk"]:
                    st.error(
                        "⚠️ Succession Risk — No ready successor. "
                        "Exit creates immediate pipeline gap."
                    )

                st.markdown(
                    f'<p class="citation">'
                    f'Cascade: <a href="{SOURCES["cross_borgatti"]["link"]}" target="_blank">'
                    f'Cross, Borgatti & Parker (2.3×)</a> | '
                    f'LMI™ — Jaini Desai (2024). © 2024–2026 Jaini Desai.'
                    f'</p>',
                    unsafe_allow_html=True
                )
                st.caption(lmi["optional_note"])

    nav_bar()

# ═══════════════════════════════════════════════════════════════
# TAB 4 — REFERENCE & GLOSSARY
# ═══════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### Reference & Glossary")
    st.caption("Plain language explanations of every concept in this platform.")

    with st.expander("📘 What is ELV™ — Employee Lifetime Value?"):
        st.markdown("""
**Employee Lifetime Value™ (ELV)**
*Original framework by Jaini Desai (2024)*

ELV measures the total economic and organizational value an employee contributes
over their remaining tenure — net of the cost to retain or reskill them.

**Formula:**
ELV = Performance Score × Skill Adjacency Score × Net Contribution Period − Retraining Cost

**Output:** ELV score normalized 0–100.
*© 2024–2026 Jaini Desai. All rights reserved.*
        """)

    with st.expander("📘 What is LMI™ — Leadership Momentum Index?"):
        st.markdown("""
**Leadership Momentum Index™ (LMI)**
*Original framework by Jaini Desai (2024)*

Measures leadership effectiveness across six dimensions:
1. Goal Achievement
2. Team Engagement
3. Leadership Consistency
4. Succession Depth
5. Stakeholder Influence
6. Change Adaptability

**Cascade Cost:** Team Size × Avg Team Salary × 2.3
**LMI is optional.** If not provided, all other calculations unchanged.
*© 2024–2026 Jaini Desai. All rights reserved.*
        """)

    with st.expander("📘 Work Redesign Engine"):
        st.markdown("""
**Work Redesign Engine**
*Original methodology by Jaini Desai*

For each released role pool, evaluates five work redesign paths:

- 🤖 **Automate** (≥85% automation) — AI or software handles entirely
- 🔄 **Self-service** (65–85%) — employee or customer performs directly
- 🏢 **Shared Services** (45–65%) — centralize across the organization
- 📦 **Centralize** (25–45%) — pool with similar work, reduce duplication
- ✅ **Keep** (<25%) — human judgment required, retain in role

This is the question transformation consultants charge millions to answer.
The platform generates it automatically from O*NET automation data.
*© 2024–2026 Jaini Desai. All rights reserved.*
        """)

    with st.expander("📘 Workforce Resilience Score"):
        st.markdown("""
**Workforce Resilience Score**
*Original methodology by Jaini Desai*

Single number 0–100. Answers: if 20% of the workforce left tomorrow,
could the organization still operate?

Five components:
1. Automation exposure (lower = more resilient)
2. Transferability (higher internal transfer options = more resilient)
3. Skill redundancy (more functions covered = more resilient)
4. Tenure stability (longer average tenure = more resilient)
5. HC retained ratio (more retained = more resilient)

*© 2024–2026 Jaini Desai. All rights reserved.*
        """)

    with st.expander("📘 Broken Pipeline Principle"):
        st.markdown("""
**Broken Pipeline Principle** — *Jaini Desai*

*"Workforce transformation without pipeline strategy is just delayed organizational damage."*
        """)

    with st.expander("📘 Rough Diamond Framework"):
        st.markdown("""
**Rough Diamond Framework** — *Jaini Desai*

Low performance + High learning agility = most valuable junior employee
for transformation investment. Undervalued today. High-value tomorrow.
        """)

    with st.expander("📘 Domain Transferability"):
        st.markdown(f"""
**Domain Transferability** — Source: [O*NET]({SOURCES["onet"]["link"]})

% of target role's DWAs present in current role.
≥60% = strong | 30–60% = moderate | <30% = domain gap, Buy recommended.
Threshold: 30% minimum to be transformable.
        """)

    with st.expander("📘 Job Zone"):
        st.markdown(f"""
**Job Zone** — Source: [O*NET]({SOURCES["onet"]["link"]})

| Zone | Preparation |
|---|---|
| 1 | Little or none |
| 2 | Up to 1 year |
| 3 | 1–2 years |
| 4 | 4+ years |
| 5 | Advanced degree + experience |

Gap ≤ 2 = reskill feasible. Gap ≥ 3 = Buy recommended.
        """)

    with st.expander("📘 Cost of Inaction"):
        st.markdown(f"""
**Cost of Inaction**

Three components:
1. Skills obsolescence — 39% by 2028 ([WEF 2025]({SOURCES["wef"]["link"]}))
2. Productivity drag ([McKinsey 2025]({SOURCES["mckinsey"]["link"]}))
3. Salary waste — paying for automated work

Shown Low / Mid / High at 12, 24, 36 months.
        """)

    with st.expander("📘 Self-Funding Sequencing"):
        st.markdown("""
**Self-Funding Transformation Sequencing** — *Jaini Desai*

Start highest ROI first. Cycle 1 savings fund Cycle 2.
Zero additional capital after Cycle 1.
        """)

    nav_bar()

# ═══════════════════════════════════════════════════════════════
# TAB 5 — HOW IT WORKS
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### How It Works — Worked Example")
    st.caption(
        "Select a role. Step-by-step walkthrough of every calculation. "
        "Every number cited. Every source linked. "
        "Methodology shown. Algorithms not exposed."
    )

    st.markdown(
        '<div class="boundary-note">'
        '<strong>IP Protection Note:</strong> '
        'This example demonstrates the analytical approach for transparency. '
        'The optimization methodology, ELV™, LMI™, Work Redesign Engine, '
        'Workforce Resilience Score, and all calculation logic are proprietary '
        'intellectual property of Jaini Desai (2024–2026). '
        'Reproduction without written permission is prohibited.'
        '</div>',
        unsafe_allow_html=True
    )

    we_fn    = st.selectbox("Select Function", get_function_names(), key="we_fn")
    we_roles = get_roles_for_function(we_fn)
    we_role  = st.selectbox(
        "Select Role", [r["title"] for r in we_roles], key="we_role"
    )
    we_soc   = next(r["soc_code"] for r in we_roles if r["title"] == we_role)

    we_run = st.button(
        "▶  Show Worked Example", use_container_width=True, key="we_run"
    )

    if we_run:
        with st.spinner(f"Pulling O*NET data for {we_role}..."):
            _, we_cad, _   = get_median_wage(we_soc)
            we_jz          = get_job_zone(we_soc)
            we_auto, _     = get_automation_score(we_soc)
            we_tasks       = get_tasks(we_soc)
            we_today       = get_technology_skills(we_soc)
            we_hot         = get_hot_technology(we_soc)
            we_related     = get_related_occupations(we_soc)
            we_tomorrow    = [h["title"] for h in we_hot]
            we_gap         = [h["title"] for h in we_hot if h["title"] not in we_today]
            we_bright      = [r for r in we_related if r["bright_outlook"]]

        st.markdown("---")
        st.markdown(f"## Worked Example: {we_role}")

        st.markdown("### Step 1 — What is this role?")
        s1c1, s1c2, s1c3, s1c4 = st.columns(4)
        s1c1.metric("SOC Code",         we_soc)
        s1c2.metric("Job Zone",          f"{we_jz} / 5")
        s1c3.metric("Median Wage (USD)", f"${int(we_cad/1.36):,}")
        s1c4.metric("Median Wage (CAD)", f"${we_cad:,}")
        st.markdown(
            f'<p class="citation">'
            f'<a href="{SOURCES["onet"]["link"]}" target="_blank">O*NET BLS</a> → '
            f'<a href="{SOURCES["boc"]["link"]}" target="_blank">Bank of Canada</a> '
            f'(1 USD = 1.36 CAD, June 10 2026)'
            f'</p>',
            unsafe_allow_html=True
        )

        st.markdown("### Step 2 — What does this person do?")
        if we_tasks:
            task_rows = []
            for t in we_tasks[:15]:
                status = (
                    "🔴 Released"    if we_auto >= 0.70 else
                    "🟡 Transformed" if we_auto >= 0.40 else
                    "✅ Retained"
                )
                task_rows.append({
                    "Task":           t.get("title", ""),
                    "Auto Risk":      f"{we_auto*100:.0f}%",
                    "Status":         status,
                })
            st.dataframe(
                pd.DataFrame(task_rows),
                use_container_width=True, hide_index=True
            )

        st.markdown("### Step 3 — Skills today vs tomorrow")
        sk1, sk2, sk3 = st.columns(3)
        sk1.markdown("**Today**")
        sk1.write(", ".join(we_today[:6]) or "—")
        sk2.markdown("**Tomorrow (Hot Tech)**")
        sk2.write(", ".join(we_tomorrow[:6]) or "—")
        sk3.markdown("**Gap**")
        sk3.write(", ".join(we_gap[:6]) or "No gap")

        st.markdown("### Step 4 — Work Redesign")
        redesign_path, redesign_desc = get_work_redesign_path(we_auto)
        st.markdown(
            f'<div class="redesign-box">'
            f'<b>Work Redesign Recommendation:</b> {redesign_path} — {redesign_desc}. '
            f'Automation rate {we_auto*100:.0f}%.'
            f'</div>',
            unsafe_allow_html=True
        )

        st.markdown("### Step 5 — Is this person transformable?")
        if we_bright:
            target  = we_bright[0]
            t_soc   = target["soc_code"]
            t_title = target["title"]
            t_jz    = get_job_zone(t_soc)
            jz_gap  = max(t_jz - we_jz, 0)
            overlap = get_dwa_overlap_score(we_soc, t_soc)

            f1c1, f1c2 = st.columns(2)
            with f1c1:
                st.markdown("**Filter 1 — Domain Transferability**")
                st.write(f"Target: {t_title}")
                st.write(f"DWA overlap: {overlap:.0%}")
                st.write(
                    f"{'✅ Transferable' if overlap >= 0.30 else '❌ Domain gap too wide'}"
                )
            with f1c2:
                st.markdown("**Filter 2 — Technical Gap**")
                st.write(f"Current JZ: {we_jz} → Target JZ: {t_jz}")
                st.write(f"Gap: {jz_gap}")
                st.write(
                    f"{'✅ Feasible' if jz_gap <= 2 else '❌ Buy recommended'}"
                )

            st.markdown("### Step 6 — What does it cost?")
            months_mid = JZ_GAP_TO_MONTHS.get(min(jz_gap, 2), {}).get("mid", 6)
            resk_cost  = RESKILLING_BY_JZ.get(t_jz, RESKILLING_BY_JZ[3])
            drag       = calculate_task_level_drag(we_soc, we_cad, months_mid)
            _, t_cad, _ = get_median_wage(t_soc)
            sev_ex     = calculate_severance("Canada", "Federal", 6, we_cad/52)

            st.markdown("**Reskill Path (Low / Mid / High)**")
            resk_rows = [
                {
                    "Component": "Reskilling investment",
                    "Low": fmt(resk_cost["low"]),
                    "Mid": fmt(resk_cost["mid"]),
                    "High": fmt(resk_cost["high"]),
                    "Source": "Deloitte 2026",
                },
                {
                    "Component": f"Productivity drag ({months_mid} mo)",
                    "Low": fmt(drag["total_low"]),
                    "Mid": fmt(drag["total_mid"]),
                    "High": fmt(drag["total_high"]),
                    "Source": "O*NET task % × salary",
                },
                {
                    "Component": "Total per person",
                    "Low": fmt(resk_cost["low"]  + drag["total_low"]),
                    "Mid": fmt(resk_cost["mid"]  + drag["total_mid"]),
                    "High": fmt(resk_cost["high"] + drag["total_high"]),
                    "Source": "Combined",
                },
            ]
            st.dataframe(
                pd.DataFrame(resk_rows),
                use_container_width=True, hide_index=True
            )

            st.markdown("**Exit Path (Low / Mid / High)**")
            exit_rows = [
                {
                    "Component": "Severance (6yr, Federal)",
                    "Low": fmt(sev_ex["low"]),
                    "Mid": fmt(sev_ex["mid"]),
                    "High": fmt(sev_ex["high"]),
                    "Source": "Canada Labour Code",
                },
                {
                    "Component": f"Replacement ({t_title})",
                    "Low": fmt(t_cad * 1.5),
                    "Mid": fmt(t_cad * 2.0),
                    "High": fmt(t_cad * 3.0),
                    "Source": "SHRM 2024",
                },
                {
                    "Component": "Total per person",
                    "Low": fmt(sev_ex["low"]  + t_cad * 1.5),
                    "Mid": fmt(sev_ex["mid"]  + t_cad * 2.0),
                    "High": fmt(sev_ex["high"] + t_cad * 3.0),
                    "Source": "Combined",
                },
            ]
            st.dataframe(
                pd.DataFrame(exit_rows),
                use_container_width=True, hide_index=True
            )

            net_mid = (
                (sev_ex["mid"] + t_cad * 2.0) -
                (resk_cost["mid"] + drag["total_mid"])
            )
            st.markdown(
                f'<div class="reasoning-box">'
                f'<b>Net saving if reskill vs exit (Mid): {fmt(net_mid)}</b><br>'
                f'Reskilling saves {fmt(net_mid)} per person vs exiting '
                f'and replacing with a {t_title}.'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("No Bright Outlook adjacent roles found. Exit & Buy may apply.")

        st.markdown("""
<div class="boundary-note">
This example shows the analytical reasoning only. The optimization engine,
ELV™, LMI™, Work Redesign Engine, Workforce Resilience Score, and all
calculation logic are proprietary IP of Jaini Desai (2024–2026).
</div>
""", unsafe_allow_html=True)

    nav_bar()

# ═══════════════════════════════════════════════════════════════
# TAB 6 — METHODOLOGY & SOURCES
# ═══════════════════════════════════════════════════════════════
with tab6:
    st.markdown("### Methodology & Sources")
    st.caption(
        "Every number traceable to a named source. "
        "Click any link to verify directly."
    )

    citations = [
        {
            "Data Point": "Automation probabilities",
            "Value":      "Per SOC code (0.02–0.99)",
            "Source":     "Frey & Osborne (2013) / O*NET",
            "Link":       SOURCES["frey_osborne"]["link"],
            "Formula":    "base_score × AI_multiplier × province_modifier",
        },
        {
            "Data Point": "Reskilling cost",
            "Value":      "$6,500 — $8,500 — $15,000",
            "Source":     "Deloitte 2026 Global Human Capital Trends",
            "Link":       SOURCES["deloitte"]["link"],
            "Formula":    "Varies by target Job Zone",
        },
        {
            "Data Point": "Productivity drag",
            "Value":      "10% — 23% — 35%",
            "Source":     "McKinsey State of AI 2025",
            "Link":       SOURCES["mckinsey"]["link"],
            "Formula":    "salary × skill_pct × months/12 (task-level)",
        },
        {
            "Data Point": "Skills obsolescence",
            "Value":      "39% by 2028",
            "Source":     "WEF Future of Jobs Report 2025",
            "Link":       SOURCES["wef"]["link"],
            "Formula":    "pop × 0.39 × AI_mult × province_mod × years",
        },
        {
            "Data Point": "Replacement cost",
            "Value":      "1.5× — 2× — 3× salary",
            "Source":     "SHRM Workforce Benchmark 2024",
            "Link":       SOURCES["shrm"]["link"],
            "Formula":    "median_wage × multiplier",
        },
        {
            "Data Point": "Occupation data",
            "Value":      "Per SOC code — live API",
            "Source":     "O*NET Web Services — U.S. Dept of Labor",
            "Link":       SOURCES["onet"]["link"],
            "Formula":    "Direct API pull",
        },
        {
            "Data Point": "Wage conversion (USD → CAD)",
            "Value":      "1 USD = 1.36 CAD (June 10, 2026)",
            "Source":     "Bank of Canada",
            "Link":       SOURCES["boc"]["link"],
            "Formula":    "onet_wage_usd × 1.36",
        },
        {
            "Data Point": "Severance — Federal Canada",
            "Value":      "Canada Labour Code",
            "Source":     "Canada Labour Code — R.S.C. 1985, c. L-2",
            "Link":       SOURCES["canada_labour_code"]["link"],
            "Formula":    "Legislative min + company policy range",
        },
        {
            "Data Point": "Severance — Ontario",
            "Value":      "Ontario ESA 2000",
            "Source":     "Ontario Employment Standards Act 2000",
            "Link":       SOURCES["ontario_esa"]["link"],
            "Formula":    "Legislative min + company policy range",
        },
        {
            "Data Point": "Severance — BC",
            "Value":      "BC ESA",
            "Source":     "BC Employment Standards Act — RSBC 1996",
            "Link":       SOURCES["bc_esa"]["link"],
            "Formula":    "Legislative min + company policy range",
        },
        {
            "Data Point": "Severance — Quebec",
            "Value":      "Quebec Labour Standards",
            "Source":     "Quebec Act Respecting Labour Standards",
            "Link":       SOURCES["quebec_lsa"]["link"],
            "Formula":    "Legislative min + company policy range",
        },
        {
            "Data Point": "Severance — Alberta",
            "Value":      "Alberta ESC",
            "Source":     "Alberta Employment Standards Code",
            "Link":       SOURCES["alberta_esc"]["link"],
            "Formula":    "Legislative min + company policy range",
        },
        {
            "Data Point": "Severance — United States",
            "Value":      "WARN Act only",
            "Source":     "WARN Act (1988)",
            "Link":       SOURCES["warn_act"]["link"],
            "Formula":    "60 days pay if qualifying layoff",
        },
        {
            "Data Point": "Cascade cost multiplier",
            "Value":      "2.3×",
            "Source":     "Cross, Borgatti & Parker",
            "Link":       SOURCES["cross_borgatti"]["link"],
            "Formula":    "team_size × avg_team_salary × 2.3",
        },
        {
            "Data Point": "Employee Lifetime Value™ (ELV)",
            "Value":      "Score 0–100",
            "Source":     "Jaini Desai (2024)",
            "Link":       "https://www.linkedin.com/in/jainidesai",
            "Formula":    "Performance × Adjacency × Net Contribution − Retraining",
        },
        {
            "Data Point": "Leadership Momentum Index™ (LMI)",
            "Value":      "Score 0–100",
            "Source":     "Jaini Desai (2024)",
            "Link":       "https://www.linkedin.com/in/jainidesai",
            "Formula":    "Weighted average of 6 dimensions",
        },
        {
            "Data Point": "Work Redesign Engine",
            "Value":      "5 redesign paths per role",
            "Source":     "Jaini Desai (2024) — original methodology",
            "Link":       "https://www.linkedin.com/in/jainidesai",
            "Formula":    "Automation rate → Automate / Self-service / Shared / Centralize / Keep",
        },
        {
            "Data Point": "Workforce Resilience Score",
            "Value":      "Score 0–100",
            "Source":     "Jaini Desai (2024) — original methodology",
            "Link":       "https://www.linkedin.com/in/jainidesai",
            "Formula":    "Composite of 5 resilience dimensions",
        },
    ]

    for c in citations:
        with st.expander(f"{c['Data Point']} — {c['Value']}"):
            st.markdown(f"**Source:** [{c['Source']}]({c['Link']})")
            st.markdown(f"**Formula:** `{c['Formula']}`")

    st.markdown("---")
    st.markdown("### Full Citations Table")
    cite_df = pd.DataFrame([
        {
            "Data Point": c["Data Point"],
            "Value":      c["Value"],
            "Source":     c["Source"],
            "Formula":    c["Formula"],
        }
        for c in citations
    ])
    st.dataframe(cite_df, use_container_width=True, hide_index=True)

    nav_bar()

# ── Footer ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray; font-size:12px;'>"
    "Workforce Transformation Intelligence™ | "
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

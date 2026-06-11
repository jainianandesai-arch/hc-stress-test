import pandas as pd
import numpy as np
from datetime import datetime

np.random.seed(42)

df = pd.read_csv('workforce_15k.csv')

print("=" * 60)
print("  HUMAN CAPITAL STRESS TEST ENGINE")
print("  Confidential — Board Risk Report")
print(f"  Run date: {datetime.today().strftime('%B %d, %Y')}")
print("=" * 60)

# ── SCENARIO 1: AI Displacement Shock ──────────────────────
print("\n📌 SCENARIO 1: AI Displacement Shock")
print("   Assumption: 30% of automatable roles eliminated over 18 months\n")

displaced = df[df['ai_displacement_score'] >= 0.60].copy()
total_displaced = int(len(displaced) * 0.30)
salary_cost_displaced = displaced.nlargest(total_displaced, 'salary')['salary'].sum()

# Monte Carlo — recovery timeline
simulations = []
for _ in range(1000):
    monthly_hire_capacity = np.random.normal(45, 8)
    months_to_recover = total_displaced / monthly_hire_capacity
    simulations.append(months_to_recover)

s1_mean = np.mean(simulations)
s1_p10 = np.percentile(simulations, 10)
s1_p90 = np.percentile(simulations, 90)

dept_exposure = df.groupby('department')['ai_displacement_score'].mean().sort_values(ascending=False)

print(f"   Employees at high displacement risk:     {len(displaced):,}")
print(f"   Estimated roles eliminated (30%):        {total_displaced:,}")
print(f"   Annual salary exposure:                  ${salary_cost_displaced:,.0f}")
print(f"   Recovery timeline (median):              {s1_mean:.1f} months")
print(f"   Recovery range (10th-90th percentile):  {s1_p10:.1f} – {s1_p90:.1f} months")
print(f"\n   Most exposed departments:")
for dept, score in dept_exposure.head(3).items():
    print(f"   ⚠️  {dept}: {score:.2f} avg displacement score")

# ── SCENARIO 2: Leadership Exodus ──────────────────────────
print("\n📌 SCENARIO 2: Leadership Exodus")
print("   Assumption: 40% of Director+ leave within 12 months\n")

leaders = df[df['level'].isin(['Director', 'VP', 'C-Suite'])].copy()
exodus_count = int(len(leaders) * 0.40)
top_performers_lost = leaders[leaders['performance_tier'].isin(['Exceeds', 'Top'])]
exodus_salary = leaders.nlargest(exodus_count, 'salary')['salary'].sum()

# Knowledge loss score — tenure weighted
knowledge_loss = (leaders['tenure_years'] * leaders['salary']).sum() / 1_000_000

# Monte Carlo — org stability
stability_sims = []
for _ in range(1000):
    cascade_factor = np.random.normal(2.3, 0.4)
    total_impact = exodus_count * cascade_factor
    stability_sims.append(total_impact)

s2_cascade_mean = np.mean(stability_sims)
s2_cascade_p90 = np.percentile(stability_sims, 90)

print(f"   Total Director+ population:              {len(leaders):,}")
print(f"   Estimated exodus (40%):                  {exodus_count:,}")
print(f"   Top performers at risk:                  {len(top_performers_lost):,}")
print(f"   Salary exposure (replacement cost 2x):  ${exodus_salary * 2:,.0f}")
print(f"   Institutional knowledge loss index:      {knowledge_loss:.1f}M")
print(f"   Cascade effect (roles impacted):         {s2_cascade_mean:.0f} avg / {s2_cascade_p90:.0f} worst case")

# ── SCENARIO 3: Skills Obsolescence Wave ───────────────────
print("\n📌 SCENARIO 3: Skills Obsolescence Wave")
print("   Assumption: 60% of current skills become less relevant by 2028\n")

AT_RISK_SKILLS = [
    'Excel Advanced', 'Process Automation', 'Compliance',
    'Financial Modelling', 'SQL', 'Risk Assessment'
]

def count_at_risk(skills_str):
    if pd.isna(skills_str):
        return 0
    skills = [s.strip() for s in skills_str.split(',')]
    return sum(1 for s in skills if s in AT_RISK_SKILLS)

df['at_risk_skill_count'] = df['skills'].apply(count_at_risk)
high_obsolescence = df[df['at_risk_skill_count'] >= 2]
reskilling_cost_per_person = 8500

total_reskilling_cost = len(high_obsolescence) * reskilling_cost_per_person
critical_gap_depts = df.groupby('department')['at_risk_skill_count'].mean().sort_values(ascending=False)

# Monte Carlo — productivity loss
productivity_sims = []
for _ in range(1000):
    productivity_drop = np.random.normal(0.23, 0.05)
    recovery_months = np.random.normal(14, 3)
    productivity_sims.append((productivity_drop, recovery_months))

avg_prod_drop = np.mean([x[0] for x in productivity_sims])
avg_recovery = np.mean([x[1] for x in productivity_sims])

print(f"   Employees with 2+ at-risk skills:        {len(high_obsolescence):,}")
print(f"   % of total workforce:                    {len(high_obsolescence)/len(df)*100:.1f}%")
print(f"   Estimated reskilling investment:         ${total_reskilling_cost:,.0f}")
print(f"   Avg productivity drop during transition: {avg_prod_drop*100:.1f}%")
print(f"   Estimated recovery timeline:             {avg_recovery:.1f} months")
print(f"\n   Departments with highest skill gap:")
for dept, score in critical_gap_depts.head(3).items():
    print(f"   ⚠️  {dept}: {score:.2f} avg at-risk skills per employee")

# ── COMPOSITE RISK RATING ───────────────────────────────────
print("\n" + "=" * 60)
print("  COMPOSITE HUMAN CAPITAL RISK RATING")
print("=" * 60)

s1_rating = "🔴 CRITICAL" if total_displaced > 1000 else "🟡 ELEVATED"
s2_rating = "🔴 CRITICAL" if exodus_count > 200 else "🟡 ELEVATED"
s3_rating = "🔴 CRITICAL" if len(high_obsolescence)/len(df) > 0.30 else "🟡 ELEVATED"

print(f"\n   Scenario 1 — AI Displacement:    {s1_rating}")
print(f"   Scenario 2 — Leadership Exodus:  {s2_rating}")
print(f"   Scenario 3 — Skills Obsolescence:{s3_rating}")

total_financial_exposure = salary_cost_displaced + (exodus_salary * 2) + total_reskilling_cost
print(f"\n   💰 TOTAL FINANCIAL EXPOSURE:     ${total_financial_exposure:,.0f}")
print(f"\n   ⚡ RECOMMENDED IMMEDIATE ACTIONS:")
print(f"   1. Ring-fence top performers in high-displacement depts")
print(f"   2. Activate succession plans for Director+ roles NOW")
print(f"   3. Launch reskilling for {len(high_obsolescence):,} employees before 2027")
print("\n" + "=" * 60)

# Save results
results = {
    'scenario': ['AI Displacement', 'Leadership Exodus', 'Skills Obsolescence'],
    'employees_at_risk': [total_displaced, exodus_count, len(high_obsolescence)],
    'financial_exposure': [salary_cost_displaced, exodus_salary*2, total_reskilling_cost],
    'recovery_months': [s1_mean, 12, avg_recovery],
    'risk_rating': ['CRITICAL', 'CRITICAL', 'CRITICAL']
}
results_df = pd.DataFrame(results)
results_df.to_csv('stress_test_results.csv', index=False)
print("\n✅ Results saved to stress_test_results.csv")

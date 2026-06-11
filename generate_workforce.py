import pandas as pd
import numpy as np
from faker import Faker
import random

fake = Faker()
np.random.seed(42)
random.seed(42)

# ── Configuration ──────────────────────────────────────────
N = 15000

DEPARTMENTS = {
    'Technology': 0.18,
    'Operations': 0.22,
    'Finance & Risk': 0.15,
    'Compliance & Legal': 0.08,
    'Human Resources': 0.07,
    'Customer Experience': 0.14,
    'Strategy & Analytics': 0.06,
    'Sales & Distribution': 0.10,
}

LEVELS = ['Analyst', 'Senior Analyst', 'Manager', 
          'Senior Manager', 'Director', 'VP', 'C-Suite']

LEVEL_WEIGHTS = [0.28, 0.24, 0.20, 0.14, 0.08, 0.05, 0.01]

# AI displacement vulnerability by department (0-1 scale)
# Based on O*NET automation probability research
AI_VULNERABILITY = {
    'Technology': 0.35,
    'Operations': 0.72,
    'Finance & Risk': 0.61,
    'Compliance & Legal': 0.45,
    'Human Resources': 0.38,
    'Customer Experience': 0.58,
    'Strategy & Analytics': 0.29,
    'Sales & Distribution': 0.54,
}

SALARY_BANDS = {
    'Analyst': (55000, 75000),
    'Senior Analyst': (75000, 100000),
    'Manager': (100000, 135000),
    'Senior Manager': (135000, 170000),
    'Director': (170000, 220000),
    'VP': (220000, 320000),
    'C-Suite': (320000, 600000),
}

SKILLS_POOL = [
    'Data Analysis', 'Python', 'SQL', 'Machine Learning',
    'Project Management', 'Stakeholder Communication',
    'Risk Assessment', 'Financial Modelling', 'Compliance',
    'Process Automation', 'Power BI', 'Excel Advanced',
    'Change Management', 'Agile', 'Cloud Computing',
    'Natural Language Processing', 'Strategic Planning',
]

# ── Generate Workforce ──────────────────────────────────────
records = []

dept_list = list(DEPARTMENTS.keys())
dept_weights = list(DEPARTMENTS.values())

for i in range(N):
    dept = random.choices(dept_list, weights=dept_weights)[0]
    level = random.choices(LEVELS, weights=LEVEL_WEIGHTS)[0]
    tenure = round(np.random.exponential(scale=4.5), 1)
    tenure = min(tenure, 35)
    
    salary_min, salary_max = SALARY_BANDS[level]
    salary = int(np.random.uniform(salary_min, salary_max))
    
    performance = random.choices(
        ['Low', 'Developing', 'Meets', 'Exceeds', 'Top'],
        weights=[0.05, 0.15, 0.45, 0.25, 0.10]
    )[0]
    
    # Flight risk: higher for top performers + low tenure
    base_flight_risk = np.random.beta(2, 5)
    if performance in ['Exceeds', 'Top']:
        base_flight_risk *= 1.4
    if tenure < 2:
        base_flight_risk *= 1.6
    flight_risk = min(round(base_flight_risk, 2), 1.0)
    
    # AI displacement score
    dept_vuln = AI_VULNERABILITY[dept]
    ai_score = round(np.random.normal(dept_vuln, 0.12), 2)
    ai_score = max(0.05, min(0.95, ai_score))
    
    # Skills (2-5 per employee)
    num_skills = random.randint(2, 5)
    skills = ', '.join(random.sample(SKILLS_POOL, num_skills))
    
    # Manager ID (everyone except C-Suite has one)
    manager_id = f"EMP{random.randint(1000, 9999)}" if level != 'C-Suite' else None
    
    records.append({
        'employee_id': f"EMP{10000 + i}",
        'department': dept,
        'level': level,
        'tenure_years': tenure,
        'salary': salary,
        'performance_tier': performance,
        'flight_risk_score': flight_risk,
        'ai_displacement_score': ai_score,
        'skills': skills,
        'manager_id': manager_id,
        'employment_type': random.choices(
            ['FTE', 'Contract'], weights=[0.85, 0.15])[0],
        'location': random.choices(
            ['Toronto', 'Vancouver', 'Montreal', 'Calgary', 'Remote'],
            weights=[0.35, 0.20, 0.18, 0.12, 0.15])[0],
    })

df = pd.DataFrame(records)
df.to_csv('workforce_15k.csv', index=False)

print(f"✅ Workforce generated: {len(df)} employees")
print(f"\n📊 Department breakdown:")
print(df['department'].value_counts())
print(f"\n🎯 Level breakdown:")
print(df['level'].value_counts())
print(f"\n⚠️  Avg AI displacement score: {df['ai_displacement_score'].mean():.2f}")
print(f"🚨 High flight risk (>0.6): {(df['flight_risk_score'] > 0.6).sum()} employees")
print(f"\n✅ Saved to workforce_15k.csv")
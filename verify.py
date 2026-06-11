import pandas as pd
df = pd.read_csv('workforce_15k.csv')
print(f"Total employees: {len(df)}")
print(df.head())

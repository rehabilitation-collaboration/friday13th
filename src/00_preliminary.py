"""
Preliminary analysis: Friday the 13th accident counts
- Identify all Friday-13ths in 2019-2024
- Compare accident counts: Friday-13th vs other Fridays
- Basic descriptive statistics
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "fullmoon-accident" / "data" / "processed"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load data
df = pd.read_parquet(DATA_DIR / "accidents_clean.parquet")
df["date"] = df["occurred_at"].dt.date
df["date"] = pd.to_datetime(df["date"])
df["day"] = df["date"].dt.day
df["dow"] = df["date"].dt.dayofweek  # 0=Mon, 4=Fri
df["month"] = df["date"].dt.month
df["year"] = df["date"].dt.year

# Daily accident counts
daily = df.groupby("date").agg(
    total=("record_key", "count"),
    fatal=("fatality_count", "sum"),
    injury=("injury_count", "sum"),
).reset_index()
daily["day"] = daily["date"].dt.day
daily["dow"] = daily["date"].dt.dayofweek
daily["month"] = daily["date"].dt.month
daily["year"] = daily["date"].dt.year
daily["is_friday"] = daily["dow"] == 4
daily["is_13th"] = daily["day"] == 13
daily["is_friday13"] = daily["is_friday"] & daily["is_13th"]

# --- 1. List all Friday-13ths ---
fri13_dates = daily[daily["is_friday13"]].sort_values("date")
print("=" * 60)
print("1. ALL FRIDAY THE 13THS (2019-2024)")
print("=" * 60)
for _, row in fri13_dates.iterrows():
    print(f"  {row['date'].strftime('%Y-%m-%d')} : {row['total']:,} accidents, {row['fatal']:.0f} fatal")
print(f"\n  Total: {len(fri13_dates)} Friday-13ths")

# --- 2. Friday-13th vs Other Fridays ---
fridays = daily[daily["is_friday"]].copy()
print("\n" + "=" * 60)
print("2. FRIDAY THE 13TH vs OTHER FRIDAYS")
print("=" * 60)

fri13 = fridays[fridays["is_friday13"]]
other_fri = fridays[~fridays["is_friday13"]]

print(f"\n  Friday 13th (n={len(fri13)}):")
print(f"    Mean daily accidents: {fri13['total'].mean():.1f} (SD={fri13['total'].std():.1f})")
print(f"    Range: {fri13['total'].min()} - {fri13['total'].max()}")
print(f"    Mean fatal: {fri13['fatal'].mean():.2f}")

print(f"\n  Other Fridays (n={len(other_fri)}):")
print(f"    Mean daily accidents: {other_fri['total'].mean():.1f} (SD={other_fri['total'].std():.1f})")
print(f"    Range: {other_fri['total'].min()} - {other_fri['total'].max()}")
print(f"    Mean fatal: {other_fri['fatal'].mean():.2f}")

# Rate ratio
rr = fri13['total'].mean() / other_fri['total'].mean()
print(f"\n  Rate Ratio (Fri13/OtherFri): {rr:.4f}")
print(f"  Difference: {fri13['total'].mean() - other_fri['total'].mean():+.1f} accidents/day")

# --- 3. Case-crossover style: same-month Fridays ---
print("\n" + "=" * 60)
print("3. CASE-CROSSOVER: FRIDAY 13TH vs SAME-MONTH OTHER FRIDAYS")
print("=" * 60)

results = []
for _, fri13_row in fri13_dates.iterrows():
    m, y = fri13_row["month"], fri13_row["year"]
    same_month_fri = fridays[(fridays["month"] == m) & (fridays["year"] == y)]
    control_fri = same_month_fri[~same_month_fri["is_friday13"]]
    results.append({
        "date": fri13_row["date"].strftime("%Y-%m-%d"),
        "fri13_count": fri13_row["total"],
        "control_mean": control_fri["total"].mean(),
        "control_n": len(control_fri),
        "ratio": fri13_row["total"] / control_fri["total"].mean(),
    })

results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))
print(f"\n  Overall mean ratio: {results_df['ratio'].mean():.4f}")
print(f"  Ratios > 1.0: {(results_df['ratio'] > 1).sum()} / {len(results_df)}")

# --- 4. Day-of-month analysis: 6th vs 13th vs 20th vs 27th ---
print("\n" + "=" * 60)
print("4. COMPARISON: 6TH vs 13TH vs 20TH vs 27TH (FRIDAYS ONLY)")
print("=" * 60)

for day_num in [6, 13, 20, 27]:
    subset = fridays[fridays["day"] == day_num]
    print(f"  {day_num}th (n={len(subset)}): mean={subset['total'].mean():.1f}, SD={subset['total'].std():.1f}")

# --- 5. Day-of-week comparison for 13th ---
print("\n" + "=" * 60)
print("5. 13TH OF MONTH BY DAY OF WEEK")
print("=" * 60)

thirteens = daily[daily["is_13th"]]
dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
for dow in range(7):
    subset = thirteens[thirteens["dow"] == dow]
    print(f"  {dow_names[dow]:3s} (n={len(subset):2d}): mean={subset['total'].mean():.1f}, SD={subset['total'].std():.1f}")

# --- 6. Simple t-test ---
from scipy import stats
print("\n" + "=" * 60)
print("6. STATISTICAL TESTS")
print("=" * 60)

t_stat, p_val = stats.ttest_ind(fri13["total"], other_fri["total"])
print(f"  Independent t-test (Fri13 vs Other Fri): t={t_stat:.3f}, p={p_val:.4f}")

# Mann-Whitney U (non-parametric)
u_stat, p_mw = stats.mannwhitneyu(fri13["total"], other_fri["total"], alternative="two-sided")
print(f"  Mann-Whitney U: U={u_stat:.0f}, p={p_mw:.4f}")

# Negative binomial would need more setup - save for main analysis

# --- 7. Power analysis ---
print("\n" + "=" * 60)
print("7. POWER ANALYSIS")
print("=" * 60)

n_fri13 = len(fri13)
n_other = len(other_fri)
pooled_std = fridays["total"].std()
mean_other = other_fri["total"].mean()

# Detectable effect size at 80% power, alpha=0.05
# Using approximation: d = (z_alpha + z_beta) * sqrt(1/n1 + 1/n2)
from scipy.stats import norm
z_alpha = norm.ppf(0.975)  # two-sided
z_beta = norm.ppf(0.80)
min_detectable_diff = (z_alpha + z_beta) * pooled_std * np.sqrt(1/n_fri13 + 1/n_other)
print(f"  n(Fri13)={n_fri13}, n(OtherFri)={n_other}")
print(f"  Pooled SD: {pooled_std:.1f}")
print(f"  Min detectable difference (80% power, alpha=0.05): {min_detectable_diff:.1f} accidents/day")
print(f"  As % of mean: {min_detectable_diff/mean_other*100:.1f}%")

# Scanlon found +52% (65 vs 45). Can we detect that?
scanlon_effect = mean_other * 0.52
print(f"\n  Scanlon-level effect (+52%): {scanlon_effect:.0f} additional accidents/day")
print(f"  Detectable? {'YES' if scanlon_effect > min_detectable_diff else 'NO'}")

# Save summary
results_df.to_csv(OUTPUT_DIR / "preliminary_friday13.csv", index=False)
print(f"\n  Results saved to {OUTPUT_DIR / 'preliminary_friday13.csv'}")

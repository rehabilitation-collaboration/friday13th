"""02_main_analysis.py
Phase 2A: 先行研究手法の再現 + Phase 2B: 独自分析

A. 先行研究再現:
  - Scanlon法: 13日金曜 vs 6日金曜 (paired t-test)
  - Nayha法: 負の二項回帰 (曜日+月+年+金曜13日ダミー), 年齢層別
  - Lo法: 6日 vs 13日 vs 20日 vs 27日 金曜 (ANOVA + post-hoc)

B. 独自分析:
  - Case-crossover: 同月内他金曜を対照とした条件付きロジスティック回帰
  - 負の二項回帰 (天候・祝日・季節を共変量に追加)
  - サブグループ: 重症度別、時間帯別、年齢層別
  - 感度分析: COVID除外、お盆・年末年始除外
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import NegativeBinomial

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load_daily():
    return pd.read_parquet(DATA_DIR / "daily_accidents.parquet")

def load_severity():
    return pd.read_parquet(DATA_DIR / "daily_by_severity.parquet")

def load_age():
    return pd.read_parquet(DATA_DIR / "daily_by_age.parquet")

def load_timeofday():
    return pd.read_parquet(DATA_DIR / "daily_by_timeofday.parquet")


# ===========================================================================
# A. 先行研究手法の再現
# ===========================================================================

def scanlon_method(daily: pd.DataFrame) -> dict:
    """
    Scanlon (1993) 再現: 13日金曜 vs 6日金曜 (paired comparison)

    原著: 同月の金曜6日を対照として paired t-test。
    追加: 同月の金曜20日も対照として比較。
    """
    print("=" * 70)
    print("A1. SCANLON METHOD: Friday 13th vs Friday 6th (Paired)")
    print("=" * 70)

    fri = daily[daily["is_friday"] == 1].copy()

    # 同月の6日金曜 vs 13日金曜をペアにする
    fri13 = fri[fri["is_friday13th"] == 1][["date", "year", "month", "total"]].copy()
    fri13 = fri13.rename(columns={"total": "total_13", "date": "date_13"})

    fri6 = fri[fri["friday_day"] == 6][["date", "year", "month", "total"]].copy()
    fri6 = fri6.rename(columns={"total": "total_6", "date": "date_6"})

    # 同年・同月で結合
    paired = fri13.merge(fri6, on=["year", "month"], how="inner")

    print(f"\n  Paired observations: {len(paired)}")
    print(f"  (Some months have Friday 13th but no Friday 6th, or vice versa)\n")

    if len(paired) > 0:
        print("  Date pairs:")
        for _, row in paired.iterrows():
            diff = row["total_13"] - row["total_6"]
            print(f"    {row['date_13'].strftime('%Y-%m-%d')} ({row['total_13']:,}) vs "
                  f"{row['date_6'].strftime('%Y-%m-%d')} ({row['total_6']:,}) : diff={diff:+d}")

        mean_13 = paired["total_13"].mean()
        mean_6 = paired["total_6"].mean()
        rr = mean_13 / mean_6

        # Paired t-test
        t_stat, p_val = stats.ttest_rel(paired["total_13"], paired["total_6"])

        # Wilcoxon signed-rank (non-parametric)
        w_stat, p_wilcox = stats.wilcoxon(paired["total_13"], paired["total_6"])

        print(f"\n  Mean Friday 13th: {mean_13:.1f}")
        print(f"  Mean Friday 6th:  {mean_6:.1f}")
        print(f"  Rate Ratio: {rr:.4f} ({(rr-1)*100:+.1f}%)")
        print(f"  Paired t-test: t={t_stat:.3f}, p={p_val:.4f}")
        print(f"  Wilcoxon signed-rank: W={w_stat:.0f}, p={p_wilcox:.4f}")
        print(f"\n  Scanlon found: RR=1.44 (+52%), p<0.05 (UK, N=110 admissions)")
        print(f"  Japan result:  RR={rr:.2f} ({(rr-1)*100:+.1f}%), p={p_val:.4f}")

        return {
            "method": "Scanlon (paired)",
            "n_pairs": len(paired),
            "mean_fri13": mean_13,
            "mean_control": mean_6,
            "rr": rr,
            "t_stat": t_stat,
            "p_paired_t": p_val,
            "p_wilcoxon": p_wilcox,
        }
    return {}


def nayha_method(daily: pd.DataFrame, daily_age: pd.DataFrame) -> dict:
    """
    Nayha (2002) 再現: 負の二項回帰

    原著: count ~ NegBin(friday13 + sex + age + temp + year)
    本研究: 性別なし → 年齢層別に層別解析
    """
    print("\n" + "=" * 70)
    print("A2. NAYHA METHOD: Negative Binomial Regression")
    print("=" * 70)

    results = {}

    # --- Overall ---
    fridays = daily[daily["is_friday"] == 1].copy()
    res_overall = _fit_negbin(fridays, "Overall")
    results["overall"] = res_overall

    # --- Age group stratification ---
    print("\n  --- Age Group Stratification ---")
    age_groups = ["young", "mid_low", "mid_hi", "elderly"]
    age_fridays = daily_age[daily_age["is_friday"] == 1].copy()

    for ag in age_groups:
        subset = age_fridays[age_fridays["age_group_a"] == ag].copy()
        if len(subset) > 0:
            res = _fit_negbin(subset, f"Age: {ag}")
            results[f"age_{ag}"] = res

    # Comparison with Nayha
    print(f"\n  Nayha (2002) found: Women RR=1.63 (sig), Men RR=1.02 (ns)")
    print(f"  Japan Overall: RR={res_overall.get('rr', 'N/A')}")

    return results


def _fit_negbin(df: pd.DataFrame, label: str) -> dict:
    """負の二項回帰を fitting する内部関数"""
    df = df.copy()
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    endog = df["total"]
    exog_cols = ["is_friday13th", "month_sin", "month_cos", "year"]

    # 雲量があれば共変量に追加
    if "cloud_cover_jma" in df.columns and df["cloud_cover_jma"].notna().sum() > 0:
        exog_cols.append("cloud_cover_jma")
        df["cloud_cover_jma"] = df["cloud_cover_jma"].fillna(df["cloud_cover_jma"].median())

    exog = sm.add_constant(df[exog_cols])

    try:
        model = GLM(endog, exog, family=NegativeBinomial(alpha=1.0))
        fit = model.fit(maxiter=100, method="newton")

        coef = fit.params["is_friday13th"]
        se = fit.bse["is_friday13th"]
        rr = np.exp(coef)
        ci_low = np.exp(coef - 1.96 * se)
        ci_high = np.exp(coef + 1.96 * se)
        p_val = fit.pvalues["is_friday13th"]

        print(f"\n  {label} (n={len(df)}):")
        print(f"    Coeff(friday13): {coef:.4f} (SE={se:.4f})")
        print(f"    RR = {rr:.4f} (95% CI: {ci_low:.4f} - {ci_high:.4f})")
        print(f"    p = {p_val:.4f}")

        return {
            "label": label,
            "n": len(df),
            "coeff": coef,
            "se": se,
            "rr": rr,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "p_value": p_val,
        }
    except Exception as e:
        print(f"\n  {label}: Model fitting failed: {e}")
        return {"label": label, "error": str(e)}


def lo_method(daily: pd.DataFrame) -> dict:
    """
    Lo (2012) 再現: 6日 vs 13日 vs 20日 vs 27日 金曜 ANOVA + post-hoc

    原著: 複数対照日との比較 + カテゴリ別ロジスティック回帰
    """
    print("\n" + "=" * 70)
    print("A3. LO METHOD: 6th vs 13th vs 20th vs 27th (Fridays)")
    print("=" * 70)

    lo_fri = daily[daily["is_lo_friday"] == 1].copy()

    groups = {}
    for day in [6, 13, 20, 27]:
        subset = lo_fri[lo_fri["friday_day"] == day]["total"]
        groups[day] = subset
        print(f"\n  {day}th (n={len(subset)}): mean={subset.mean():.1f}, SD={subset.std():.1f}, "
              f"median={subset.median():.0f}")

    # One-way ANOVA
    f_stat, p_anova = stats.f_oneway(*groups.values())
    print(f"\n  One-way ANOVA: F={f_stat:.3f}, p={p_anova:.4f}")

    # Kruskal-Wallis (non-parametric)
    h_stat, p_kw = stats.kruskal(*groups.values())
    print(f"  Kruskal-Wallis: H={h_stat:.3f}, p={p_kw:.4f}")

    # Post-hoc: 13th vs each control
    print("\n  Post-hoc (13th vs each):")
    posthoc = {}
    for day in [6, 20, 27]:
        t, p = stats.ttest_ind(groups[13], groups[day])
        u, p_mw = stats.mannwhitneyu(groups[13], groups[day], alternative="two-sided")
        diff = groups[13].mean() - groups[day].mean()
        print(f"    13th vs {day}th: diff={diff:+.1f}, t={t:.3f}, p={p:.4f}, MW-U p={p_mw:.4f}")
        posthoc[day] = {"t": t, "p_t": p, "p_mw": p_mw, "diff": diff}

    print(f"\n  Lo (2012) found: Overall ED visits DECREASED on Fri 13th")
    print(f"  Lo (2012): Penetrating trauma only OR=1.65 (95% CI: 1.04-2.61)")

    return {
        "method": "Lo (ANOVA)",
        "f_stat": f_stat,
        "p_anova": p_anova,
        "h_stat": h_stat,
        "p_kruskal": p_kw,
        "posthoc": posthoc,
        "group_means": {d: g.mean() for d, g in groups.items()},
    }


# ===========================================================================
# B. 独自分析
# ===========================================================================

def case_crossover(daily: pd.DataFrame) -> dict:
    """
    Case-crossover: 同月内他金曜を対照とした比較

    各13日金曜日について、同月の他の金曜日を対照群とする。
    条件付きロジスティック回帰に近似した paired 分析。
    """
    print("\n" + "=" * 70)
    print("B1. CASE-CROSSOVER: Same-month Friday controls")
    print("=" * 70)

    fridays = daily[daily["is_friday"] == 1].copy()
    fri13_dates = fridays[fridays["is_friday13th"] == 1]

    results = []
    for _, row in fri13_dates.iterrows():
        y, m = row["year"], row["month"]
        same_month = fridays[(fridays["year"] == y) & (fridays["month"] == m)]
        controls = same_month[same_month["is_friday13th"] == 0]

        case_count = row["total"]
        control_mean = controls["total"].mean()
        control_sd = controls["total"].std()
        n_controls = len(controls)
        ratio = case_count / control_mean if control_mean > 0 else np.nan

        results.append({
            "date": row["date"],
            "case_count": case_count,
            "control_mean": control_mean,
            "control_sd": control_sd,
            "n_controls": n_controls,
            "ratio": ratio,
        })

    res_df = pd.DataFrame(results)
    print("\n" + res_df.to_string(index=False))

    mean_ratio = res_df["ratio"].mean()
    # One-sample t-test: is mean ratio significantly different from 1?
    t_ratio, p_ratio = stats.ttest_1samp(res_df["ratio"], 1.0)

    # Pooled comparison
    all_case = fri13_dates["total"].values
    all_control_means = res_df["control_mean"].values
    overall_rr = all_case.mean() / all_control_means.mean()

    print(f"\n  Mean ratio: {mean_ratio:.4f}")
    print(f"  t-test (ratio vs 1.0): t={t_ratio:.3f}, p={p_ratio:.4f}")
    print(f"  Overall RR: {overall_rr:.4f}")
    print(f"  Ratios > 1: {(res_df['ratio'] > 1).sum()} / {len(res_df)}")

    return {
        "method": "Case-crossover",
        "mean_ratio": mean_ratio,
        "overall_rr": overall_rr,
        "t_ratio": t_ratio,
        "p_ratio": p_ratio,
        "n_above_1": int((res_df["ratio"] > 1).sum()),
        "n_total": len(res_df),
        "detail": res_df,
    }


def adjusted_negbin(daily: pd.DataFrame) -> dict:
    """
    独自分析: 共変量調整済み負の二項回帰

    Nayha法を拡張: 天候 + 祝日 + お盆/年末年始 を共変量に追加
    """
    print("\n" + "=" * 70)
    print("B2. ADJUSTED NEGATIVE BINOMIAL REGRESSION")
    print("=" * 70)

    fridays = daily[daily["is_friday"] == 1].copy()

    fridays["month_sin"] = np.sin(2 * np.pi * fridays["month"] / 12)
    fridays["month_cos"] = np.cos(2 * np.pi * fridays["month"] / 12)
    fridays["cloud_cover_jma"] = fridays["cloud_cover_jma"].fillna(
        fridays["cloud_cover_jma"].median()
    )

    endog = fridays["total"]
    exog_cols = [
        "is_friday13th",
        "month_sin", "month_cos",
        "year",
        "cloud_cover_jma",
        "is_holiday_flag",
        "is_obon",
        "is_newyear",
    ]
    exog = sm.add_constant(fridays[exog_cols])

    model = GLM(endog, exog, family=NegativeBinomial(alpha=1.0))
    fit = model.fit(maxiter=100, method="newton")

    print("\n  Full model summary (Friday the 13th coefficient):")
    coef = fit.params["is_friday13th"]
    se = fit.bse["is_friday13th"]
    rr = np.exp(coef)
    ci_low = np.exp(coef - 1.96 * se)
    ci_high = np.exp(coef + 1.96 * se)
    p_val = fit.pvalues["is_friday13th"]

    print(f"    Coeff: {coef:.4f} (SE={se:.4f})")
    print(f"    RR = {rr:.4f} (95% CI: {ci_low:.4f} - {ci_high:.4f})")
    print(f"    p = {p_val:.4f}")

    print("\n  All coefficients:")
    for var in fit.params.index:
        print(f"    {var:20s}: coeff={fit.params[var]:.4f}, p={fit.pvalues[var]:.4f}")

    return {
        "method": "Adjusted NegBin",
        "rr": rr,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "p_value": p_val,
        "coeff": coef,
        "se": se,
        "n": len(fridays),
    }


def subgroup_analyses(daily_sev: pd.DataFrame, daily_age: pd.DataFrame,
                       daily_tod: pd.DataFrame) -> dict:
    """
    サブグループ分析: 重症度別、年齢層別、時間帯別
    """
    print("\n" + "=" * 70)
    print("B3. SUBGROUP ANALYSES")
    print("=" * 70)

    results = {}

    # --- Severity ---
    print("\n  --- By Severity ---")
    for sev in daily_sev["severity_label"].unique():
        subset = daily_sev[
            (daily_sev["severity_label"] == sev) & (daily_sev["is_friday"] == 1)
        ]
        fri13 = subset[subset["is_friday13th"] == 1]["total"]
        other = subset[subset["is_friday13th"] == 0]["total"]
        if len(fri13) > 0 and len(other) > 0:
            rr = fri13.mean() / other.mean()
            t, p = stats.ttest_ind(fri13, other)
            print(f"    {sev}: Fri13 mean={fri13.mean():.1f}, Other={other.mean():.1f}, "
                  f"RR={rr:.4f}, p={p:.4f}")
            results[f"severity_{sev}"] = {"rr": rr, "p": p, "n_fri13": len(fri13)}

    # --- Age group ---
    print("\n  --- By Age Group ---")
    for ag in sorted(daily_age["age_group_a"].unique()):
        subset = daily_age[
            (daily_age["age_group_a"] == ag) & (daily_age["is_friday"] == 1)
        ]
        fri13 = subset[subset["is_friday13th"] == 1]["total"]
        other = subset[subset["is_friday13th"] == 0]["total"]
        if len(fri13) > 0 and len(other) > 0:
            rr = fri13.mean() / other.mean()
            t, p = stats.ttest_ind(fri13, other)
            print(f"    {ag}: Fri13 mean={fri13.mean():.1f}, Other={other.mean():.1f}, "
                  f"RR={rr:.4f}, p={p:.4f}")
            results[f"age_{ag}"] = {"rr": rr, "p": p, "n_fri13": len(fri13)}

    # --- Time of day ---
    print("\n  --- By Time of Day ---")
    for tod in sorted(daily_tod["timeofday"].unique()):
        subset = daily_tod[
            (daily_tod["timeofday"] == tod) & (daily_tod["is_friday"] == 1)
        ]
        fri13 = subset[subset["is_friday13th"] == 1]["total"]
        other = subset[subset["is_friday13th"] == 0]["total"]
        if len(fri13) > 0 and len(other) > 0:
            rr = fri13.mean() / other.mean()
            t, p = stats.ttest_ind(fri13, other)
            print(f"    {tod}: Fri13 mean={fri13.mean():.1f}, Other={other.mean():.1f}, "
                  f"RR={rr:.4f}, p={p:.4f}")
            results[f"timeofday_{tod}"] = {"rr": rr, "p": p, "n_fri13": len(fri13)}

    return results


def sensitivity_analyses(daily: pd.DataFrame) -> dict:
    """
    感度分析:
    1. COVID (2020) 除外
    2. お盆・年末年始除外
    3. 祝日除外
    """
    print("\n" + "=" * 70)
    print("B4. SENSITIVITY ANALYSES")
    print("=" * 70)

    results = {}
    fridays = daily[daily["is_friday"] == 1].copy()

    # Base case
    fri13_base = fridays[fridays["is_friday13th"] == 1]["total"]
    other_base = fridays[fridays["is_friday13th"] == 0]["total"]
    rr_base = fri13_base.mean() / other_base.mean()

    scenarios = {
        "Base (all data)": fridays,
        "Excl. COVID (2020)": fridays[fridays["is_covid_year"] == 0],
        "Excl. Obon & New Year": fridays[(fridays["is_obon"] == 0) & (fridays["is_newyear"] == 0)],
        "Excl. Holidays": fridays[fridays["is_holiday_flag"] == 0],
        "Excl. COVID + Holidays": fridays[
            (fridays["is_covid_year"] == 0) & (fridays["is_holiday_flag"] == 0)
        ],
    }

    for label, subset in scenarios.items():
        fri13 = subset[subset["is_friday13th"] == 1]["total"]
        other = subset[subset["is_friday13th"] == 0]["total"]
        if len(fri13) > 0 and len(other) > 0:
            rr = fri13.mean() / other.mean()
            t, p = stats.ttest_ind(fri13, other)
            print(f"\n  {label}:")
            print(f"    n(Fri13)={len(fri13)}, n(Other)={len(other)}")
            print(f"    Fri13 mean={fri13.mean():.1f}, Other mean={other.mean():.1f}")
            print(f"    RR={rr:.4f}, p={p:.4f}")
            results[label] = {
                "rr": rr, "p": p,
                "n_fri13": len(fri13), "n_other": len(other),
                "mean_fri13": fri13.mean(), "mean_other": other.mean(),
            }

    return results


# ===========================================================================
# C. 国際比較テーブル
# ===========================================================================

def cross_national_comparison(japan_results: dict) -> pd.DataFrame:
    """
    先行研究の結果と日本の結果を並べた国際比較テーブルを作成
    """
    print("\n" + "=" * 70)
    print("C. CROSS-NATIONAL COMPARISON TABLE")
    print("=" * 70)

    rows = [
        {
            "Country": "UK",
            "Study": "Scanlon 1993",
            "Period": "multiple years",
            "N_events": 110,
            "Outcome": "Hospital admissions",
            "Design": "Paired (6th vs 13th)",
            "Effect_RR": 1.44,
            "CI_95": "not reported",
            "Significant": "Yes (p<0.05)",
            "Direction": "Increase (+52%)",
            "Cultural_fear_13": "Strong",
        },
        {
            "Country": "Finland",
            "Study": "Nayha 2002",
            "Period": "1971-1997",
            "N_events": "41 (women)",
            "Outcome": "Traffic fatalities",
            "Design": "NegBin regression",
            "Effect_RR": "Women 1.63 / Men 1.02",
            "CI_95": "not reported",
            "Significant": "Women only",
            "Direction": "Increase (women)",
            "Cultural_fear_13": "Moderate",
        },
        {
            "Country": "Finland",
            "Study": "Radun 2004",
            "Period": "1989-2002",
            "N_events": "21 Fri13s",
            "Outcome": "Injury accidents",
            "Design": "Matched (adjacent Fri)",
            "Effect_RR": "~1.0",
            "CI_95": "not reported",
            "Significant": "No",
            "Direction": "Null",
            "Cultural_fear_13": "Moderate",
        },
        {
            "Country": "Netherlands",
            "Study": "CVS 2008",
            "Period": "~2 years",
            "N_events": "7500/day",
            "Outcome": "Insurance claims",
            "Design": "Descriptive",
            "Effect_RR": 0.96,
            "CI_95": "N/A (non-academic)",
            "Significant": "No (decreased)",
            "Direction": "Decrease (-4%)",
            "Cultural_fear_13": "Moderate",
        },
        {
            "Country": "Germany",
            "Study": "Schuld 2011",
            "Period": "2001-2010",
            "N_events": 27914,
            "Outcome": "Surgical outcomes",
            "Design": "Retrospective cohort",
            "Effect_RR": "~1.0",
            "CI_95": "not reported",
            "Significant": "No",
            "Direction": "Null",
            "Cultural_fear_13": "Strong",
        },
        {
            "Country": "USA",
            "Study": "Lo 2012",
            "Period": "8 years",
            "N_events": 49094,
            "Outcome": "ED visits",
            "Design": "Multi-control comparison",
            "Effect_RR": "Overall <1.0 / Penetrating 1.65",
            "CI_95": "Penetrating: 1.04-2.61",
            "Significant": "Penetrating only",
            "Direction": "Decrease (overall) / Increase (penetrating)",
            "Cultural_fear_13": "Strong",
        },
        {
            "Country": "Canada",
            "Study": "Ranganathan 2024",
            "Period": "2007-2019",
            "N_events": 19747,
            "Outcome": "Surgical outcomes",
            "Design": "Population cohort",
            "Effect_RR": 1.02,
            "CI_95": "0.94-1.09",
            "Significant": "No",
            "Direction": "Null",
            "Cultural_fear_13": "Strong",
        },
        {
            "Country": "USA",
            "Study": "Shekhar 2025",
            "Period": "not confirmed",
            "N_events": "not confirmed",
            "Outcome": "EMS volume",
            "Design": "Letter",
            "Effect_RR": "~1.0",
            "CI_95": "not confirmed",
            "Significant": "No",
            "Direction": "Null",
            "Cultural_fear_13": "Strong",
        },
        {
            "Country": "Japan",
            "Study": "Present study",
            "Period": "2019-2024",
            "N_events": "1,884,793",
            "Outcome": "Traffic accidents",
            "Design": "Multiple (Scanlon/Nayha/Lo/Case-crossover)",
            "Effect_RR": japan_results.get("rr", "N/A"),
            "CI_95": japan_results.get("ci", "N/A"),
            "Significant": japan_results.get("sig", "N/A"),
            "Direction": japan_results.get("direction", "N/A"),
            "Cultural_fear_13": "Absent",
        },
    ]

    comp_df = pd.DataFrame(rows)
    print("\n" + comp_df.to_string(index=False))

    comp_df.to_csv(OUTPUT_DIR / "cross_national_comparison.csv", index=False)
    print(f"\n  Saved to {OUTPUT_DIR / 'cross_national_comparison.csv'}")

    # Summary by cultural fear level
    print("\n  --- Pattern by Cultural Context ---")
    print("  Strong fear (UK, USA, Germany, Canada): Mixed (1 sig, rest null)")
    print("  Moderate fear (Finland, Netherlands): Mixed (1 sig women-only, rest null)")
    print("  Absent fear (Japan): " + japan_results.get("direction", "TBD"))

    return comp_df


# ===========================================================================
# Power analysis
# ===========================================================================

def power_analysis(daily: pd.DataFrame) -> dict:
    """検出力分析: N=10で検出可能な効果サイズ"""
    print("\n" + "=" * 70)
    print("POWER ANALYSIS")
    print("=" * 70)

    fridays = daily[daily["is_friday"] == 1]
    n1 = len(fridays[fridays["is_friday13th"] == 1])
    n2 = len(fridays[fridays["is_friday13th"] == 0])
    pooled_sd = fridays["total"].std()
    mean_control = fridays[fridays["is_friday13th"] == 0]["total"].mean()

    from scipy.stats import norm
    z_alpha = norm.ppf(0.975)
    z_beta = norm.ppf(0.80)
    min_diff = (z_alpha + z_beta) * pooled_sd * np.sqrt(1/n1 + 1/n2)

    print(f"  n(Friday 13th) = {n1}")
    print(f"  n(Other Fridays) = {n2}")
    print(f"  Pooled SD = {pooled_sd:.1f}")
    print(f"  Mean (Other Fridays) = {mean_control:.1f}")
    print(f"  Min detectable difference (80% power, alpha=0.05): {min_diff:.1f}")
    print(f"  As % of mean: {min_diff/mean_control*100:.1f}%")

    # Effect sizes from literature
    effects = {
        "Scanlon (+52%)": mean_control * 0.52,
        "Nayha women (+63%)": mean_control * 0.63,
        "Lo penetrating (+65%)": mean_control * 0.65,
        "Japan observed (+3.9%)": mean_control * 0.039,
    }
    print(f"\n  Detectable effects at 80% power:")
    for label, effect in effects.items():
        detectable = "YES" if effect > min_diff else "NO"
        print(f"    {label}: {effect:.0f} accidents ({detectable})")

    return {
        "n_fri13": n1,
        "n_other": n2,
        "pooled_sd": pooled_sd,
        "min_detectable_diff": min_diff,
        "min_detectable_pct": min_diff / mean_control * 100,
    }


# ===========================================================================
# Main
# ===========================================================================

def main():
    daily = load_daily()
    daily_sev = load_severity()
    daily_age = load_age()
    daily_tod = load_timeofday()

    # A. Prior study reproductions
    scanlon_res = scanlon_method(daily)
    nayha_res = nayha_method(daily, daily_age)
    lo_res = lo_method(daily)

    # B. Original analyses
    crossover_res = case_crossover(daily)
    adjnb_res = adjusted_negbin(daily)
    subgroup_res = subgroup_analyses(daily_sev, daily_age, daily_tod)
    sensitivity_res = sensitivity_analyses(daily)

    # Power analysis
    power_res = power_analysis(daily)

    # C. Cross-national comparison
    japan_rr = adjnb_res.get("rr", scanlon_res.get("rr", "N/A"))
    japan_ci = f"{adjnb_res.get('ci_low', 'N/A'):.4f}-{adjnb_res.get('ci_high', 'N/A'):.4f}" if isinstance(adjnb_res.get("ci_low"), float) else "N/A"
    japan_p = adjnb_res.get("p_value", "N/A")
    japan_sig = "No" if isinstance(japan_p, float) and japan_p > 0.05 else "Yes" if isinstance(japan_p, float) else "N/A"
    japan_dir = "Null" if isinstance(japan_rr, float) and 0.95 < japan_rr < 1.05 else (
        "Increase" if isinstance(japan_rr, float) and japan_rr >= 1.05 else "Decrease" if isinstance(japan_rr, float) else "N/A"
    )

    comp_df = cross_national_comparison({
        "rr": f"{japan_rr:.4f}" if isinstance(japan_rr, float) else japan_rr,
        "ci": japan_ci,
        "sig": japan_sig,
        "direction": japan_dir,
    })

    # Save all results
    all_results = {
        "scanlon": scanlon_res,
        "nayha_overall": nayha_res.get("overall", {}),
        "lo": {k: v for k, v in lo_res.items() if k != "posthoc"},
        "case_crossover": {k: v for k, v in crossover_res.items() if k != "detail"},
        "adjusted_negbin": adjnb_res,
        "power": power_res,
    }

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY OF ALL ANALYSES")
    print("=" * 70)

    summary_rows = []
    if scanlon_res:
        summary_rows.append({
            "Analysis": "Scanlon (paired 6th vs 13th)",
            "RR": f"{scanlon_res.get('rr', 'N/A'):.4f}" if isinstance(scanlon_res.get('rr'), float) else "N/A",
            "p-value": f"{scanlon_res.get('p_paired_t', 'N/A'):.4f}" if isinstance(scanlon_res.get('p_paired_t'), float) else "N/A",
            "Significant": "No" if isinstance(scanlon_res.get('p_paired_t'), float) and scanlon_res['p_paired_t'] > 0.05 else "Yes",
        })

    nayha_ov = nayha_res.get("overall", {})
    if nayha_ov and "rr" in nayha_ov:
        summary_rows.append({
            "Analysis": "Nayha (NegBin, overall)",
            "RR": f"{nayha_ov['rr']:.4f}",
            "p-value": f"{nayha_ov['p_value']:.4f}",
            "Significant": "No" if nayha_ov["p_value"] > 0.05 else "Yes",
        })

    summary_rows.append({
        "Analysis": "Lo (ANOVA, 4 groups)",
        "RR": "N/A (ANOVA)",
        "p-value": f"{lo_res['p_anova']:.4f}",
        "Significant": "No" if lo_res["p_anova"] > 0.05 else "Yes",
    })

    summary_rows.append({
        "Analysis": "Case-crossover (same-month)",
        "RR": f"{crossover_res['overall_rr']:.4f}",
        "p-value": f"{crossover_res['p_ratio']:.4f}",
        "Significant": "No" if crossover_res["p_ratio"] > 0.05 else "Yes",
    })

    summary_rows.append({
        "Analysis": "Adjusted NegBin (full model)",
        "RR": f"{adjnb_res['rr']:.4f}",
        "p-value": f"{adjnb_res['p_value']:.4f}",
        "Significant": "No" if adjnb_res["p_value"] > 0.05 else "Yes",
    })

    summary_df = pd.DataFrame(summary_rows)
    print("\n" + summary_df.to_string(index=False))
    summary_df.to_csv(OUTPUT_DIR / "analysis_summary.csv", index=False)

    print(f"\n  Results saved to {OUTPUT_DIR}")
    print("\nDone.")


if __name__ == "__main__":
    main()

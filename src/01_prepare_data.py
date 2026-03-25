"""01_prepare_data.py
13日の金曜日分析用の日別集計データを作成する。

Input:
  fullmoon-accident/data/processed/accidents_clean.parquet  -- 事故個票データ
  fullmoon-accident/data/processed/accidents_analysis.parquet  -- 気象マージ済み個票
  fullmoon-accident/data/raw/jma/jma_cloud_cover_daily.parquet -- JMA日別雲量

Output:
  friday13th/data/daily_accidents.parquet   -- 日別集計メインデータ
  friday13th/data/daily_by_severity.parquet -- 重症度別日別集計
  friday13th/data/daily_by_age.parquet      -- 年齢層別日別集計
  friday13th/data/daily_by_timeofday.parquet -- 時間帯別日別集計

設計方針:
  - Lo法再現: 6th/13th/20th/27th の金曜日フラグを作成
  - Nayha法再現: 性別カラムが存在しないため年齢層別のみ（age_a基準）
  - 天候データ: accidents_analysisの nearest_station_id を転用して日別平均雲量を結合
  - 祝日・お盆・年末年始・COVID期間フラグを追加

NPA weekday_code 対応:
  1=日曜, 2=月曜, 3=火曜, 4=水曜, 5=木曜, 6=金曜, 7=土曜

NOTE: 性別カラムは accidents_clean.parquet に存在しない（hojuhyo由来のため）。
Nayha法の性別サブグループ分析は不可。年齢層別のみ実施。
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# パス定数
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent
_FULLMOON_ROOT = _REPO_ROOT.parent / "fullmoon-accident"

ACCIDENTS_CLEAN = _FULLMOON_ROOT / "data" / "processed" / "accidents_clean.parquet"
ACCIDENTS_ANALYSIS = _FULLMOON_ROOT / "data" / "processed" / "accidents_analysis.parquet"
JMA_WEATHER = _FULLMOON_ROOT / "data" / "raw" / "jma" / "jma_cloud_cover_daily.parquet"

OUTPUT_DIR = _REPO_ROOT / "data"
OUT_DAILY = OUTPUT_DIR / "daily_accidents.parquet"
OUT_SEVERITY = OUTPUT_DIR / "daily_by_severity.parquet"
OUT_AGE = OUTPUT_DIR / "daily_by_age.parquet"
OUT_TIMEOFDAY = OUTPUT_DIR / "daily_by_timeofday.parquet"

# ---------------------------------------------------------------------------
# カレンダー定数
# ---------------------------------------------------------------------------
# NPA weekday_code: 1=日 2=月 3=火 4=水 5=木 6=金 7=土
WEEKDAY_FRIDAY = 6

# Lo法: 同月の 6/13/20/27 日を対照群とする金曜日のみ対象
LO_METHOD_DAYS = [6, 13, 20, 27]

# accident_severity: 1=死亡, 2=傷害
SEVERITY_FATAL = 1
SEVERITY_INJURY = 2

# is_holiday: 1=祝日, 2=振替休日, 3=平日, 0=不明
HOLIDAY_FLAGS = {1, 2}   # 祝日 or 振替休日

# お盆期間
OBON_MONTHS = [8]
OBON_DAYS = list(range(13, 17))   # 8/13-16

# 年末年始期間
NEWYEAR_START_MONTH, NEWYEAR_START_DAY = 12, 29
NEWYEAR_END_MONTH, NEWYEAR_END_DAY = 1, 3

# COVID期間: 2020年（感度分析用）
COVID_YEAR = 2020

# NPA の年齢コード対応表
# NPA は 5歳または10歳刻みの代表値でエンコード:
#   0  = 不明
#   1  = 24歳以下（~24）
#   25 = 25-34歳
#   35 = 35-44歳
#   45 = 45-54歳
#   55 = 55-64歳
#   65 = 65-74歳
#   75 = 75歳以上
#
# Nayha法の理想区分 (0-15, 16-24, 25-64, 65+) は NPA コードで再現不可。
# NPA コードに即した4区分を採用:
#   "young"   = 1（24歳以下）
#   "mid_low" = 25-34, 35-44（25-44歳）
#   "mid_hi"  = 45-54, 55-64（45-64歳）
#   "elderly" = 65-74, 75+（65歳以上）
#   "unknown" = 0（不明）
AGE_CODE_TO_GROUP = {
    0:  "unknown",
    1:  "young",    # 24歳以下
    25: "mid_low",  # 25-34歳
    35: "mid_low",  # 35-44歳
    45: "mid_hi",   # 45-54歳
    55: "mid_hi",   # 55-64歳
    65: "elderly",  # 65-74歳
    75: "elderly",  # 75歳以上
}

# daynight グループ
DAYNIGHT_DAYTIME = {"daytime"}
DAYNIGHT_NIGHTTIME = {"night", "night_dark", "dusk"}

# ---------------------------------------------------------------------------
# ロガー設定
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ユーティリティ関数
# ---------------------------------------------------------------------------

def load_accidents() -> pd.DataFrame:
    """事故個票を読み込み、日付カラムを追加して返す。"""
    logger.info("Loading accidents_clean: %s", ACCIDENTS_CLEAN)
    df = pd.read_parquet(ACCIDENTS_CLEAN)
    logger.info("  Loaded %d records, %d columns", len(df), len(df.columns))
    df["date"] = df["occurred_at"].dt.normalize()
    return df


def load_station_mapping() -> pd.DataFrame:
    """
    accidents_analysis から (pref_code, station_code, record_no, occurred_at_jst,
    nearest_station_id) のマッピングを取得。

    結合キーについて:
      - record_key (pref+station+record_no) は年をまたいで再利用されるため一意でない
      - (pref_code, station_code, record_no, occurred_at) の4列複合キーが全行で一意
      - accidents_analysis の occurred_at は UTC。accidents_clean は JST（タイムゾーン非付与）
        → UTC を JST (+9h) に変換してから結合する
    """
    logger.info("Loading station mapping from accidents_analysis: %s", ACCIDENTS_ANALYSIS)
    cols = ["pref_code", "station_code", "record_no", "occurred_at", "nearest_station_id"]
    df = pd.read_parquet(ACCIDENTS_ANALYSIS, columns=cols)

    # UTC → JST 変換 (タイムゾーン情報を除去して naive datetime にする)
    df["occurred_at_jst"] = (
        df["occurred_at"]
        .dt.tz_convert("Asia/Tokyo")
        .dt.tz_localize(None)
    )
    df = df.drop(columns=["occurred_at"])

    logger.info("  Loaded station mapping: %d records", len(df))
    return df


def load_weather() -> pd.DataFrame:
    """JMA日別雲量データを読み込む。station_id / date をキーに返す。"""
    logger.info("Loading JMA weather: %s", JMA_WEATHER)
    weather = pd.read_parquet(JMA_WEATHER)
    # dateをdatetime64[D]（日付のみ）に正規化
    weather["date"] = pd.to_datetime(weather["date"]).dt.normalize()
    logger.info("  Loaded %d rows, stations: %d", len(weather), weather["station_id"].nunique())
    return weather


def build_daily_weather(weather: pd.DataFrame) -> pd.DataFrame:
    """
    station_id x date ごとの雲量を pivot して返す。
    各日の最終的な cloud_cover は weather["cloud_cover"]（日平均）を使用。
    """
    return weather[["station_id", "date", "cloud_cover"]].copy()


# ---------------------------------------------------------------------------
# カレンダーフラグ作成
# ---------------------------------------------------------------------------

def add_friday13th_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    13日の金曜フラグと関連カレンダーフラグを追加する。

    追加カラム:
      is_friday          -- 金曜日フラグ (weekday_code == 6)
      is_13th            -- 13日フラグ
      is_friday13th      -- 13日の金曜フラグ
      friday_day         -- 金曜日のその月の日 (6/13/20/27 or NaN)
      is_lo_friday       -- Lo法: 6/13/20/27 日の金曜フラグ
      is_obon            -- お盆期間フラグ (8/13-16)
      is_newyear         -- 年末年始フラグ (12/29-1/3)
      is_covid_year      -- 2020年フラグ (感度分析用)
      is_holiday_flag    -- 祝日・振替休日フラグ (is_holiday in {1,2})
    """
    day = df["date"].dt.day
    month = df["date"].dt.month
    year = df["date"].dt.year

    df["is_friday"] = (df["weekday_code"] == WEEKDAY_FRIDAY).astype(int)
    df["is_13th"] = (day == 13).astype(int)
    df["is_friday13th"] = ((df["weekday_code"] == WEEKDAY_FRIDAY) & (day == 13)).astype(int)

    # Lo法: 6/13/20/27日の金曜 → 同月対照設計用
    df["friday_day"] = np.where(
        (df["weekday_code"] == WEEKDAY_FRIDAY) & (day.isin(LO_METHOD_DAYS)),
        day, np.nan
    )
    df["is_lo_friday"] = (
        (df["weekday_code"] == WEEKDAY_FRIDAY) & (day.isin(LO_METHOD_DAYS))
    ).astype(int)

    # お盆
    df["is_obon"] = (
        month.isin(OBON_MONTHS) & day.isin(OBON_DAYS)
    ).astype(int)

    # 年末年始 (12/29-31 or 1/1-3)
    df["is_newyear"] = (
        ((month == NEWYEAR_START_MONTH) & (day >= NEWYEAR_START_DAY)) |
        ((month == NEWYEAR_END_MONTH) & (day <= NEWYEAR_END_DAY))
    ).astype(int)

    # COVID
    df["is_covid_year"] = (year == COVID_YEAR).astype(int)

    # 祝日フラグ正規化
    df["is_holiday_flag"] = df["is_holiday"].isin(HOLIDAY_FLAGS).astype(int)

    return df


def add_age_group(df: pd.DataFrame) -> pd.DataFrame:
    """
    age_a を NPA コードに基づく年齢層カラムに変換する。

    NPA 年齢コード（10歳刻み代表値）を 4 グループに集約:
      young   = 1（24歳以下）
      mid_low = 25-44歳（コード 25, 35）
      mid_hi  = 45-64歳（コード 45, 55）
      elderly = 65歳以上（コード 65, 75）
      unknown = 0（不明）

    NOTE:
      - Nayha法の理想区分 (0-15, 16-24, 25-64, 65+) は NPA コードでは再現不可。
        NPA は 1=24歳以下 の単一コードしか持たないため。
      - 性別カラム (sex_a/sex_b) は accidents_clean.parquet に存在しないため
        Nayha法の性別サブグループ分析は実施不可。年齢層別のみ実施する。
    """
    df["age_group_a"] = df["age_a"].map(AGE_CODE_TO_GROUP).fillna("unknown")
    return df


# ---------------------------------------------------------------------------
# 気象データ結合
# ---------------------------------------------------------------------------

def merge_weather_to_accidents(
    df: pd.DataFrame,
    station_map: pd.DataFrame,
    weather_daily: pd.DataFrame,
) -> pd.DataFrame:
    """
    事故個票に最寄り観測所の日別雲量を結合する。

    手順:
      1. df に station_map を (pref_code, station_code, record_no, occurred_at) で left join
         ※ record_key は年またぎで再利用されるため使用しない
      2. (nearest_station_id, date) で weather_daily と left join
    """
    # station mapping 結合（4列複合キー）
    join_keys = ["pref_code", "station_code", "record_no", "occurred_at"]
    station_map_renamed = station_map.rename(columns={"occurred_at_jst": "occurred_at"})

    pre_len = len(df)
    df = df.merge(
        station_map_renamed[join_keys + ["nearest_station_id"]],
        on=join_keys,
        how="left",
    )
    assert len(df) == pre_len, (
        f"Merge caused row count change: {pre_len} -> {len(df)}. "
        "Check for duplicate keys in station_map."
    )

    logger.info(
        "  Station mapping: %d matched (%.1f%%)",
        df["nearest_station_id"].notna().sum(),
        100 * df["nearest_station_id"].notna().mean(),
    )

    # 気象データ結合
    df = df.merge(
        weather_daily.rename(columns={"station_id": "nearest_station_id", "cloud_cover": "cloud_cover_jma"}),
        on=["nearest_station_id", "date"],
        how="left",
    )
    assert len(df) == pre_len, (
        f"Weather merge caused row count change: {pre_len} -> {len(df)}."
    )

    logger.info(
        "  Cloud cover matched: %d (%.1f%%)",
        df["cloud_cover_jma"].notna().sum(),
        100 * df["cloud_cover_jma"].notna().mean(),
    )
    return df


# ---------------------------------------------------------------------------
# 日別集計
# ---------------------------------------------------------------------------

def build_daily_main(df: pd.DataFrame) -> pd.DataFrame:
    """
    メインの日別集計テーブルを作成する。

    集計:
      total            -- 全事故件数
      fatal_count      -- 死者数合計
      injury_count     -- 負傷者数合計
      n_fatal_acc      -- 死亡事故件数 (accident_severity==1)
      n_injury_acc     -- 傷害事故件数 (accident_severity==2)
      cloud_cover_jma  -- 日別平均雲量

    カレンダー属性 (first値を取得):
      weekday_code, is_holiday_flag,
      is_friday, is_13th, is_friday13th,
      is_lo_friday, friday_day,
      is_obon, is_newyear, is_covid_year
    """
    cal_cols = [
        "weekday_code", "is_holiday_flag",
        "is_friday", "is_13th", "is_friday13th",
        "is_lo_friday", "friday_day",
        "is_obon", "is_newyear", "is_covid_year",
    ]
    agg_dict = {
        "record_key": "count",
        "fatality_count": "sum",
        "injury_count": "sum",
        "cloud_cover_jma": "mean",
    }
    # 死亡事故件数・傷害事故件数
    agg_dict["n_fatal_acc"] = pd.NamedAgg(
        column="accident_severity",
        aggfunc=lambda x: (x == SEVERITY_FATAL).sum(),
    )
    agg_dict["n_injury_acc"] = pd.NamedAgg(
        column="accident_severity",
        aggfunc=lambda x: (x == SEVERITY_INJURY).sum(),
    )

    daily = df.groupby("date").agg(**{
        "total": pd.NamedAgg(column="record_key", aggfunc="count"),
        "fatal_count": pd.NamedAgg(column="fatality_count", aggfunc="sum"),
        "injury_count": pd.NamedAgg(column="injury_count", aggfunc="sum"),
        "n_fatal_acc": pd.NamedAgg(
            column="accident_severity",
            aggfunc=lambda x: (x == SEVERITY_FATAL).sum(),
        ),
        "n_injury_acc": pd.NamedAgg(
            column="accident_severity",
            aggfunc=lambda x: (x == SEVERITY_INJURY).sum(),
        ),
        "cloud_cover_jma": pd.NamedAgg(column="cloud_cover_jma", aggfunc="mean"),
        **{c: pd.NamedAgg(column=c, aggfunc="first") for c in cal_cols},
    }).reset_index()

    # 日付から year/month/day を展開
    daily["year"] = daily["date"].dt.year
    daily["month"] = daily["date"].dt.month
    daily["day"] = daily["date"].dt.day

    logger.info(
        "daily_accidents: %d days, %d - %d total accidents/day (mean %.1f)",
        len(daily),
        daily["total"].min(),
        daily["total"].max(),
        daily["total"].mean(),
    )
    return daily


def build_daily_by_severity(df: pd.DataFrame) -> pd.DataFrame:
    """
    重症度別の日別集計。
    accident_severity: 1=死亡, 2=傷害
    """
    severity_label = {SEVERITY_FATAL: "fatal", SEVERITY_INJURY: "injury"}
    df["severity_label"] = df["accident_severity"].map(severity_label).fillna("unknown")

    cal_cols = ["weekday_code", "is_holiday_flag", "is_friday", "is_13th",
                "is_friday13th", "is_lo_friday", "is_covid_year"]

    daily = df.groupby(["date", "severity_label"]).agg(
        total=("record_key", "count"),
        **{c: (c, "first") for c in cal_cols},
    ).reset_index()

    daily["year"] = daily["date"].dt.year
    daily["month"] = daily["date"].dt.month

    logger.info("daily_by_severity: %d rows", len(daily))
    return daily


def build_daily_by_age(df: pd.DataFrame) -> pd.DataFrame:
    """
    年齢層別の日別集計 (age_a 基準)。

    NOTE: 性別カラム (sex_a, sex_b) は accidents_clean.parquet に存在しない。
    Nayha法の「性別×年齢層」サブグループは実施不可。年齢層別のみ。
    """
    cal_cols = ["weekday_code", "is_holiday_flag", "is_friday", "is_13th",
                "is_friday13th", "is_lo_friday", "is_covid_year"]

    # age_group_a == "unknown" (age_a==0) は集計から除外する
    valid = df[df["age_group_a"] != "unknown"]

    daily = valid.groupby(["date", "age_group_a"], observed=True).agg(
        total=("record_key", "count"),
        fatal_count=("fatality_count", "sum"),
        **{c: (c, "first") for c in cal_cols},
    ).reset_index()

    daily["year"] = daily["date"].dt.year
    daily["month"] = daily["date"].dt.month
    daily["age_group_a"] = daily["age_group_a"].astype(str)

    logger.info("daily_by_age: %d rows", len(daily))
    return daily


def build_daily_by_timeofday(df: pd.DataFrame) -> pd.DataFrame:
    """
    時間帯別の日別集計。
    daynight: daytime / nighttime（night + night_dark + dusk を統合）
    """
    # 時間帯を2分類に統合
    df["timeofday"] = df["daynight"].apply(
        lambda x: "daytime" if x in DAYNIGHT_DAYTIME else "nighttime"
    )

    cal_cols = ["weekday_code", "is_holiday_flag", "is_friday", "is_13th",
                "is_friday13th", "is_lo_friday", "is_covid_year"]

    daily = df.groupby(["date", "timeofday"]).agg(
        total=("record_key", "count"),
        fatal_count=("fatality_count", "sum"),
        cloud_cover_jma=("cloud_cover_jma", "mean"),
        **{c: (c, "first") for c in cal_cols},
    ).reset_index()

    daily["year"] = daily["date"].dt.year
    daily["month"] = daily["date"].dt.month

    logger.info("daily_by_timeofday: %d rows", len(daily))
    return daily


# ---------------------------------------------------------------------------
# バリデーション
# ---------------------------------------------------------------------------

def validate_daily(daily: pd.DataFrame, name: str) -> None:
    """基本的な整合性チェックをログ出力する。"""
    logger.info("=== Validation: %s ===", name)

    # 日付範囲
    logger.info("  Date range: %s - %s", daily["date"].min(), daily["date"].max())

    # 日数
    n_days = daily["date"].nunique()
    expected_days = (
        pd.Timestamp("2024-12-31") - pd.Timestamp("2019-01-01")
    ).days + 1
    logger.info(
        "  Unique dates: %d (expected ~%d for 2019-2024)",
        n_days, expected_days,
    )

    # 金曜日13日の件数
    if "is_friday13th" in daily.columns:
        n_f13 = daily[daily["is_friday13th"] == 1]["date"].nunique()
        logger.info("  Friday 13th dates: %d (expected ~10 for 6 years)", n_f13)

    # 欠損値
    null_counts = daily.isnull().sum()
    non_zero_nulls = null_counts[null_counts > 0]
    if len(non_zero_nulls) > 0:
        logger.info("  Columns with nulls: %s", non_zero_nulls.to_dict())

    # cloud_cover 欠損率
    if "cloud_cover_jma" in daily.columns:
        null_rate = daily["cloud_cover_jma"].isnull().mean()
        logger.info("  cloud_cover_jma null rate: %.1f%%", 100 * null_rate)


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- データ読み込み ---
    df = load_accidents()
    station_map = load_station_mapping()
    weather = load_weather()
    weather_daily = build_daily_weather(weather)

    # --- フラグ付与 ---
    logger.info("Adding calendar flags...")
    df = add_friday13th_flags(df)
    logger.info("Adding age groups...")
    df = add_age_group(df)

    # --- 気象データ結合 ---
    logger.info("Merging weather data...")
    df = merge_weather_to_accidents(df, station_map, weather_daily)

    # --- サマリー出力 ---
    logger.info("=== Input Data Summary ===")
    logger.info("Total accidents: %d", len(df))
    logger.info("Date range: %s - %s", df["date"].min(), df["date"].max())
    logger.info("Friday 13th accidents: %d", df["is_friday13th"].sum())
    n_f13_dates = df[df["is_friday13th"] == 1]["date"].nunique()
    logger.info("Friday 13th dates: %d", n_f13_dates)

    friday_days = df[df["is_friday"] == 1]["date"].dt.day.value_counts().sort_index()
    logger.info("Friday distribution by day-of-month:\n%s", friday_days.to_string())

    # --- 日別集計 ---
    logger.info("Building daily aggregations...")

    daily = build_daily_main(df)
    daily_severity = build_daily_by_severity(df)
    daily_age = build_daily_by_age(df)
    daily_timeofday = build_daily_by_timeofday(df)

    # --- バリデーション ---
    validate_daily(daily, "daily_accidents")
    validate_daily(daily_severity, "daily_by_severity")

    # --- 保存 ---
    logger.info("Saving outputs...")
    daily.to_parquet(OUT_DAILY, index=False)
    logger.info("  -> %s (%d rows)", OUT_DAILY, len(daily))

    daily_severity.to_parquet(OUT_SEVERITY, index=False)
    logger.info("  -> %s (%d rows)", OUT_SEVERITY, len(daily_severity))

    daily_age.to_parquet(OUT_AGE, index=False)
    logger.info("  -> %s (%d rows)", OUT_AGE, len(daily_age))

    daily_timeofday.to_parquet(OUT_TIMEOFDAY, index=False)
    logger.info("  -> %s (%d rows)", OUT_TIMEOFDAY, len(daily_timeofday))

    # --- 最終確認テーブル ---
    logger.info("\n=== Friday 13th vs Other Fridays (daily_accidents) ===")
    friday_only = daily[daily["is_friday"] == 1].copy()
    summary = friday_only.groupby("is_friday13th")["total"].describe()
    logger.info("\n%s", summary.to_string())

    logger.info("\n=== Lo-method control dates ===")
    lo_summary = daily[daily["is_lo_friday"] == 1].groupby("friday_day")["total"].describe()
    logger.info("\n%s", lo_summary.to_string())

    logger.info("Done.")


if __name__ == "__main__":
    main()

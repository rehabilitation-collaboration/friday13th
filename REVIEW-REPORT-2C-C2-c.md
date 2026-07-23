# Code Review Report (Phase 2C-C2-c)
Date: 2026-07-22
System: MAGI(Sonnet×3: CASPER/BALTHASAR/MELCHIOR) + AKAGI(Opus×1)
Target:
- `src/02_prefecture_panel_nb.py` (NEW, 356 lines)
- `tests/test_prefecture_panel_nb.py` (NEW, 208 lines)
- `tests/conftest.py` (MODIFIED, +21 lines)

## Critical Findings (P1)

| # | ID | Issue | Source | File:Line | Action Required |
|---|-----|-------|--------|-----------|----------------|
| P1-1 | A1 | **Single-way clustering on a day-level treatment understates SE (Bertrand-Duflo-Mullainathan 2004)**. `is_fri13` varies at date level (constant across all 47 prefectures on any given day). Clustering only on prefecture ignores cross-prefecture within-date correlation. Nationwide Fri13 media coverage would induce cross-prefecture same-date correlation not absorbed by prefecture/year/month/weekday FE. Current SE=0.0150 and p=0.083 are potentially anti-conservative — honest p could be materially larger, CI wider than [0.997, 1.057]. | AKAGI-independent | :19-21, :143-146, :178-181 | **切替: two-way clustering (prefecture + date) or date-only clustering。statsmodels は 2D groups サポート済** |

## Important Findings (P2)

| # | ID | Issue | Source | File:Line | Action Required |
|---|-----|-------|--------|-----------|----------------|
| P2-1 | F2 | `fit_poisson_qmle` の `family` label "Poisson QMLE (Pearson-scaled)" は嘘。コメントは "Rescale SE by sqrt(scale)" と主張するがコードは実行してない。`pearson_scale` は metadata として保存されるだけ。iid SE のまま | MAGI(3/3) | :163-169 | fallback 削除 (P2-3) で消滅。残すならコメント/label 訂正 |
| P2-2 | F3 | `except (RuntimeError, np.linalg.LinAlgError, Exception)` は冗長で bare Exception と同義。programming bug も fallback に silently 流される | MAGI(3/3) | :319-324 | fallback 削除で解消。残すなら narrow 化 |
| P2-3 | F4+A6 | **Poisson QMLE fallback path は unexercised dead code**。実データで両モデル NB MLE 収束 (fallback 発火せず) + test fixture が `run_sensitivity()` 経由でなく直接呼ぶので production の try/except も未検証。**YAGNI 違反** (~30行の起こり得ないシナリオ防御コード) | MAGI(3/3) + AKAGI | :156-186, :319-324 | **推奨: `fit_poisson_qmle` 削除 + `run_sensitivity` 単純化** |
| P2-4 | F5 | test が `count_ratio` の妥当範囲チェック無し。`math.isfinite` + `> 0` + CI順序のみ | MAGI(3/3) | test:131-140, 146-159 | `assert 0.8 < count_ratio < 1.3` 追加 |
| P2-5 | F6 | **Obon 交絡**: 10個の Fri13 のうち **2021-08-13 が Obon 初日** — 日本最大の国内旅行期間。旧 `adjusted_negbin()` は `is_obon` 統制、新 panel model は不採用。加えて panel parquet に `is_holiday/is_obon/is_newyear` 列が存在しないので、追加には panel 再生成が必要 | MAGI(3/3) | :27 docstring | **PLAN 通り C2-c は中間生成物として output/ 留置**。C2-d/e フェーズで `01a_build_panels.py` に is_holiday/is_obon 追加が必須 |
| P2-6 | F8 | Sensitivity は `pref_code` (51) で cluster、FE 定義と同じ列 → 「finer FE」と「finer clustering」の2軸 robustness を1テストで混ぜてる | MAGI(3/3) | :311-324 | **A1 修正 (two-way clustering) と同時に整理**。案: sensitivity は「pref_code FE (51) + cluster at prefecture_en (47)」 |
| P2-7 | F17 | 案Z の validation criterion 「primary と sensitivity が数値一致」を test で検証してない | MAGI(1/3, MELCHIOR) — AKAGI upgrade | test 全体 | `abs(primary_ratio - sensitivity_ratio) < 0.005` テスト追加 |
| P2-8 | A2 | **G < K: rank-deficient cluster meat matrix**。primary G=47 vs K=72, sensitivity G=51 vs K=76。Liang-Zeger V の rank ≤ G-1 = 46 で K を下回る。Cameron-Miller (2015) は G<50 で CR2 補正 or bootstrap-t 推奨。statsmodels はデフォルトで警告出さない | AKAGI-independent | :99, :143 | **まず A1 (two-way clustering) 対応してから G の方向性を判断** |
| P2-9 | A3 | **`is_13th` 主効果が未統制**。`is_fri13 = is_friday × is_13th`。`is_friday` は weekday FE で吸収されるが、`is_13th` (任意曜日の13日) は controlled されてない。給料日隣接など曜日と独立な day-13 効果が is_fri13 に leak する可能性 | AKAGI-independent | :99 | `DUMMY_COLS` に `is_13th` main effect (or day_of_month FE) 追加 |

## Minor Findings (P3)

| # | ID | Issue | Source | File:Line | Action Required |
|---|-----|-------|--------|-----------|----------------|
| P3-1 | F1 | `fit_c` (cluster refit) の convergence check なし。maxiter=50。warm start で即収束するので現状問題なし | MAGI(3/3) — AKAGI downgrade | :142-153, 176-186 | 3行の防御追加 |
| P3-2 | F7+F14+F16 | **`_to_native()` バンドル**: (a) numpy branches が現状 unreachable (全 field は upstream で cast 済)、(b) `np.bool_` 未対応、(c) `json.dumps(allow_nan=True)` デフォルトで NaN が非合法 JSON | MAGI(部分) + AKAGI | :289-300, :273-287 | **推奨: `_to_native()` 削除 + `json.dumps(..., allow_nan=False)`** |
| P3-3 | F9 | test の `REPO_ROOT` 未使用 dead variable | MAGI(2/3) | test:20 | 削除 |
| P3-4 | F10 | 新 `_v()` が旧版から optional `context` field を落とした。truth.json に context 使う entry ゼロで下流破壊なし | MAGI(2/3) — AKAGI REJECT as bug | :213-214 | 対応不要 (cosmetic) |
| P3-5 | F12 | test の `alpha < 0.5` hard-code (empirical) | MAGI(1/3, CASPER) | test:120-128 | 現状 OK。is_holiday 追加時に再チューニング必要 (docstring 予告済) |
| P3-6 | F13 | Poisson warm-start convergence 未チェック。NB 側で下流検知 | MAGI(1/3, CASPER) | :123-127 | 3行の防御追加 (低優先) |
| P3-7 | F15 | `use_t == False` for NB cluster (statsmodels default)。G=47/51 で t-df 補正なし → mildly anti-conservative | MAGI(1/3, BALTHASAR) | :189-207 | statsmodels 側。Methods セクションに z-based と明記 |
| P3-8 | A5 | `loglike_method="nb2"` hardcoded, nb1 sensitivity 未実施 | AKAGI-independent | :126 | Reviewers 対応で diagnostics に nb1 refit を1行追加 (or docstring 正当化) |
| P3-9 | A7 | docstring "is_holiday is not carried in the panel yet" は panel parquet 自体に列が無い状況を過小表現 | AKAGI-independent | :27 | docstring 修正: 「panel regeneration が必要」と明示 |
| P3-10 | A8 | README に `02_prefecture_panel_nb.py` 未記載 | AKAGI-independent | README.md | 一言追加 |
| P3-11 | A9 | `_v()` helper が2コピー (旧 + 新)。DRY 3コピールール的にはまだOK | AKAGI-independent | :213 | 次 (C1 or C3) 実装時に判断 |

## Rejected by AKAGI

| # | MAGI Finding | Rejection Reason |
|---|-------------|-----------------|
| F11 | 356行 > 300行ガイド | 兄弟ファイル `02_main_analysis.py` 1011行, `01_prepare_data.py` 575行 の project 規範内 |
| F10 (as bug) | `_v()` context field 欠落 | truth.json 実出力に context 使用ゼロ、下流破壊なし。cosmetic 扱いで P3 に留置 |

## Review Statistics

- **MAGI**: 40 items × 3 agents, 32 findings 抽出 (18 after 3/3 or 2/3 vote filter)
- **AKAGI verification**: ACCEPT 15 / REJECT 2 (F11, F10-as-bug)
- **AKAGI independent**: 9 findings (P1×1, P2×3, P3×5)
- **Composite severity**: **P1×1 / P2×9 / P3×11**

## AKAGI 深掘り所見

1. **CI [0.997, 1.057] は overstated の可能性大**
   - 「n=103k」は naïve view。effective d.f. は Fri13 dates n=10 に近い
   - two-way clustering (P1-1) + G<K 補正 (P2-8) を入れた honest CI は widen する
   - **manuscript にどの CI を載せるかは修正後に再判断**

2. **Old vs New の並記推奨**
   - 旧 [0.54, 1.94] → 新 [0.997, 1.057] の劇的な contraction (±90% → ±3%)
   - **黙って差し替えない**。旧は Nayha replication としてそのまま、新は panel design の追加分析として並記

3. **GPT V1 Major 5 (weather endogeneity) は mechanically 解消**
   - cloud_cover が prefecture-day covariate なので accident-location weighting の内生性は破れた
   - 「weather affects both counts and reporting」の別種内生性は残る (これは C2-d/e の降水降雪追加で緩和)

4. **nb2 vs nb1** — alpha=0.032 で両方で似た結果になる想定だが、reviewer 対応で nb1 refit を diagnostics に1行足すとベター

## 推奨アクションプラン

### 即対応 (2C-C2-c 完了扱いにする前)
1. **P1-1 (A1)**: two-way clustering (prefecture + date) に切替。SE/CI/p 再計算 → 結果報告
2. **P2-3 (F4+A6)**: `fit_poisson_qmle` 削除 + `run_sensitivity` 単純化 (F2, F3 も同時解消)
3. **P2-4 (F5)**: `assert 0.8 < count_ratio < 1.3` test 追加
4. **P2-7 (F17)**: primary↔sensitivity agreement test 追加
5. **P2-8 (A2)**: A1 修正後に G の方向性を再判断
6. **P2-9 (A3)**: `is_13th` main effect を DUMMY_COLS に追加
7. **P3-2 (F7+F14+F16)**: `_to_native()` 削除 + `allow_nan=False`
8. **P3-3, P3-9, P3-10**: 削除/docstring 修正/README 追加

### C2-d/e フェーズで対応
- **P2-5 (F6)**: `01a_build_panels.py` に is_holiday/is_obon/is_newyear 追加 + panel 再生成
- ~~**P2-6 (F8)**: sensitivity の cluster 軸を prefecture_en (47) に切替 (A1 修正と同時整理)~~ ← **2026-07-22 後半の 15 件修正一括適用の (iv) で解消済み** (`src/02_prefecture_panel_nb.py` L27/L127/L335-337・`prefecture_panel_results.json` の `bureau_nb_n_clusters_pref: 47` で確認可能)

### 後回し
- **P3-5, P3-6, P3-7, P3-8, P3-11**: 統計 hygiene / docstring 系。C系フェーズ完了時に対応

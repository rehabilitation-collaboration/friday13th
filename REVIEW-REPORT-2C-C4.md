# Code Review Report — Phase 2C-C4

**Date**: 2026-07-23 evening
**System**: MAGI(Sonnet×3: CASPER/BALTHASAR/MELCHIOR) + AKAGI(Opus×1)
**Target**: friday13th リポ Phase 2C-C4 差分
- `src/07_prefecture_by_prefecture_fit.py` (391行 → 460行, 新規 + fix)
- `src/06_figures.py` (272行 → 285行, 新規 + fix)
- `tests/test_prefecture_by_prefecture_fit.py` (263行 → 380行, 新規 + fix)
- `tests/test_06_figures.py` (86行, 新規)
- `tests/conftest.py` (+2 fixtures)

## Summary
- **MAGI 3体合議**: 26 raw findings → 18 unique (dedupe 後)
  - P1×1 / P2×8 / P3×9
- **AKAGI verdicts**: ACCEPT 15 / PARTIAL 3 / REJECT 0
- **AKAGI 独自 findings**: 9 items (P1×1 subsumed / P2×4 / P3×4)
- **即対応 fix**: **20 items** (P1 全 1 + P2 の 8/12 + AKAGI 独自 6 + P3 の 5/9)
- **C4-f defer**: 8 items (batched mechanical polish・DRY 抽出等)
- **C5 defer**: 2 items (manuscript 統合時)
- **GPT V2 flagged**: 1 item (HC1 選択理由説明)
- **pytest**: 142 → **179 pass** (+37: test_06_figures.py 8 + test_prefecture_by_prefecture_fit.py 拡張 12 + 07 の初期 17)
- **収束率**: 45/47 → **47/47** (Ehime/Okayama collinearity fix で 2 県復活)

## Critical Findings (P1)

| # | ID | Issue | Source | File:Line | Fix Status |
|---|-----|-------|--------|-----------|-----------|
| 1 | INDEP-cluster-singleton | 1-way date cluster SE は subset 内で singleton clusters (n=1) となり HC0 と等価。docstring の「Cameron-Miller G_date≈2192」justification は誤診断 (small G ではなく small size per cluster が問題)。実データ Aichi で cluster SE=0.04406 ≈ HC0=0.04373 (diff <1%)。manuscript-facing で「1-way date cluster SE」と report すると referee 撃墜。AKAGI B1 = model_notes 文字列に同一問題埋まってた (framing bomb) | MAGI(2/3) + AKAGI-independent(B1) | 07:19-21, 146-148, 357-362 | **FIXED**: `cov_type='cluster'` → `'HC1'`, `se_source='hc1_heteroscedasticity_robust'`, docstring + model_notes 全書き換え。全 45 converged prefecture で数値差 <2%、referee 対応上正確な label に統一 |

## Important Findings (P2)

| # | ID | Issue | Source | File:Line | Fix Status |
|---|-----|-------|--------|-----------|-----------|
| 2 | INDEP-ehime-okayama-collinearity | 非収束 2 県は snowfall_cm と snow_depth_max_cm の perfect collinearity (corr=1.000000)。SVD で null-space vector 上に 0.707/-0.707。Ehime=1 snow day, Okayama=2 snow days で全て snowfall==snow_depth 完全一致 | MAGI(3/3) | 07:120-127, 187 | **FIXED**: `_find_pairwise_collinear(threshold=0.999)` 追加 + `_find_dropped_covariates` combined helper 導入。**47/47 収束達成** (Ehime ratio=1.2554, Okayama ratio=1.1884 復活)。dropped_covariates_by_prefecture schema を `{col, reason}` に拡張 |
| 3 | B4 multi-test-disclosure | 5/45 CI excludes 1.0 だが Bonferroni/FDR 開示なし。binomtest(5,45,0.05,greater)=0.073 で null-compatible。C5 で "5 prefectures 有意" と書かれる selective reading リスク | MAGI(1/3) + AKAGI(B4) | 07:306-343 | **FIXED**: `build_truth_values` に 3 fields 追加 (`pref_by_pref_n_ci_excludes_one_binomial_p`, `pref_by_pref_n_bonferroni_significant`, `pref_by_pref_n_bh_fdr_significant`)。`_bh_fdr_significant` helper 新設 + 4 tests |
| 4 | 06-cli-silent-noop | `python 06_figures.py S2` (大文字) で silent no-op、"Done." 出力 | MAGI(1/3) | 06:263-268 | **FIXED**: argparse `--only choices=['s2','s3','all']` 導入、typo は SystemExit で reject |
| 5 | 06-missing-json-crash | 06 で入力 JSON 無い時 unhandled `FileNotFoundError` | MAGI(1/3) | 06:105, 175 | **FIXED**: `CASE_CROSSOVER_JSON.exists()` + `PREF_IRR_JSON.exists()` guard、None return + print "SKIPPED" (03 の diff_vs_prior pattern) |
| 6 | 06-non-conv-x1-fabrication | Figure S3 で非収束 prefecture を x=1.0 に「x」マーカーで plot。null line と重なって「no effect」に誤読される visual bomb | MAGI(1/3) + AKAGI(B7) | 06:195-206 | **FIXED**: 「x」マーカー削除、右端に "PrefName (n.c.)" text (italic, xlim[1]-0.03) のみ配置 |
| 7 | B2 se-source-per-row-drift | 非収束 row にも `se_source: "cluster_1way_date"` が書かれる (SE 計算されてないのに label 付き) | AKAGI-independent | 07:201, JSON results[*] | **FIXED**: 非収束時 `se_source=None`、収束時のみ `'hc1_heteroscedasticity_robust'` (P1 fix と合流) |
| 8 | B3 docstring-divergence-from-03 | 07 docstring "same weather+holiday specification as 03" だが実は mean model 同一で SE 手法根本異なる (2-way cluster vs HC1)。referee に "same specification" として誤認される | AKAGI-independent | 07:5-8 | **FIXED**: docstring rewrite で "reuses the mean model" + "SE necessarily differs" を明示 |
| 9 | 07-write-results-no-unittest | write_results/run_all_prefectures/load_prefecture_panel 直接 unit test 欠落。JSON snapshot テストのみ | MAGI(1/3) | tests/test_prefecture_by_prefecture_fit.py 全体 | **FIXED**: `test_write_results_direct_writes_valid_json` + `test_write_results_rejects_nan` + `test_load_prefecture_panel_returns_tuple` 追加 (tmp_path + fake results pattern) |
| 10 | B5 median-imputation-scope | `cloud_cover` NaN → panel-wide median で subset fit 前に計算 (per-prefecture median でない)。03 と consistent だが未文書化 | AKAGI-independent | 07:111 | **FIXED**: `load_prefecture_panel` docstring に "panel-wide, not per-prefecture — same choice as 03" 明記 |
| 11 | B9 collinearity-note-absent-from-JSON | dropped_covariates_by_prefecture の drop 理由が JSON にない (zero_var vs collinear が区別できない) | AKAGI-independent | 07:346-375 | **FIXED**: `dropped_covariates_by_prefecture` schema を `{col, reason}` object に拡張 (list of str → list of dict)。`dropped_reason` field を per-row 結果にも追加 |
| 12 | B8 listwise-N-drops-silent | 07 の load_prefecture_panel で listwise deletion 行数 print + JSON 記録欠落 (03 は print あり) | MAGI(1/3) + AKAGI-independent | 07:113-114 | **FIXED**: `load_prefecture_panel` が `(df, n_listwise_dropped)` tuple 返却 + print 追加 + JSON `diagnostics.n_listwise_dropped` field 追加 |

## Minor Findings (P3) — 即対応 fix

| # | ID | Issue | Source | Fix Status |
|---|-----|-------|--------|-----------|
| 13 | unused-imports (sys/math/numpy) | 07:56 sys, tests:13,15 math+numpy 未使用 | MAGI(3/3) | **FIXED**: 全 3 imports 削除 |
| 14 | unused-holiday-cols | 07:79 HOLIDAY_COLS 未使用 (BASE_MAIN_EFFECTS に既含) | MAGI(1/3) | **FIXED**: 削除 |
| 15 | B6 xlim-margin-lower | Figure S3 xlim=(0.3, 2.0) で Tottori CI-low=0.319 → margin 1.9% で whisker cap 視覚的にクリップ | MAGI(1/3) + AKAGI(B6) | **FIXED**: xlim=(0.28, 2.05) に拡大 (下側 margin 拡大 + 上側 3% 余裕) |
| 16 | 06-no-tests | 06_figures.py に test 無し | MAGI(1/3) | **FIXED**: `tests/test_06_figures.py` 新規 (8 tests: parse_args × 4 + .exists() skip × 2 + smoke test × 2) |
| 17 | docstring-stale-model-notes | 07 docstring の schema list に `model_notes`/`se_source`/`nb2_runtime_warnings` 欠落 | MAGI(1/3) | **FIXED**: docstring schema section 完全 rewrite |

## Priority Actions

### C4-f defer (batched mechanical polish・pre-flagged from 2C-C1/C3 + 07 追加分)

| # | ID | Issue | Deferred from |
|---|-----|-------|--------------|
| D1 | Z95-drift | 07 で `Z95=1.959963984540054`, 04/05 で `Z_CRIT_95=1.96`, 03 hardcode `1.96` の 3 種類 drift。数値影響 7.5e-6 で微小だが manuscript-facing で不都合 | 2C-C3 P3-e pre-flagged、07 で 3-form drift に escalate |
| D2 | DRY-fit-nb-core | Poisson warm start → NB2 iid → NB2 refit-with-cov の core loop が 02/03/04/07 で 4-copy | 2C-C1 P2-5 M12 pre-flagged |
| D3 | P2-A path duplication | ACCIDENTS_PARQUET 系 3 コピー → `src/_paths.py` | 2C-C3 P2-A |
| D4 | P3-e safe helpers | `_safe_float`/`_safe_exp`/`Z_CRIT_95` を `src/_stats_helpers.py` に統一 (04↔05↔07 統一) | 2C-C3 P3-e |
| D5 | CC=14/12 | 07 `fit_single_prefecture` CC≈14, `build_truth_values` CC≈12 (target≤8 だが 04 CC=21 の accepted precedent 範囲) | 2C-C4 新規 |
| D6 | argparse-missing | 07 に argparse 無し (04/05 は `_positive_int` パターン) | 2C-C4 新規 |
| D7 | 391-lines | 07 391 行超過 (accepted precedent 04=877/05=682 で許容範囲) | 2C-C4 新規 accept as-is |
| D8 | 07 pytest CC 分割余地 | fit_single_prefecture の try/except 連鎖を `_run_poisson_warm_start`/`_run_nb2_iid`/`_run_nb2_hc1` に分割可能 | 2C-C4 新規 |

### C5 defer (manuscript 統合時対応)

- Figure S3 caption: SE method (HC1) 明示 + Ehime/Okayama recovery 経緯 (pairwise collinearity check で救済) 一行言及
- Multi-test disclosure prose: binomial p=0.073 + Bonferroni n=1 (Mie) + BH-FDR n=1 (Mie) を prefecture-forest discussion paragraph で明示

### C4 GPT V2 round flagged (次 GPT 査読で対応)

- **HC1 選択理由の説明**: PLAN L44 は "cluster SE" 想定 (実装 defer なし)。GPT V2 が "why HC1 not cluster within subset" と問うた場合、"within a single-prefecture subset each date has 1 obs, so cluster reduces to HC0 with a small finite-sample scaling; HC1 is the honest label with (N/(N-K)) correction" と答える。PLAN-DEVIATIONS.md #2 起票不要 (mean model 保持・SE 手法だけ変更で範囲内)

## Rejected by AKAGI

| # | MAGI Finding | Rejection Reason |
|---|-------------|-----------------|
| - | (なし) | 全 18 findings が ACCEPT or PARTIAL (3 PARTIAL は severity/scope 調整のみ) |

## Review Statistics

- MAGI: 40項目 × 3 agents = 120 checks
- Raw findings: 26 (CASPER 10 + BALTHASAR 11 + MELCHIOR 6, 重複 dedupe 前)
- Unique findings after dedupe: 18 (P1×1 / P2×8 / P3×9)
- AKAGI verdicts: ACCEPT 15 / PARTIAL 3 / REJECT 0
- AKAGI independent findings: 9 (P1×1 subsumed by MAGI P1 / P2×4 / P3×4)
- 即対応 fix: 20 items (P1×1 + P2 全 12 + P3×5 + AKAGI 独自 6)
- Defer: 8 (C4-f batched) + 2 (C5 manuscript) + 1 (GPT V2)
- pytest baseline → after: 142 → **179 pass** (+37)
- 収束率 baseline → after: 45/47 (95.7%) → **47/47 (100%)**

## Key Empirical Findings from AKAGI Reproduction

- **cluster/HC0 ratio**: min=1.007147 max=1.007649 mean=1.007553 across all 45 originally-converged prefectures — 定数 1.008 scaling = `sqrt((G/(G-1))×((N-1)/(N-K)))` for G=N=2192, K≈32 (statsmodels finite-sample correction for cluster MLE with singleton clusters)
- **iid/cluster ratio**: min=0.7750 max=1.5278 mean=1.1268 — 実質的 inflation は cluster→iid で 12% (方向は cluster<iid が 31/45)
- **HC1 vs cluster diff**: ~0.8% で数値的にほぼ同一。P1 fix は数値ではなく **label の正確性** の問題
- **Ehime/Okayama corr(snowfall, snow_depth)**: 1.00000000 (SVD 確認済) → pairwise collinearity check で救済可能

## Notes for C5 (Manuscript Integration)

**scaffold**: 07 の `model_notes` 文字列は manuscript verbatim コピー可能 (fact-check 済・HC1 明示・pairwise collinearity 経緯明記)。ただし C5 は必ず `output/prefecture_irr_by_prefecture.json['model_notes']` を最初に読んで最新版と一致させること。

**multi-test disclosure**: JSON に 3 field 永続化済 (`n_ci_excludes_one=5`, `n_ci_excludes_one_binomial_p=0.073`, `n_bonferroni_significant=1`, `n_bh_fdr_significant=1`)。C5 manuscript の Figure S3 discussion paragraph でこの 4 数値を「5 prefectures nominal α=0.05, but under BH-FDR q=0.05 only Mie survives; under Bonferroni α_family=0.05 also only Mie; binomial test of excess p=0.073 fails to reject the null-everywhere hypothesis」と 1-2 文で開示。

**Figure S3 caption 提案**: "Per-prefecture Fri13 count ratios (95% CI, HC1-robust) from separate NB2 fits reusing the mean model of Table X's primary panel (2C-C2-e). Two prefectures (Ehime, Okayama) required dropping snow_depth_max_cm due to perfect collinearity with snowfall_cm (1-2 snow days in the study period); six prefectures with year-round zero snowfall (Kagawa, Miyazaki, Oita, Okinawa, Osaka, Shizuoka) required dropping both snow covariates. All 47 prefectures converged."

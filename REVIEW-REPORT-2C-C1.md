# Code Review Report (Phase 2C-C1)
Date: 2026-07-23
System: MAGI(Sonnet×3: CASPER/BALTHASAR/MELCHIOR) + AKAGI(Opus×1)
Target:
- `src/04_diagnostics.py` (NEW, ~877 lines — 6 diagnostics + Methods draft + Cameron-Miller pair cluster bootstrap 手実装)
- `tests/test_diagnostics.py` (NEW, ~180 lines, 21 tests)
- `tests/conftest.py` (MODIFIED, +2 fixtures at end)
- `requirements.txt` (NEW, pinned deps for venv)
- `output/diagnostics_results.json` (generated artifact)
- `output/figures/S1_pearson_residuals_03_primary.png` (Figure S1)

Empirical anchor (`output/diagnostics_results.json`):
- 03_primary NB2 z-based: count_ratio=1.0248, cluster SE=0.0267, p=0.360
- 03_primary bootstrap (500 iter, conv_fail=0): CI=[0.9918, 1.0565], p_two_sided=0.136
- 03_primary Pearson resid: sd=1.013, prop|r|>2=4.4%, prop|r|>3=0.69% (theoretical 0.27% → 2.6x fat tail)
- Spec sensitivity max_delta=0.0004 (dummy vs harmonic); spline excluded
- HC1 SE=0.0151 (= iid SE), HC1/cluster_2way = 0.56
- pytest 97/97 pass

## Critical Findings (P1)

| # | ID | Issue | Source | File:Line | Action Required |
|---|-----|-------|--------|-----------|----------------|
| P1-1 | M1 (CASPER) | **`build_methods_draft_c1` crashes with KeyError when bootstrap has <10 successful iter**. The guard `"n_iter_successful" in boot03` matches BOTH the success dict AND the `<10 successful` failure dict (both contain that key), but the failure dict lacks `count_ratio_ci_low_boot/ci_high_boot/p_two_sided_boot`. AKAGI reproduced via synthetic payload. Called at line 827 BEFORE `write_results` at line 870 → crash loses entire ~70min bootstrap compute for all 4 specs with no JSON written. | CASPER + AKAGI empirical | src/04_diagnostics.py:736,746-748 | Change guard to `"count_ratio_ci_low_boot" in boot03` (or `"error" not in boot03`). 1-line fix. |
| P1-2 | M2 (BALTHASAR) + B1 (AKAGI extension) | **Pair cluster bootstrap resamples ONLY the prefecture axis, never the date axis** — but `is_fri13` is a date-level treatment with only 10 treated dates. Every boot draw reuses the identical fixed set of Fri13 shocks. AKAGI empirical variance decomposition: bootstrap SD=0.0159 ≈ iid SE=0.0151 (5% wider) ≈ HC1 SE=0.0151 (0% wider), vs cluster_2way SE=0.0267 (77% wider than iid). **The bootstrap essentially reproduces iid variance and DOES NOT capture the date-clustered variance that dominates cluster SE.** Consistent with observed CI narrowing (0.083 boot vs 0.107 z-based) — this is under-coverage on the date axis, NOT finite-G correction. Methods draft paragraph 6 claims "prefecture-cluster-robust inference for finite G=47" without disclosing this limitation. p_boot=0.136 is not a corroboration of cluster p=0.360 — it is an estimator that ignores the dominant variance source. | BALTHASAR + AKAGI-independent variance decomp | src/04_diagnostics.py:543-659 + Methods draft para 6 | Rewrite Methods draft bootstrap paragraph with honest disclosure. Two options: (a) drop bootstrap p entirely, report only z-based cluster p=0.360 with G_pref=47 rank-deficiency caveat; (b) keep bootstrap with explicit statement "prefecture-axis pair cluster bootstrap; under-covers date-level variance (0.0159 boot SD vs 0.0267 cluster SE); provides sensitivity only to prefecture-cluster misspecification". **Selected: (b)** — informative + honest, retains diagnostic value. Add MC SE and note bootstrap resamples on prefecture only. |
| P1-3 | M3 (BALTHASAR) | **Spline rank-deficiency root cause claim is EMPIRICALLY WRONG**. Code error string says "collinearity between spline basis and year FE at panel scale" — BALTHASAR + AKAGI reproduced with direct test: removing year FE keeps deficiency at 1; removing intercept RESTORES full rank. True cause = B-spline partition-of-unity (bs basis columns sum to ≈ 1 across rows, near-collinear with intercept `const`), NOT year FE. **This wrong claim is baked into `output/diagnostics_results.json['methods_draft_c1']['paragraphs'][4]` for Phase 2C-C5 manuscript reuse**. Publishing an incorrect statistical claim in Methods is worse than omitting the spline attempt entirely. | BALTHASAR + AKAGI empirical | src/04_diagnostics.py:466 (error string), Methods draft paragraph 5 | Fix error string to accurate root cause: "collinearity with intercept (B-spline partition-of-unity artifact)". Fix Methods draft paragraph 5 spline_note wording accordingly. |
| P1-4 | B3 (AKAGI independent) | **`payload["methods_draft_c1"] = build_methods_draft_c1(payload)` runs INSIDE `run_all_diagnostics` at line 827 BEFORE `write_results` at line 870**. Any exception in `build_methods_draft_c1` — including M1's KeyError, OR any new formatting error added later — throws away ~70 min compute with no JSON written. Amplifies M1's blast radius. | AKAGI-independent | src/04_diagnostics.py:827 (in run_all_diagnostics) → 869-870 (main) | Reorder: (1) `write_results(payload_without_methods_draft, out_path, ...)` FIRST; (2) `try: payload["methods_draft_c1"] = build_methods_draft_c1(payload); write_results(payload, out_path, ...) except Exception as exc: print warning`. Ensures raw diagnostics are always persisted even if draft formatting fails. |
| P1-5 | M5 (3/3: CASPER+BALTHASAR+MELCHIOR) | **`pearson = payload["pearson_residuals"]` extracted in `build_methods_draft_c1` but never referenced**. Pearson diagnostic (b) — one of the six documented diagnostics — is entirely absent from the Methods draft. This selectively omits the ONE mildly unfavorable finding: `prop|r|>3 = 0.69%` for 03_primary vs theoretical 0.27% for N(0,1) (~2.6x fat tail), a mild misspecification signal. All 5 diagnostics that support the null are written up in full. For a permanent-public paper this reads as selective disclosure — scientific integrity concern. `test_json_methods_draft_populated` only asserts `len ≥ 4` so this gap is untested. | 3/3 vote + AKAGI confirm | src/04_diagnostics.py:668,754-758 | Add a Pearson paragraph to Methods draft with sd/prop|r|>2/prop|r|>3 numbers and honest fat-tail acknowledgment. Update `test_json_methods_draft_populated` to require each of the 6 diagnostics to be represented. |
| P1-6 | B4 (AKAGI independent) | **Methods draft paragraph 6 (bootstrap) makes claims that exceed what the diagnostic supports**. Asserts bootstrap "corroborates the null-everywhere claim under prefecture-cluster-robust inference for finite G=47". Per B1, the bootstrap is NOT prefecture-cluster-robust in a meaningful sense — variance essentially iid. Also does not disclose the 2.6x p-value discrepancy (0.136 vs 0.360) or reconcile it. For SSRN submission this will not survive referee scrutiny. | AKAGI-independent | src/04_diagnostics.py:737-751 | Same rewrite as P1-2. Cover: (i) resampling axis (prefecture only), (ii) variance decomposition (boot ≈ iid), (iii) which p is primary and which is sensitivity, (iv) MC SE at 500 iter. |

## Important Findings (P2)

| # | ID | Issue | Source | File:Line | Action Required |
|---|-----|-------|--------|-----------|----------------|
| P2-1 | M4 (2/3 CASPER+MELCHIOR) | `hc1_diagnostic` reruns NB2 with `cov_type='HC1'` but never checks `fit_hc1.mle_retvals.get('converged', False)`. Every sibling MLE refit in this file explicitly checks. Silent bogus SE risk. | 2/3 vote | src/04_diagnostics.py:368-395 | Add explicit convergence check; raise or skip on failure. |
| P2-2 | M6 (CASPER) | `quasi_poisson_diagnostic` uses `sm.GLM(...).fit(scale='X2')` twice with no `.converged` inspection; also uses raw `math.exp`/`float` not `_safe_exp/_safe_float`. Non-convergence → silent bogus SE or later `allow_nan=False` crash at write_results. | 1/3 + AKAGI ACCEPT | src/04_diagnostics.py:336-362 | Add convergence check; use `_safe_exp`/`_safe_float` in CI construction. |
| P2-3 | M7 (2/3 CASPER+MELCHIOR) | `_safe_float`/`_safe_exp` were built specifically for NaN→None sanitization pre-`allow_nan=False` JSON write, but only used inside `spec_sensitivity_diagnostic`. The other 4 diagnostics (a/b/c/d1) use raw `float`/`math.exp` — a NaN on future data raises uncaught at `write_results` after the entire ~70min run. | 2/3 vote | src/04_diagnostics.py:210-395 | Apply `_safe_float`/`_safe_exp` uniformly across all 4 diagnostic result-dict construction sites. |
| P2-4 | M10 (2/3 BALTHASAR+MELCHIOR) | PLAN L44/125/192 specifies `wildboottest` one-way Rademacher wild-cluster bootstrap × 1000 iter. Actual = Cameron-Miller pair cluster bootstrap × 500 iter (different family + halved iter). The wildboottest-incompatibility rationale (NB2 nonlinear, not OLS) is disclosed in code docstring, but NOT the well-documented weaker small-G coverage of pair-vs-wild bootstrap, nor the halved iter count. `PLAN-DEVIATIONS.md` does not exist in the repo. | 2/3 vote + AKAGI ACCEPT | PLAN vs src/04_diagnostics.py:16-32,75 | Create `PLAN-DEVIATIONS.md` (deviation #7 under this PLAN) recording: actual method, iter count, reasoning, statistical caveats (pair vs wild). Cross-reference from handoff. |
| P2-5 | M12 (MELCHIOR) | `fit_nb2_with_objects` in 04 is 3rd copy of the Poisson-warmstart→NB2-iid→NB2-cluster sequence (also in 02/03 `fit_nb_panel`). Prior review said "2-copy allowed"; this crosses the 3-copy DRY threshold (`code-quality.md §4`). | 1/3 + AKAGI ACCEPT | src/04_diagnostics.py:166-204 vs 02/03 fit_nb_panel | **Deferred** — extracting to `src/_panel_nb_helpers.py` requires touching 02/03 which are non-touch this phase. Record for next phase (2C-C3 or C5). |
| P2-6 | M13 (MELCHIOR) | JSON key `wildboot_pref_only` names the diagnostic after the abandoned wild-cluster approach; actual implementation is pair cluster bootstrap. Misleading for tests + future manuscript-integration code. | 1/3 + AKAGI ACCEPT | src/04_diagnostics.py:672,825 + test file | Rename to `pair_cluster_boot_pref_only`. Update tests + JSON (in-place key rename). |
| P2-7 | M14 (MELCHIOR) | Cyclomatic complexity: `spec_sensitivity_diagnostic=21`, `build_methods_draft_c1=21`, `pair_cluster_bootstrap=18`. All 2-2.6x the ≤8 target (`code-quality.md §2`). | 1/3 + AKAGI ACCEPT | src/04_diagnostics.py:452,543,665 | **Deferred** — extraction to per-kind/per-paragraph helpers is real refactor; not blocking for SSRN. Log for next phase. |
| P2-8 | M15 (MELCHIOR) | Figure S1 histogram has no explicit x-axis limit; auto-scale to [-5, 11.2] (extreme outliers) compresses the bulk into ~1/3 of the panel. Permanent supplementary figure. | 1/3 + AKAGI ACCEPT | src/04_diagnostics.py:308-320 + PNG | Add `axes[0].set_xlim(-5, 5)` (1 line); regenerate figure. |
| P2-9 | M17 (BALTHASAR) | Zero unit tests for the 6 core diagnostic functions themselves (dispersion, pearson, quasi_poisson, hc1, spec_sensitivity, pair_cluster_bootstrap, `_build_design_alt_seasonality`). All 21 tests are helpers OR JSON snapshot. Snapshot tests don't localize failures or test edge cases (NaN inputs, degenerate designs, zero-iter bootstrap). | 1/3 + AKAGI ACCEPT | tests/test_diagnostics.py | Add ≥1 direct-invocation unit test per core function with small synthetic inputs. |
| P2-10 | B5 (AKAGI independent) | Bootstrap MC SE at p ≈ 0.14, n_iter=500 is ≈ sqrt(0.14×0.86/500) ≈ 0.016, so p=0.136 ± 0.016 could straddle 0.10 across seeds. Neither MC SE nor seed sensitivity documented in JSON or Methods draft. | AKAGI-independent | src/04_diagnostics.py + JSON | Add `bootstrap_mc_se_approx` field to bootstrap section; add sentence about MC SE to Methods bootstrap paragraph (part of P1-2/P1-6 rewrite). |
| P2-11 | B7 (AKAGI independent) | `spec_sensitivity_diagnostic` (CC=21) and `build_methods_draft_c1` (CC=21) both mix per-spec/per-diagnostic loop with formatting. Standard extraction into per-kind / per-paragraph helpers would halve CC. | AKAGI-independent | src/04_diagnostics.py:452,665 | **Deferred with P2-7**. |

## Minor Findings (P3)

| # | ID | Issue | Source | File:Line | Action Required |
|---|-----|-------|--------|-----------|----------------|
| P3-1 | M8 (3/3) | 04_diagnostics.py = 877 lines, 3x the 300-line guideline. Research script with 6 diagnostics + Methods draft + CLI; AKAGI downgrades P2→P3 given script-not-library nature. Existing project precedent: `02_main_analysis.py` = 1011 lines. | 3/3 vote | src/04_diagnostics.py | **Accepted as-is** given precedent. Split candidate for P2-7/P2-11 future refactor. |
| P3-2 | M9 (3/3) | `pair_cluster_bootstrap` = 117 lines (over 100-line guideline). | 3/3 vote | src/04_diagnostics.py:543-659 | **Deferred** with P2-7 refactor. |
| P3-3 | M11 (2/3 CASPER+MELCHIOR) | `linearmodels==7.0` + `wildboottest==0.3.2` pinned in requirements but never imported. Leftover from abandoned wild-cluster approach. | 2/3 vote | requirements.txt:14-15 | Remove both pins. |
| P3-4 | M16 (BALTHASAR) | QP Methods paragraph claims "NB2 count ratio matched within four decimals, indicating that dispersion structure does not drive the null" — technically overstated. NB2 and QP share log-link mean model; near-equal point est is EXPECTED regardless of dispersion adequacy. Scale factor 1.44 is more informative. | 1/3 + AKAGI (partial ACCEPT, downgrades P2→P3) | src/04_diagnostics.py:702-710 | Rephrase: "QP scale factor 1.44 indicates modest extra-Poisson variance, comparable to what NB2 alpha=0.023 captures". |
| P3-5 | M18 (CASPER) | `ratio_ratio = (nb1_alpha / nb2_alpha) if (nb1_alpha and nb2_alpha) else None` uses truthiness; adjacent line uses `is not None`. alpha=0.0 would silently drop. Near-impossible for MLE alpha to hit exact 0.0. | 1/3 + AKAGI ACCEPT | src/04_diagnostics.py:250 | Change to `if nb1_alpha is not None and nb2_alpha is not None`. |
| P3-6 | M19 (MELCHIOR) | Z-critical 1.96 hardcoded 6 times in `quasi_poisson_diagnostic` + `spec_sensitivity_diagnostic`. 02/03 centralize in `_extract()`. | 1/3 + AKAGI ACCEPT | src/04_diagnostics.py:358-361,487-488 | Introduce module-level `Z_CRIT_95 = 1.96`. |
| P3-7 | M20 (MELCHIOR) | Bootstrap per-iter loop uses `warnings.simplefilter("ignore", RuntimeWarning)` — silently discards numerical-instability warnings. No counter for "converged=True but numerically suspect". Contrary to file's own precedent (`fit_nb2_with_objects` captures via record=True). | 1/3 + AKAGI ACCEPT | src/04_diagnostics.py:588-598 | Change to `record=True`; count `n_iter_with_runtime_warnings` in the return dict. |
| P3-8 | M21 (MELCHIOR) | `adjusts_weather_holiday` set in all 4 spec dicts but never read. Dead field. | 1/3 + AKAGI ACCEPT | src/04_diagnostics.py:131,140,149,158 | Remove all 4 assignments. |
| P3-9 | M22 (MELCHIOR) | Module docstring line 23 says `spline: bs(day_of_year, df=6)`, actual code line 435 says `df=3`. PLAN says df=6 (also stale). | 1/3 + AKAGI ACCEPT | src/04_diagnostics.py:23 vs 426,435 | Fix docstring to `df=3`. Note PLAN itself does not need update (PLAN describes the target; the deviation to df=3 is recorded in PLAN-DEVIATIONS.md per P2-4). |
| P3-10 | M23 (MELCHIOR) | Two defensive branches (SE>100 cap; `<10 iter` fallback) never exercised by current data. `<10 iter` branch is now known unsafe per P1-1. | 1/3 + AKAGI ACCEPT | src/04_diagnostics.py:481-482,620-631 | `<10 iter` branch fix is subsumed by P1-1. SE>100 cap kept as-is with existing inline comment. |
| P3-11 | B2 (AKAGI independent) | `_load_src_module` caches modules in `sys.modules`. Two specs share `mod_02`, two share `mod_03`. If 02/03 later grow module-level DataFrame caches (e.g., `@lru_cache` on `load_prefecture_panel`), sensitivity spec fits would inherit primary-spec state. Currently benign. | AKAGI-independent | src/04_diagnostics.py:109-116,121-122 | Advisory only; add a comment noting the assumption of pure loaders. |
| P3-12 | B6 (AKAGI independent) | Mixed use of `is_fri13_coef` (log scale, 6 diagnostics) vs `count_ratio` (linear scale, 4 diagnostics) in same result dicts. Adjacent fields `is_fri13_coef_ci_low_boot` + `count_ratio_ci_low_boot`. 02/03 use only `count_ratio_*` externally. | AKAGI-independent | src/04_diagnostics.py various | **Deferred** — schema-breaking rename requires test updates; not blocking. Log for next phase. |
| P3-13 | B8 (AKAGI independent) | Bootstrap seed=20260723 hardcoded default; `rng.choice(clusters, size=G, replace=True)` depends on `pd.unique()` first-appearance order. Any change to input parquet row order would silently produce different bootstrap draws under the same seed. | AKAGI-independent | src/04_diagnostics.py:551,569 | Sort `clusters` alphabetically before use to make deterministic across row-order changes. |
| P3-14 | B9 (AKAGI independent) | `adjusts_weather_holiday` dict field is dead (P3-8), but paragraph 1 hardcodes "weather+holiday-adjusted primary fit" in the string. Duplicate signal, disconnected. If a new spec is added, prose won't update. | AKAGI-independent | src/04_diagnostics.py:131,140,149,158 vs 682 | Subsumed by P3-8 removal; ensure paragraph 1 template references `spec_label.startswith("03_")` if it needs to specialize. Currently OK to leave string as-is since only 03_primary is used for the draft. |

## Rejected by AKAGI

| # | MAGI Finding | Rejection Reason |
|---|-------------|-----------------|
| (無) | ― | 23 MAGI findings 全て ACCEPT (0 REJECT)。M2/M3 は AKAGI independent 実測で firm P1 化。M14/M15/M16 は severity 調整 (P2→P3) のみ。 |

## Review Statistics

- **MAGI**: 3 agents × 40 checklist items, aggregate 23 unique findings
  - CASPER-2: 7 findings (P1×1 / P2×2 / P3×4)
  - BALTHASAR-2: 8 findings (P1×2 / P2×4 / P3×2)
  - MELCHIOR: 16 findings (P1×0 / P2×9 / P3×7)
  - Vote overlap: 3/3 votes on M5/M8/M9; 2/3 on M4/M7/M10/M11
- **AKAGI verification**: ACCEPT 23 / REJECT 0 (severity 調整: 6件 P2→P3)
- **AKAGI independent**: 9 items (B1-B9 = P1×3, P2×2, P3×4)
- **Composite severity**: **P1×6 / P2×11 / P3×14 = 31 findings**

## AKAGI 深掘り所見

1. **Bootstrap variance decomposition が最も強い empirical evidence**
   - AKAGI 実測 (03_primary): bootstrap SD=0.0159, iid SE=0.0151, HC1 SE=0.0151, cluster_2way SE=0.0267
   - bootstrap は iid variance を 5% wider に再現しただけ = 実質 iid 推定
   - **date-cluster shocks (Fri13 の 10 dates) が固定** → date-cluster 変動を捕捉できない
   - Methods draft para 6 の「prefecture-cluster-robust inference for finite G=47」主張は referee scrutiny を通らない

2. **Spline root cause の empirical falsification**
   - AKAGI 独立検証: `_build_design_alt_seasonality` recipe そのままで直接テスト
     - full = 71 col, rank 70 (deficient by 1)
     - year FE 削除 = still deficient by 1
     - intercept 削除 = full rank restored
   - **true cause = B-spline partition-of-unity artifact (basis rowsum ≈ 1, const 列と near-collinear)**
   - Methods draft para 5 に既に誤情報が焼き込まれている → 2C-C5 コピー禁止

3. **Methods draft は scaffold として扱う (verbatim コピー禁止)**
   - M3 (spline 誤診断) + B4 (bootstrap over-claim) + M5 (Pearson 省略) + M16 (dispersion 表現) = substantive editing 必須
   - 2C-C5 で manuscript 反映時、para 単位で fact-check する

4. **Bootstrap reporting for SSRN (AKAGI 推奨)**
   - Option (a): drop bootstrap p entirely, cluster p=0.360 only + G_pref=47 rank-deficiency caveat
   - Option (b): keep bootstrap + explicit disclosure of resampling axis limitation
   - **推奨 = (b)** (informative + honest, 診断の価値保持)
   - **または (a)** も accept 可 (safer for referees, wall time 短縮 = 35分 bootstrap 不要になる)

5. **`build_methods_draft_c1` の実行位置 = write_results 前 = 70分 loss リスク**
   - B3: 順序を変えて raw diagnostics を先 write、methods draft は second-pass write でカプセル化
   - M1 の fix + この reorder で double 冗長 (どちらか片方でも防げるが両方するのが安全)

## 推奨アクションプラン

### 即対応 (Phase 2C-C1 完了扱いにする前)

1. **P1-1 (M1 KeyError guard)**: 1-line fix
2. **P1-4 (B3 reorder)**: write_results を 2 段階に (先 raw、後 methods_draft 付き)
3. **P1-3 (M3 spline root cause)**: error string + Methods draft paragraph 5 の 2 箇所修正
4. **P1-2/P1-6 (M2/B4 bootstrap disclosure)**: Methods draft paragraph 6 全書き直し + JSON bootstrap section に `mc_se_approx` 追加
5. **P1-5 (M5 Pearson paragraph)**: Methods draft に Pearson section 追加 + test 更新 (6 診断全 coverage assertion)
6. **P2-1/P2-2 (M4/M6 convergence check)**: hc1_diagnostic + quasi_poisson_diagnostic に `.converged` check 追加
7. **P2-3 (M7 safe_* uniformity)**: 4 diagnostic に `_safe_float`/`_safe_exp` 統一適用
8. **P2-6 (M13 rename)**: `wildboot_pref_only` → `pair_cluster_boot_pref_only` (code + test + 既存 JSON in-place rename)
9. **P2-8 (M15 figure xlim)**: `axes[0].set_xlim(-5, 5)` + figure 再生成
10. **P2-9 (M17 unit tests)**: 6 診断関数 × 1-2 direct-invocation test 追加
11. **P2-4 (M10 PLAN-DEVIATIONS)**: `PLAN-DEVIATIONS.md` 新規作成 (deviation #7 = wildboottest → pair cluster bootstrap + 500 iter)
12. **P3-3 (M11 unused deps)**: `wildboottest` / `linearmodels` を requirements.txt から削除
13. **P3-4 (M16 QP wording)**: 1 sentence rephrase
14. **P3-5 (M18 truthiness)**: `is not None` に統一
15. **P3-6 (M19 Z_CRIT_95)**: 定数化
16. **P3-7 (M20 warnings capture)**: `record=True` + counter
17. **P3-8 (M21 dead field)**: `adjusts_weather_holiday` 削除
18. **P3-9 (M22 docstring)**: `df=6` → `df=3`
19. **P3-13 (B8 seed determinism)**: `clusters` を sort してから resample
20. **JSON 再生成**: `--skip-bootstrap` mode で methods_draft + spec_sensitivity 部分だけ再生成、bootstrap セクションは既存を Python one-liner で key rename して保持 (bootstrap 500 iter 再走 = 35 分 avoid)
21. **pytest 全 pass 確認** (97 → ~105+ 期待)

### 2C-C3 以降で対応 (次フェーズ)

22. **P2-5 (M12 DRY 抽出)**: `src/_panel_nb_helpers.py` に fit_nb2 sequence を extract、02/03/04 の 3 copy を統合。04 sensitivity spec (04-alt/05) 追加時のトリガに合わせる
23. **P2-7/P2-11 (M14/B7 CC refactor)**: `spec_sensitivity_diagnostic` / `build_methods_draft_c1` / `pair_cluster_bootstrap` を per-helper に分割
24. **P3-1/P3-2 (M8/M9 line length)**: P2-7 refactor 完了時に自然解消想定
25. **P3-11 (B2 sys.modules cache 注意)**: advisory コメント追加のみ
26. **P3-12 (B6 coef vs count_ratio schema)**: 04/05 sensitivity spec 追加時に schema統一

### Phase 2C-C5 (manuscript 反映) で対応

27. **Methods draft は scaffold 扱い**: para 単位で fact-check、verbatim コピー禁止
28. **Bootstrap 報告**: Option (b) 誠実 disclosure (variance decomposition + MC SE + resampling axis limitation)
29. **旧 Näyhä [0.54, 1.94] + 2C-c panel [0.955, 1.094] + 2C-e weather+holiday [0.9725, 1.0799] の 3 段並記** に加え、pair bootstrap [0.9918, 1.0565] を **sensitivity 位置づけ** で追記 (primary は依然 cluster z-based)

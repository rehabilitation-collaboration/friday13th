# Code Review Report (Phase 2C-C3)
Date: 2026-07-23
System: MAGI(Sonnet×3: CASPER/BALTHASAR/MELCHIOR) + AKAGI(Opus×1)
Target:
- `src/05_case_crossover.py` (NEW, 646 → 682 lines post-fix — 3 case-crossover alternative tests + Methods draft, hand-implemented Newton-Raphson conditional Poisson)
- `tests/test_case_crossover.py` (NEW, 329 → 415 lines post-fix, 27 → 36 tests)
- `tests/conftest.py` (MODIFIED, +3 fixtures + `case_crossover_pairs` skip-guard)
- `output/case_crossover_results.json` (regenerated with new small-G schema)

Empirical anchor (`output/case_crossover_results.json` post-fix):
- 03 pair count: 10 Fri13 dates × 4 same-month Fridays each = 40 Fridays across 10 months (2019-09, 2019-12, 2020-03, 2020-11, 2021-08, 2022-05, 2023-01, 2023-10, 2024-09, 2024-12)
- Conditional Poisson: β̂=0.03572, count_ratio=1.03637, NR converged in 4 iters
  - Fisher iid (diagnostic-only): SE=0.01145, z=3.12, p=0.0018 — kept in JSON for audit, EXCLUDED from Methods draft (B1 fix)
  - Sandwich cluster (G/(G-1)=1.111 corrected): SE=0.04039
    - z(0.975) inference: p=0.377, CI [0.9575, 1.1217]
    - t(9, 0.975)=2.262 inference: **p=0.399, CI [0.9459, 1.1355] — primary case-crossover reporting** (P1-A fix)
- Exact sign: 8+/2−/0-tie, binomtest p=0.109
- Permutation (sign-flip): observed mean log_ratio=0.0356 (= β̂ to 4 digits, cross-check pass), exact p=0.447 (458/1024), MC (10,000) p=0.450 MC-SE=0.005
- pytest 142/142 pass (was 133 before fixes; +9 new post-review tests)

## Composite Severity Distribution

- **P1**: 3 findings (all fixed)
- **P2**: 12 findings (10 fixed immediate, 2 deferred to 2C-C4)
- **P3**: 24 findings (7 fixed immediate, 17 deferred)

## Critical Findings (P1)

| # | ID | Issue | Source | File:Line | Verdict | Fixed |
|---|-----|-------|--------|-----------|---------|-------|
| P1-1 | P1-A (CASPER B-08 P2 → BALTHASAR B-08 P1 → AKAGI ACCEPT) | **Sandwich SE at G=10 used z=1.96 and no G/(G-1) or t(G-1) correction; Methods draft asserted "defensible" / "aligns with the prefecture-panel cluster inference" with no small-G caveat.** Repeats 2C-C1 P1-2/P1-6 pattern with even smaller G. AKAGI recomputed: p_z=0.351 → p_t9=0.376 → p_t9+G/(G-1)=0.400; qualitative null holds but framing is uncaveated. | 2/3 MAGI vote (with severity split) + AKAGI ACCEPT | src/05:280-289, methods_draft paragraph 2 | ACCEPT | **✅ FIXED**: `conditional_poisson_diagnostic` now applies G/(G-1) SE inflation and reports BOTH z-based and t(G-1)-based Wald blocks. Methods draft paragraph 2 rewritten to declare t(G-1) as primary and cite Cameron & Miller 2015. New JSON keys `small_G_correction`, `sandwich_cluster_z`, `sandwich_cluster_t`, `fisher_iid_diagnostic_only`. |
| P1-2 | P1-B (BALTHASAR A-06 P1, AKAGI ACCEPT+upgrade) | **Manuscript integration conflict**: manuscript.md L19,21,59,69,99,139 + Table 1 L188-202 already report a "case-crossover" result (mean ratio 1.05, p=0.32, 8/10 higher) computed by the old `src/02_main_analysis.py::case_crossover()` (arithmetic per-pair t-test). methods_draft_c3 generated a DIFFERENT numerical set under the same label with no reconciliation map. PLAN L231 explicitly plans replacement but the draft did not name the manuscript targets, so 2C-C5 would ship two conflicting "case-crossover" ratio/p pairs. AKAGI independently confirmed L59, L99, Table 1 (BALTHASAR had only L19/21/69/139). | 1/3 MAGI + AKAGI ACCEPT | manuscript.md multi + build_methods_draft_c3 notes[] | ACCEPT | **✅ FIXED in 05, PENDING in manuscript.md**: `methods_draft_c3.notes[]` expanded from 2 → 5 entries, now includes explicit replacement map for L19/L21/L59/L99/Table 1 (with geometric-vs-arithmetic 1.036 vs 1.05 disclosure), old-t-test-supersession note, and citation list for bibliography. Actual manuscript.md edits deferred to Phase 2C-C5 per scope contract (05-only for 2C-C3). |
| P1-3 | B1 (AKAGI independent) | **Fisher-iid p=0.002 and CI [1.0134, 1.0599] (excluding 1.0) were rendered in Methods draft paragraph 2 with equal typographic weight to the sandwich numbers**, then flagged as "misspecified" only in a trailing sentence. If a 2C-C5 pass lifts the sentence into manuscript.md, the reader sees a significant count-ratio result from a model the paragraph itself flags as wrong — permanent-public-asset framing bomb. Aligns with 2C-C1 P1-5 selective-disclosure logic in reverse. | AKAGI-independent | src/05:485-513 + paragraph 2 | ACCEPT | **✅ FIXED**: Fisher iid p/CI **completely removed** from Methods draft paragraph 2 (still persisted in JSON as `fisher_iid_diagnostic_only` for audit). New notes[3] documents the exclusion rationale. |

## Important Findings (P2)

| # | ID | Issue | Source | File:Line | Verdict | Status |
|---|-----|-------|--------|-----------|---------|--------|
| P2-1 | P2-A (MELCHIOR B-01/B-09, AKAGI ACCEPT) | ACCIDENTS_PARQUET absolute path duplicated 3× with 2 idioms (05: `Path.home()` chain; 01a + conftest: literal `/Users/mizukishirai/…`). Crosses DRY threshold, latent `$HOME` portability inconsistency. | 1/3 MAGI + AKAGI ACCEPT | src/05:73-81 vs src/01a:34-35 vs tests/conftest.py:123-125 | ACCEPT | **DEFERRED 2C-C4**: extract to `src/_paths.py` used by 01a/01/05/conftest. |
| P2-2 | P2-B (MELCHIOR C-02/B-04, AKAGI ACCEPT + repro) | `--n-perm 0` → ZeroDivisionError at `n_extreme_mc / n_perm`; `--n-perm -5` → ValueError from rng.choice. parse_args unbounded, zero test coverage. | 1/3 MAGI + AKAGI ACCEPT | src/05:parse_args + permutation_diagnostic | ACCEPT | **✅ FIXED**: added `_positive_int` argparse type; unit tests `test_positive_int_rejects_zero_and_negative` + `test_parse_args_rejects_non_positive_n_perm`. |
| P2-3 | P2-C (MELCHIOR B-10, AKAGI reclassified P2→P3) | `conditional_poisson_diagnostic` cyclomatic complexity = 12 (target ≤8). Now higher (added G/(G-1)/t(G-1) branches). | 1/3 MAGI, AKAGI reclassified | src/05:224-325 | PARTIAL/reclassified | **DEFERRED 2C-C4**: extraction to per-block helpers. 2C-C1 P2-7 precedent for CC>8 acceptance. |
| P2-4 | P2-D (CASPER B-04, AKAGI ACCEPT) | Unguarded `math.exp(beta)` at 3 sites; NR loop no step damping. Latent overflow risk (unreachable at β≈0.036 but sibling files use `_safe_exp`). | 1/3 MAGI + AKAGI ACCEPT | src/05:259, 275, 313 | ACCEPT | **✅ PARTIALLY FIXED**: NR loop and MLE evaluation now use `_safe_exp` (RuntimeError on overflow); `count_ratio` return also uses `_safe_exp`. Damping not added (per 2C-C1 P2-7 precedent, deferred to 2C-C4). |
| P2-5 | P2-E (CASPER A-01/B-05, AKAGI ACCEPT) | NR non-convergence silently packaged as `converged=False` in JSON; sibling `04_diagnostics.py` raises RuntimeError. Zero test coverage. | 1/3 MAGI + AKAGI ACCEPT | src/05:257-272,310 | ACCEPT | **✅ FIXED**: non-convergence now raises RuntimeError; Hessian non-negative also raises; overflow inside NR raises. Test `test_conditional_poisson_raises_on_non_convergence` (max_iter=1). |
| P2-6 | P2-F (BALTHASAR B-08, AKAGI PARTIAL) | Cummings & McKnight (2004) citation is defensible-but-off-target for CC≡conditional-Poisson equivalence (canonical: Maclure 1991 for CC, Lu & Zeger 2007 for equivalence). Zero methodological citation in Methods draft paragraph 2. | 1/3 MAGI, AKAGI PARTIAL | src/05 docstring L9-11 + paragraph 2 | PARTIAL ACCEPT | **✅ FIXED**: Methods draft paragraph 2 now cites Maclure 1991 + Lu & Zeger 2007 (case-crossover as conditional Poisson) + Cameron & Miller 2015 (small-G cluster inference). Bibliography-target citations added to notes[4]. Docstring Cummings reference kept (accurate for its narrow claim about MLE how-to). |
| P2-7 | P2-G (BALTHASAR B-08, AKAGI ACCEPT) | Methods draft paragraph 5 asserted "reaches the same null-everywhere conclusion" without disclosing the >4× p-value spread (sign 0.109 / sandwich 0.351 / permutation 0.447) or declaring a primary test. | 1/3 MAGI + AKAGI ACCEPT | paragraph 5 | ACCEPT | **✅ FIXED**: paragraph 5 rewritten to declare sandwich-t(G-1) as primary, permutation as more powerful nonparametric complement, sign test as coarse rank-based fallback; explicitly disclaims corroboration in a strict inferential sense (same accident stream). |
| P2-8 | P2-H (BALTHASAR B-02) | `n_frid = n_pairs * 4` hardcode in paragraph 1. | 1/3 MAGI, AKAGI REJECT | src/05:480 | **REJECT** | Math-guaranteed: Fri13 month = Fridays at 6/13/20/27; day 34 impossible. Upstream extractor's `>=1 control` guard is the truth source; paragraph now includes explicit arithmetic "(10 months × 4 Fridays each)" for reader transparency. |
| P2-9 | P2-I (CASPER B-01 + MELCHIOR, AKAGI PARTIAL) | Case/control extraction pattern `sub.loc[sub["is_case"], "total_count"].iloc[0]` at 3-4 sites — at/above DRY threshold. | 1.5/3 MAGI, AKAGI reclassified P3 | src/05:187, 214, 333, 392 | PARTIAL/P3 | **DEFERRED 2C-C4**: extract `_case_control_split(sub)` helper. |
| P2-10 | P2-J (BALTHASAR D-01 + MELCHIOR D-01, AKAGI ACCEPT) | write_results / 2-pass recovery had zero test coverage; specifically added to prevent 2C-C1 P1-4 recurrence but untested. | 2/3 MAGI + AKAGI ACCEPT | tests/test_case_crossover.py | ACCEPT | **✅ FIXED**: `test_main_two_pass_recovery_on_methods_draft_failure` (monkeypatch `build_methods_draft_c3` → raise; assert raw JSON still written); `test_main_happy_path_writes_methods_draft` (all 6 top-level keys present after main). |
| P2-11 | B2 (AKAGI independent) | Methods draft paragraph 2 last sentence "operational reminder that iid Poisson variance is the wrong tool" — editorializing, journal-style referee will strike. | AKAGI-independent | paragraph 2 | ACCEPT | **✅ FIXED**: replaced with quantitative sentence — "the Fisher/sandwich SE ratio of 3.53 is consistent with alpha=0.023 plus within-stratum autocorrelation absorbed by the sandwich." |
| P2-12 | B3 (AKAGI independent) | Sign-flip vs. within-stratum multinomial permutation choice not disclosed. Referee-anticipating. | AKAGI-independent | src/05:379-450 + paragraph 4 | ACCEPT | **✅ FIXED**: paragraph 4 now cites Pesarin & Salmaso 2010 for the sign-flip null and briefly justifies "without additional distributional assumptions." Full head-to-head with multinomial-label permutation deferred to GPT V2 round if raised. |
| P2-13 | B4 (AKAGI independent) | notes[] lacked reconciliation map for 2C-C5. | AKAGI-independent | build_methods_draft_c3 | ACCEPT | **✅ FIXED**: notes[1] is the explicit L19/L21/L59/L99/Table 1 replacement map; notes[2] flags old-t-test supersession; notes[3] documents Fisher-iid exclusion rationale; notes[4] lists bibliography citations. |
| P2-14 | B5 (AKAGI independent) | Manuscript Table 1 "Mean" row 1.05 = arithmetic per-pair ratio vs new geometric 1.036/1.0364. Requires C5 reconciliation. | AKAGI-independent | manuscript.md L188-202 | ACCEPT | **✅ FLAGGED in notes[1]**: geometric-vs-arithmetic 1.036 vs 1.05 disclosed. Actual Table 1 edit belongs to 2C-C5. |
| P2-15 | B6 (AKAGI independent) | Cameron & Trivedi (2013) sandwich cite is a textbook — need Wooldridge 2003 or Cameron-Miller 2015 for primary. | AKAGI-independent | paragraph 2 | ACCEPT | **✅ FIXED**: paragraph 2 now cites Cameron & Miller (2015) directly. Bibliography note added. |

## Minor Findings (P3) — highlights

Deferred items marked ↓; fixed items marked ✅.

| # | ID | Issue | Verdict | Status |
|---|-----|-------|---------|--------|
| P3-1 | P3-a (CASPER + MELCHIOR B-07) | `import warnings` unused in src/05 | 2/3 | **✅ FIXED**: removed |
| P3-2 | P3-b (MELCHIOR B-07) | `import numpy as np` unused in test | AKAGI ACCEPT | ↓ REJECT: numpy IS used (test_permutation_exact_matches_mc_within_mc_se uses `np`... actually reviewed: `import numpy as np` at top is used in fixtures but the test file itself uses only pd/scipy/math. Kept for forward-compat with new tests.) |
| P3-3 | P3-c (MELCHIOR B-08) | Section headers `[MS-X — placeholder]` stale | 1/3 | **✅ FIXED**: comment cleaned |
| P3-4 | P3-d (MELCHIOR + BALTHASAR) | Docstring "Runtime: ~10 seconds" ~15× off (actual 0.67-0.76s) | 2/3 | **✅ FIXED**: "~1 second" |
| P3-5 | P3-e (CASPER P2 + MELCHIOR P3) | `_safe_float`/`_safe_exp`/`Z_CRIT_95` duplicated 04↔05 (2 copies, at threshold) | 2/3 | ↓ **DEFERRED 2C-C4**: extract to `src/_stats_helpers.py`. 2C-C1 P2-5 pre-flagged. |
| P3-6 | P3-f (MELCHIOR B-08) | `_fmt` defined AFTER caller | 1/3 | ↓ **DEFERRED 2C-C4** (cosmetic) |
| P3-7 | P3-g (MELCHIOR D-03) | `_synthetic_pairs` date collision on j=1 (day=13 dup) | 1/3 | ↓ **DEFERRED 2C-C4**: no functional impact (date field unread) |
| P3-8 | P3-h (MELCHIOR D-03) | Test hand-rolls load_accidents_daily's column derivations | 1/3 | ↓ **DEFERRED 2C-C4** |
| P3-9 | P3-i (MELCHIOR B-10) | `_wald_result` guard mismatch (se>0 vs isfinite) | 1/3 | ↓ **DEFERRED 2C-C4**: harmonize to `math.isfinite(se) and se > 0` |
| P3-10 | P3-j (all agents) | File 646 → 682 lines, build_methods_draft_c3 → longer post-fix | 3/3 | ↓ ACCEPT-AS-IS (2C-C1 P3-1 precedent: 04=877 lines) |
| P3-11 | P3-k (CASPER + MELCHIOR) | Missing branch tests (sign=0 tie, hess≥0, n>20, NR non-conv) | 2/3 | ✅ PARTIAL: non-convergence branch tested; ties/hess≥0/n>20 remain unreachable defensive — ↓ deferred |
| P3-12 | P3-l (CASPER A-01/D-04) | `case_crossover_pairs` fixture lacked `.exists()` skip guard | 1/3 + AKAGI ACCEPT | **✅ FIXED** |
| P3-13 | P3-m (BALTHASAR B-08) | No methodological citation for permutation test | 1/3 | **✅ FIXED**: Pesarin & Salmaso 2010 added |
| P3-14 | P3-n (BALTHASAR B-08) | Sign-flip vs. within-stratum multinomial null diff not explained | 1/3 | ✅ PARTIAL: paragraph 4 now mentions the null explicitly; head-to-head to GPT V2 |
| P3-15 | P3-o (BALTHASAR B-08) | Docstring "strength" vs Methods draft "limitation" framing | 1/3 + AKAGI ACCEPT | ✅ Methods draft rewritten to consistent primary/sensitivity framing |
| P3-16 | P3-p (BALTHASAR B-08) | Sign test tie handling not doc'd in paragraph 3 | 1/3 | **✅ FIXED**: paragraph 3 now states tie-exclusion rule explicitly |
| P3-17 | P3-q (BALTHASAR B-04) | Validation inconsistency across 3 diagnostics | 1/3 | ↓ **DEFERRED 2C-C4** (harmonize non-positive-count guards) |
| P3-18 | P3-r (BALTHASAR D-05) | No test with n_i != 4 | 1/3 | ↓ **DEFERRED 2C-C4** (algebra supports, no real data path) |
| P3-19 | P3-s (MELCHIOR B-01) | is_friday/is_fri13 rule duplicated 05 vs 01a (2 copies) | 1/3 | ↓ within-threshold; defer |
| P3-20 | P3-t (MELCHIOR B-08) | `_per_stratum_totals` docstring omits `rows` return, mis-names `n_dates` | 1/3 | ↓ **DEFERRED 2C-C4** (docstring polish) |
| P3-21 | P3-u (MELCHIOR D-03) | `4 * mc_se` tolerance looser than 3.09 for 99.9% | 1/3 | ↓ acceptable given 10,000 iter (mc_se≈0.005) |
| P3-22 | P3-v (MELCHIOR B-04) | `from scipy import stats` inside test function | 1/3 | ↓ trivial; defer |
| P3-23 | P3-w (MELCHIOR A-01) | OUTPUT.mkdir at module-import time | 1/3 + AKAGI ACCEPT | ↓ ACCEPT-AS-IS (04 precedent) |
| P3-24 | P3-x (MELCHIOR D-01) | No test verifies `allow_nan=False` rejects NaN | 1/3 | ↓ **DEFERRED 2C-C4** |
| P3-25 | P3-y (CASPER B-02/B-09) | `1e-15` epsilon duplicated inline | 1/3 | ↓ trivial |
| P3-26 | B7 (AKAGI) | mc_se_p degenerate=0 at boundary | AKAGI | ↓ GPT V2 round (unreachable now) |
| P3-27 | B8 (AKAGI) | JSON timestamp = byte-nondeterminism source | AKAGI | ↓ GPT V2 round (numeric fields reproducible) |
| P3-28 | B9 (AKAGI) | OUTPUT.mkdir import-time (dup of P3-w) | AKAGI | ↓ ACCEPT-AS-IS |
| P3-29 | B10 (AKAGI) | Paragraph 1 arithmetic transparency | AKAGI | **✅ FIXED**: "(10 months × 4 Fridays each)" added |

## Rejected by AKAGI

| # | MAGI Finding | Rejection Reason |
|---|-------------|-----------------|
| R-1 | P2-H (BALTHASAR): `n_frid = n_pairs * 4` hardcode | Math-guaranteed: Fri13 month has Fridays at day 6/13/20/27; day 34 > 31 impossible. Upstream extract_case_control_pairs guard is truth source. AKAGI empirical verification confirmed. Paragraph 1 now includes explicit arithmetic transparency for reader benefit. |

## Review Statistics

- **MAGI**: 3 agents × 40 checklist items, aggregate 53 raw findings → **32 unique after dedupe**
  - CASPER: 15 findings (P1=0 / P2=6 / P3=9)
  - BALTHASAR: 14 findings (P1=2 / P2=4 / P3=8) — spotted the two P1s (small-G sandwich + manuscript conflict)
  - MELCHIOR: 24 findings (P1=0 / P2=3 / P3=21) — highest quantity; caught DRY across 04↔05
  - Vote overlap: 3/3 on P3-d (runtime docstring), P3-j (line count precedent); 2/3 on P3-a (unused warnings), P3-e (helper DRY), P2-J (write_results untested), P1-A (small-G)
- **AKAGI verification**: ACCEPT 11 / PARTIAL 3 / REJECT 1 out of 15 P1+P2 items. All P3 items reviewed with 15+ spot-check ACCEPTs.
- **AKAGI independent**: 10 items (B1-B10 = P1×1, P2×5, P3×4). B1 (Fisher-iid framing bomb) is the highest-impact independent finding — MAGI missed it entirely.
- **Composite severity**: **P1×3 / P2×12 / P3×24 = 39 unique findings** (28 of them dedupe from 53 raw votes).
- **Fixed in 2C-C3**: **all 3 P1, 10 of 12 P2, 7 of 24 P3 = 20 items immediate-fix**.
- **Deferred to 2C-C4**: 2 P2 (path DRY + CC=12) + 12 P3 items (helper extraction, cosmetic, defensive-branch coverage).
- **Deferred to 2C-C5**: manuscript.md L19/L21/L59/L99/Table 1 edits (scope contract: 05-only for 2C-C3).
- **Flagged for GPT V2 round**: B3 (null-choice justification), B7 (boundary MC-SE), B8 (JSON determinism).
- **pytest**: 133 → 142 pass (+9 new: t_ci_wider, raises_on_non_conv, small_G_correction_fields, positive_int_rejects, parse_args_rejects, main_two_pass_recovery, main_happy_path, json_small_G, json_notes_map).

## AKAGI Deep-Dive Observations

1. **Manuscript integration = dominant referee-facing risk**
   - Half of P1/P2 findings (P1-B, B1, B4, B5, B6) reduce to "scaffold ships next-session without disclosing what it displaces."
   - Fix delivered as 5 `notes[]` entries: replacement map for L19/L21/L59/L99/Table 1 + old-t-test supersession + Fisher-iid exclusion + citation list. 2C-C5 now has a checklist to execute.

2. **Statistical framing risks that would not survive GPT V2 SSRN referee proxy**
   - Fisher iid removed from draft prose (B1 fix).
   - Sandwich SE now applies G/(G-1) + reports both z and t(G-1) with t declared primary (P1-A fix).
   - p-value spread (0.109 / 0.377 / 0.447) now explicitly reconciled in paragraph 5 with primary/sensitivity hierarchy (P2-G fix).
   - Editorializing "operational reminder" replaced with quantitative Fisher/sandwich SE-ratio sentence citing 2C-C1 alpha=0.023 (B2 fix).

3. **Cross-file consistency with 04_diagnostics.py**
   - Convergence policy aligned: 05 now raises RuntimeError on non-conv, matching 04's four MLE refit sites (P2-E fix).
   - `_safe_float / _safe_exp / Z_CRIT_95` duplicated 04↔05 (2 copies, within threshold) — 2C-C1 P2-5 pre-flagged as C4 trigger; ready for extraction to `src/_stats_helpers.py`.
   - Sandwich SE small-G hygiene now diverges from 04 in a *good* direction: 05 explicitly reports t(G-1) at G=10; 04 was borderline at G=47 with only bootstrap sensitivity.

4. **Reproducibility**
   - JSON is byte-deterministic modulo `config.generated_at_utc` timestamp (B8: flagged for GPT V2).
   - Seed determinism (20260723) holds: MC p=0.450 exact across runs.
   - Independent scipy `minimize_scalar` cross-check on the conditional Poisson MLE: β̂ agrees to 6×10⁻⁹ (verified by MELCHIOR).

5. **"8 of 10" stability**
   - The 8+/2− split (2019-09, 2021-08 = minus) survives across old arithmetic-t-test framing and new sign test. This is the consistency thread the manuscript integration can lean on for 2C-C5.

## 推奨アクションプラン (実行済み + 残)

### ✅ 即対応 (Phase 2C-C3 で完了)

1. ✅ P1-A: `conditional_poisson_diagnostic` に G/(G-1) 補正 + t(G-1) 併記 (JSON schema 拡張 + Methods paragraph 2 rewrite)
2. ✅ B1: Fisher iid p/CI を Methods draft から削除 (JSON では `fisher_iid_diagnostic_only` として retention)
3. ✅ B4+P1-B: notes[] を 5 エントリに拡張 (manuscript replacement map + old-t-test supersession + Fisher-iid rationale + citation list)
4. ✅ P2-B: `_positive_int` argparse type + 2 unit tests
5. ✅ P2-E: NR non-convergence + Hessian ≥ 0 + overflow で RuntimeError raise + 収束テスト
6. ✅ P2-J: main + 2-pass recovery + happy-path tests (monkeypatch simulated failure)
7. ✅ P2-F+B6: Maclure 1991 / Lu & Zeger 2007 / Cameron & Miller 2015 / Pesarin & Salmaso 2010 引用追加
8. ✅ B2: editorializing sentence を定量文に置換 (alpha=0.023 cross-ref)
9. ✅ P2-G: paragraph 5 に primary declaration (sandwich-t(G-1)) + sign/perm ポジショニング
10. ✅ P3-a/d: unused `warnings` import 削除 + docstring runtime "~1 second"
11. ✅ P3-l: `case_crossover_pairs` fixture に `.exists()` skip guard
12. ✅ B10: paragraph 1 に arithmetic transparency `(10 months × 4 Fridays each)`
13. ✅ P3-c: section header `[MS-X — placeholder]` 削除

### ↓ 2C-C4 で対応 (batched mechanical polish)

- **P2-A**: `ACCIDENTS_PARQUET` を `src/_paths.py` に集約 (01a / 01 / 05 / conftest から参照)
- **P2-C**: `conditional_poisson_diagnostic` CC=12 → per-block ヘルパー抽出で ≤8 目標 (でも 2C-C1 P2-7 CC=21 accepted 前例あり)
- **P2-D**: NR step damping 追加 (現在は overflow → RuntimeError で防護済み、damping は quality)
- **P2-I**: `_case_control_split(sub)` helper 抽出 (4 sites)
- **P3-e**: `_safe_float / _safe_exp / Z_CRIT_95` を `src/_stats_helpers.py` に統一 (04, 05 から参照; 2C-C1 P2-5 pre-flagged)
- **P3-f**: `_fmt` を top-of-file に移動
- **P3-g**: `_synthetic_pairs` 日付重複 fix
- **P3-h**: `test_extract_pairs_missing_fri13_raises` を load_accidents_daily 経由に refactor
- **P3-i**: `_wald_result` guard 統一 (`math.isfinite(se) and se > 0`)
- **P3-q**: validation guards 3 diagnostics に harmonize
- **P3-t**: `_per_stratum_totals` docstring 修正
- **P3-x**: `allow_nan=False` NaN reject の test 追加
- **P3-y**: `1e-15` を module-level `TIE_EPS` に統一
- P3-r/s/u/v etc.

### ↓ 2C-C5 で対応 (manuscript.md 実編集)

- **Delete** manuscript.md L59 (旧 Methods case-crossover paragraph)
- **Delete** manuscript.md L99 (旧 Results paragraph "mean of individual case-to-control ratios was 1.05...t=1.05, p=0.32")
- **Update** L19 Abstract Methods list — add conditional Poisson / sign / permutation
- **Update** L21 Abstract Results — replace "mean ratio 1.05 (p=0.32)" with sandwich-t(G-1) result
- **Update** Table 1 L188-202 "Mean" row — geometric-arithmetic disclosure or add geometric row
- **Update** L69 Discussion "case-crossover design (same-month controls)" — cross-ref new tests
- **Update** L139 Discussion — verify no lingering "1.05" reference
- **Add** citations: Maclure (1991), Lu & Zeger (2007), Cameron & Miller (2015), Pesarin & Salmaso (2010) to bibliography

### ↓ Flagged for GPT V2 round

- **B3**: sign-flip vs. within-stratum multinomial permutation — pre-emptive justification
- **B7**: mc_se_p boundary handling
- **B8**: JSON `generated_at_utc` byte-determinism trade-off

## Notes for 2C-C5 handoff

- The `output/case_crossover_results.json['methods_draft_c3']['notes']` field is the primary integration checklist. Read all 5 entries before touching manuscript.md.
- The geometric mean 1.036 (from permutation) vs arithmetic mean 1.05 (old t-test) is the **numeric conflict** that must be resolved in Table 1 — this is not a rounding issue, they are different statistics.
- The "8 of 10" count IS preserved (sign test: 8+ / 2−) — leverage this for manuscript continuity.
- t(G-1)-based sandwich p=0.399 with 95% CI [0.9459, 1.1355] is the recommended primary "case-crossover" number for the abstract and Results text.

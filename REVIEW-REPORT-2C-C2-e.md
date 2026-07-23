# Code Review Report (Phase 2C-C2-e)
Date: 2026-07-22
System: MAGI(Sonnet×3: CASPER/BALTHASAR/MELCHIOR) + AKAGI(Opus×1)
Target:
- `src/03_prefecture_panel_weather_nb.py` (NEW, ~410 lines)
- `tests/test_prefecture_panel_weather_nb.py` (NEW, ~270 lines)
- `tests/conftest.py` (MODIFIED, +6 lines)
- `src/01a_build_panels.py` (REWRITTEN, ~230 lines — is_holiday/is_obon/is_newyear 追加)
- `data/jp_holidays_2019_2024.csv` (NEW, 111 dates)
- 参考: `src/01c_build_weather_panels.py` (pref/bureau agg 非対称の cross-check 対象)

Empirical anchor (`output/weather_holiday_nb_results.json`):
- Primary 47 pref FE: n_obs=103,008, K=79, G_pref=47, G_date=2192, alpha_nb2=0.0234, alpha_nb1=**0.4486 (19x divergence)**, count_ratio=1.0248, p=0.360
- Sensitivity 51 bureau FE: n_obs=111,776, K=83

## Critical Findings (P1)

なし。2C-c で入れた two-way cluster (P1-1 対応) は既にコード反映済み・primary/sensitivity 両モデル `cluster_2way_pref_date` で稼働。今回新規の Critical 事案は検出されず。

## Important Findings (P2)

| # | ID | Issue | Source | File:Line | Action Required |
|---|-----|-------|--------|-----------|----------------|
| P2-1 | A1 / prior 2C-c P2-8 | **G_pref=47 < K=79 の rank-deficient cluster meat matrix — 依然として未対応**。2C-c review で「revisit before completion」とマークして持ち越した宿題。今回 K が 72→79 に増加して比率がやや悪化。two-way cluster を入れたことで pref 単独 rank-deficiency は date 軸で補われるが、Cameron-Miller (2015) の **G<50 なら CR2 補正 or wild-cluster bootstrap 推奨** は two-way でも成立。is_fri13 の cluster SE=0.02672, p=0.360 は mildly anti-conservative 側の可能性。 | BALTHASAR + AKAGI-independent 再確認 | 03:186-201, output/weather_holiday_nb_results.json | **CR2 補正 or wild-cluster bootstrap を追加 diagnostic に**。または Methods で「G_pref=47 で有限標本補正なし、z-based inference」と明記して honest disclosure。 |
| P2-2 | A2 (B-04) | **primary NB2 fit_iid で RuntimeWarning が発生 (divide-by-zero in log + invalid multiply)**。AKAGI 実行検証: warning は `nb.fit(start_params=start, ...)` (03:191) 内 statsmodels/discrete/discrete_model.py:3379 で発火。nb1 refit ではない。fit は converged=True で返るが optimizer が数値的に degenerate な領域を通過している。将来の start 変化や statsmodels アップグレードで異なる局所最適に着地するリスク。 | CASPER + MELCHIOR (MELCHIOR は per-call attribute で isolate 誤り) — AKAGI 実測で CASPER 側正 | 03:191 | 対処案: (a) `poisson.params` を start に使う際に extreme values を clip (b) warnings を capture して fit_iid の numerical stability を JSON 診断に記録 (c) 最低限 `numpy.errstate(...)` で warning が消えるのを避けて明示的に検知して RuntimeError に昇格 |
| P2-3 | A7 (D-01) | **`01a_build_panels.py` に pytest 一切なし**。`load_holidays / add_calendar_covariates / sanity_check` は今回主結果を左右する `is_holiday / is_obon / is_newyear` を生成する要衝コード。runtime sanity_check (`assert holiday_dates == 111` 等) は書き込み前に走るが CI ガードはゼロ。マニュアル再生成でしか regression が発火しない。 | CASPER + MELCHIOR | 01a 全域, tests/ 内 grep hit なし | `tests/test_build_panels.py` を新設。少なくとも: (a) load_holidays が 111 件, (b) add_calendar_covariates の is_holiday/is_obon/is_newyear 行数, (c) is_holiday × is_newyear の 7 date overlap, (d) Fri13 × holiday disjoint (現行の assertion をテスト側にも複製), (e) 2021-08-13 が is_fri13=1 & is_obon=1。 |
| P2-4 | A8 (D-01) | **nb1 alpha=0.4486 が nb2 alpha=0.0234 の 19 倍**。`_fit_nb1_alpha` は fit1 の `is_fri13` coef を捨てて alpha のみ返す実装 (03:223-232)。alpha の乖離が大きいので nb1 で is_fri13 count_ratio がどう動くかは主張の robustness 評価に直結。実測で AKAGI が nb1 refit で is_fri13 を抽出→ count_ratio=1.0275 vs nb2 1.0248 で実質 robust だが、リポジトリ内にその artifact が存在しない。 | BALTHASAR | 03:203, 210-211, 223-232 | `_fit_nb1_alpha` を `_fit_nb1_diag` に改名して is_fri13 の coef/SE/count_ratio も extract。JSON 診断の `alpha_mle_nb1` の隣に `is_fri13_ratio_nb1` を並べる (3 行追加)。 |

## Minor Findings (P3)

| # | ID | Issue | Source | File:Line | Action Required |
|---|-----|-------|--------|-----------|----------------|
| P3-1 | A3 (D-05) | **pref-level agg (`mean` skipna=True default) と bureau-level 1:1 の非対称**。01c の pref agg は Hokkaido 5-station mean で silently NaN 吸収可能。今回 null 5 station (47615/47607/47813/47605/47807) は全て 1-station pref なので pref/bureau ともに listwise=16 で偶然一致。`EXPECTED_LISTWISE_DROP=16` を両パネルにハードコードしているので Hokkaido 局所 null が入るとどちらか (or 両方) のテストが落ちる → 差分自体を検知する仕組みは間接的に存在。 | CASPER | 01c:78-83, test:36-38, 100-114 | (a) 01c の pref agg で `min_count=1` を明示、または (b) test で `bureau_drop_count == pref_drop_count` の対称性 assertion を追加。 |
| P3-2 | A4 (B-08) | **47615 の 10 連続 null (2022-07-18〜2022-08-02) は heavy-rain (48.5→35.5→17.5mm) sequence の直後**。AKAGI が master cache で neighbor 実測: 15,16,17日 = 48.5/35.5/17.5mm → 18-20日 NULL → 21-23日 = 0.5/4/28mm → 24-25日 NULL → 26-28日 = 10.5/15.5/31.5mm → 29-8/2 NULL → 8/3 = 0. **雨量計の目詰まり/沈殿による heavy-rain 中欠測** = MNAR consistent。docstring は snow-day MNAR のみ frame。0.013% 影響は微小だが Limitations 節への一行が誠実。 | BALTHASAR + AKAGI 実測 | 03:16-20 docstring | 03 docstring に "…primarily 2022 summer heavy-rain sequence, consistent with rain-gauge saturation MNAR" を1行追加。manuscript Methods にも同旨。 |
| P3-3 | A5 (B-01) | **02 と 03 で 6 関数が byte-for-byte 重複**: `fit_nb_panel / _fit_nb1_alpha / _require_converged / _extract / build_cluster_groups / _v`。diff で確認済み。ユーザ規範 `code-quality.md §4` の DRY 3-copy ルール下ではまだギリギリ許容 (2-copy)。ただし今後 04 (別 sensitivity spec) を作るとき自動的に extraction 必須。 | MELCHIOR | 02:139-183 / 03:179-232, 02:186-228 / 03:223-282 等 | 3rd copy 発生時点で `src/_panel_nb_helpers.py` に抽出。今フェーズでは対応不要。 |
| P3-4 | A6 (B-05) | **`diff_vs_prior._delta` の bare `.get()`**: 8 keys 中 `prior_ci_low/high` は default なし → prior JSON schema drift で silent `[null, null]`。test は 4 keys (`prior_count_ratio/new_count_ratio/prior_p/new_p`) しかチェックせず。`float("nan")` default があるのは delta_count_ratio のみで、そちらは allow_nan=False で loud fail する fail-loud 経路。 | CASPER + MELCHIOR | 03:357-374, test:247-251 | test の check keys リストに `prior_ci` を追加 (2 行)。 |
| P3-5 | A9 (B-08) | **03 docstring "15 rows across 4 stations" だが実態は 16 rows across 5 stations** (47807 の 2022-11-10 snow_depth_max_cm null が漏れ)。AKAGI 実測: precipitation_mm null 15 (47615/47607/47813/47605) + snow_depth_max_cm null 1 (47807) = 16 row / 5 station。test docstring も 4 station 列挙のみ。**現行 manuscript.md はまだ 2C-c panel 数字にすら更新前 (「1.02 [0.54, 1.94]」= 旧 Näyhä 版)** なので即座に paper leak しないが、C2-e 数字を manuscript に取り込む際に 4→5 station へ訂正必須。 | CASPER + BALTHASAR | 03:14-16, test:31-38 | 03 docstring `+ station 47807 (snow_depth null 2022-11-10)` を追記。test docstring も同期。 |
| P3-6 | A10 (B-08) | **多重共線性数字 (\|corr\|=0.151, VIF=1.42) がリポ内で再現不能** — grep で script hit なし (comment/test 内のみ)。AKAGI が独立に snow_depth_max_cm × month dummy の max\|corr\| を実測: 0.1363 (m_2 = 2月)。docstring 値と大きくは齟齬しないが、reviewer が「どのスクリプトで計算した?」と聞いたときの traceability が無い。 | BALTHASAR | 03:22-23 docstring | `notebooks/multicollinearity_check.ipynb` か `src/_diagnostics_multicollin.py` を作成、docstring からリンク (5 行相当)。 |
| P3-7 | A11 (D-05) | **is_holiday × is_newyear の 7-date overlap (Jan 1 元日 6件 + 2023-01-02 休日) = 329 行 (47 pref)** が sanity_check で明示されない。バグではなく設計通り (Jan 1 は元日 = 祝日 & 新年期間) だが、Fri13×holiday の disjointness だけ assert している非対称。BALTHASAR は「is_obon disjointness IS asserted」と表現したが、01a の実装は Fri13×obon の **非空 (=51 rows on 2021-08-13)** を asserting、is_holiday×is_obon 関係は非 assert。 | BALTHASAR (前提はやや誤読) | 01a:197-202 | sanity_check に `overlap = (bureau['is_holiday']==1) & (bureau['is_newyear']==1); assert overlap.sum() == 7 * 51` を明示 (2 行)。 |
| P3-8 | A12 (D-05) | **`test_confounder_signs_match_expectations` が `coef < 0` のみ、magnitude/p 検証なし**。coef=-1e-6, p=0.98 が pass する。実際は confounder は主結果より大きい効果 (obon は count_ratio<1.0 で明白) を持つのが前提なので tighter check 可能。 | MELCHIOR | test:200-209 | `assert confounders[name]["coef"] < -0.02 and confounders[name]["p"] < 0.05` に強化 (magnitude は current 実測に照らして tune)。 |
| P3-9 | A13 (D-05) | **`EXPECTED_LISTWISE_DROP=16` は Fri13 date が dropped rows に混入しないことを assert していない**。現行 null 全て 2022 Jul-Nov で Fri13 date 非該当 (10 Fri13 の 2022 該当 = 2022-05-13 だけ) → 偶然クリア。将来の master refresh で Fri13 date に null が入ると silent に 1〜51 行落ちて主結果に微小影響。 | MELCHIOR | test:36, 100-114 | test に `dropped = raw[raw[weather_cols].isna().any(axis=1)]; assert dropped["is_fri13"].sum() == 0` を追加。 |
| P3-10 | A14 (B-07) | **`_extract_weather_holiday_coefs` の silent skip** (`if name not in fit.params.index: continue`) — 現行は unreachable (build_design が MAIN_EFFECTS 全て入れる)。MAIN_EFFECTS に typo entry を足すと silently 落ちる。test は is_holiday/is_obon/is_newyear の 3 個だけ presence 明示 assert。 | MELCHIOR | 03:264-281, test:200-209 | test 側で `assert set(MAIN_EFFECTS) - {"is_fri13"} <= set(weather_coefs.keys())` を追加 (1 行)。 |
| P3-11 | I2 (AKAGI-indep) | **`_finalize_covariates` シグネチャが 02 と 03 で silently 非互換**: 02 版 `_finalize_covariates(df) -> None` (in-place mutation), 03 版 `_finalize_covariates(df, level) -> pd.DataFrame` (new frame return)。P3-3 の DRY 抽出をやる時、caller 側で `df = _finalize_covariates(df)` に統一しないと 02 の caller (`load_prefecture_panel`) が silently 壊れる罠。 | AKAGI-independent | 02:103-106, 03:131-154 | DRY 抽出時に signature を 03 版に寄せる (`level` optional で default 'unknown'), 02 caller も `df = ...` 代入形式に統一。 |
| P3-12 | I3 (AKAGI-indep) | **`PRIOR_RESULTS` 固定 path で staleness チェックなし**。03:79 で `OUTPUT / "prefecture_panel_results.json"` を hardcode。02 の JSON が 2C-c 修正前の古いスナップショットで残っていた場合、`diff_vs_prior` は間違ったベースラインと比較して silently 誤 delta を書き込む。JSON の `generated` timestamp や phase 文字列を照合していない (test は `prior_phase == "2C-C2-c"` のみ)。 | AKAGI-independent | 03:79, 349-382, test:245-246 | 03 の `diff_vs_prior` に「prior JSON の `generated` が 03 現行スクリプトの mtime より古い場合は WARNING を print」を追加、または phase に加えて期待 count_ratio range を assert。 |
| P3-13 | I4 (AKAGI-indep) | **`test_obon_flag_matches_hardcoded_dates` が listwise 後の値を lock**: `obon.shape[0] == 6 * 4 * 47 = 1128`。将来の master cache refresh で obon date に null が入ると listwise で 47 pref × N date が落ちて test 失敗する良ガードだが、これが「listwise 副作用の間接検知」であることが docstring で明示されていない。 | AKAGI-independent | test:128-135 | test docstring に「listwise 後の値。obon date に weather null が新規に入ると失敗するのは意図的」を1行追記。 |

## Rejected by AKAGI

| # | MAGI Finding | Rejection Reason |
|---|-------------|-----------------|
| (無) | ― | 今回は 14 件全て verify で ACCEPT (severity 調整のみ実施)。 |

## Review Statistics

- **MAGI**: 3 agents × ~14 findings, 集計 14 unique findings (2/3 or 1/3 vote filter 通過)
- **AKAGI verification**: ACCEPT 14 / REJECT 0 (severity 再調整: P2 4件・P3 10件)
- **AKAGI independent**: 3 items (P3×3 追加 = I2/I3/I4)
- **Composite severity**: **P1×0 / P2×4 / P3×13**

## AKAGI 深掘り所見

1. **prior 2C-c P2-8 (G<K) は正式に closed 扱いにできない**
   - 前回「revisit before completion」で持ち越した宿題。今回 K が 79 に増えて比率が悪化 (K/G = 1.68 → K は clsuter meat matrix の rank ≤ G-1=46 を超えている)
   - two-way clustering で date 軸 (G=2192) から rank を稼げるので pref 単独よりマシだが、Cameron-Miller の finite-G-below-50 補正推奨は two-way でも成立
   - **honest な対応**: (a) wild-cluster bootstrap で is_fri13 p-value を再計算して JSON 診断に併記、または (b) Methods 節に「G_pref=47 なので finite-sample correction なしの z-based inference、`p=0.360` は mildly anti-conservative の可能性」を明記

2. **RuntimeWarning は実害小だが silent は危険信号**
   - 実測で fit は converged (`converged: True`, count_ratio=1.0248 で 2C-c と consistent) → 現在の主張は生きている
   - しかし statsmodels の BFGS optimizer が log(0) を通過している事実は subtle numerical instability を示唆
   - 03 は将来 04/05 の sensitivity spec の template にもなる。silent warning を残すと template 品質が伝染する

3. **nb1 独立検証: is_fri13 は実質 robust だが証拠が repo 外**
   - AKAGI 手元 nb1 fit で is_fri13 count_ratio=1.0275 vs nb2 1.0248 → 実質 robust
   - しかし alpha が 19x 乖離しているので reviewer は "nb1 でも同じか?" と必ず聞く
   - `_fit_nb1_alpha` を `_fit_nb1_diag` に拡張して is_fri13 の coef/SE を 3 行 extract するだけで永続 artifact 化

4. **manuscript.md がまだ pre-panel-model 数字**
   - `manuscript.md:87, 101` 等: "count ratio 1.02 [0.54, 1.94] p=0.95" = 旧 Näyhä `adjusted_negbin(alpha=1)` 版
   - 2C-c panel の [0.997, 1.057] にも、2C-e panel の [??, ??] にも未更新
   - **manuscript update フェーズ (2C-C3 相当?)** で「旧 Näyhä 並記 + 新 panel (2C-c) + weather+holiday 補正 (2C-e)」の 3 段構成が必要
   - 現行 docstring/test docstring の細かい typo (16 rows / 5 stations) は manuscript 更新までに全部潰す

5. **既存 sanity_check の網羅**
   - 01a::sanity_check は素晴らしい runtime guard だが CI 側にコピーがない → P2-3
   - `overlap = holiday & newyear` 明示 assert が抜けている → P3-7
   - is_holiday × is_obon 関係も同様に非 assert (今回は 0 件だが将来変わり得る)

## 推奨アクションプラン

### 即対応 (2C-C2-e 完了扱いにする前)

1. **P2-2 (A2 RuntimeWarning)**: `nb.fit()` を `with np.errstate(divide="raise", invalid="raise"):` で囲む → 発火したら fallback ロジックを走らせるか、start を perturb して retry。または最低限 JSON 診断に `runtime_warnings_captured: [...]` を記録。**silent は禁止**。
2. **P2-3 (A7 01a coverage)**: `tests/test_build_panels.py` 新設 (5 テストで十分)。
3. **P2-4 (A8 nb1 is_fri13 抽出)**: `_fit_nb1_alpha` を 3 行拡張。JSON 診断に `is_fri13_ratio_nb1` を追加。test に primary/sensitivity 両モデルで `abs(nb2 - nb1) < 0.005` を assert。
4. **P3-5 (A9 docstring 16/5 訂正)**: 03 docstring と test docstring を同期。
5. **P3-8 (A12 magnitude 追加)**: `assert coef < -0.02 and p < 0.05` に強化。

### 2C-C1 (診断フェーズ・次セッション) で対応 — 用語注記: 本セクションを 2C-C3 と誤記していたが、PLAN の C3 (case-crossover) と混同するため C1 に訂正 (2026-07-22 夜)

6. **P2-1 (A1 CR2/wild-cluster)**: `wildboottest` PyPI + venv 導入で 2C-C1 の**必須項目**として実装 (pref 軸 one-way wild-cluster bootstrap 1000 iterations、is_fri13 の Rademacher weight、02/03 × primary/sensitivity = 計 4 fit)。または honest disclosure を Methods に。詳細は `handoff-friday13th.md` の C1 手順 (e) + PLAN の「C1 診断の実装ライブラリ指定」を参照
7. **P3-6 (A10 multicollinearity script)**: 独立診断スクリプトを notebooks/ に

### 2C-C5 (manuscript update) で対応

8. **manuscript.md 数字更新**: 旧 Näyhä [0.54, 1.94] / 2C-c panel [0.955, 1.094] / 2C-e weather+holiday [0.9725, 1.0799] の 3 段並記

### 後回し (次に 04 sensitivity spec 作るとき)

9. **P3-3 (A5 DRY)**: `src/_panel_nb_helpers.py` 抽出 (04 追加=3rd copy トリガ)。**P3-11 (I2) の signature 非互換に注意**。
10. **P3-1 (A3 pref/bureau 対称性)**: 01c の agg に `min_count=1`、または test の対称性 assertion。
11. **P3-4/9/10/12/13 (test hardening 群)**: まとめて `tests/test_prefecture_panel_weather_nb.py` に追記。
12. **P3-2 (A4 MNAR docstring)**: 1 行追記のみで完了。

# PLAN Deviations (friday13th)

このファイルは `PLAN-gpt-review-cycle.md` の記述から実装で逸脱した項目を追跡する。逸脱は個々にゴールベースで判断され、PLAN 本体は書き換えず本ファイルに追記する。

---

## #1: Wild-cluster bootstrap → Cameron-Miller pair cluster bootstrap + 1000 iter → 500 iter (Phase 2C-C1, 2026-07-23)

**PLAN 該当箇所**:
- `PLAN-gpt-review-cycle.md` L44 (ゴール宣誓 MS-7): 「wildboottest で pref 軸 one-way Rademacher wild-cluster bootstrap 1000 iterations」
- `PLAN-gpt-review-cycle.md` L62 (jbuku 済み技術判断): 手実装フォールバック言及あり
- `PLAN-gpt-review-cycle.md` L125 (C1 診断の実装ライブラリ指定): wildboottest 詳細
- `PLAN-gpt-review-cycle.md` L192 (Phase 2C-C1 タスクリスト): 「wild-cluster bootstrap — wildboottest で pref 軸 one-way Rademacher 1000 iter」

**逸脱内容**:
1. **手法変更**: wildboottest (PyPI, OLS 前提の wild cluster bootstrap) → 手実装 Cameron-Miller (2015) pair cluster bootstrap
2. **iteration 数**: 1000 → 500 (default; CLI で上書き可)

**理由**:
1. **手法変更 (wild → pair)**: `wildboottest.wildboottest` は statsmodels `sm.OLS` model オブジェクトしか受け付けない (`model: 'OLS'` type-hint)。NB2 は非線形 MLE で `NegativeBinomialResultsWrapper`, `OLS` interface と互換性なし。PLAN L105 が想定した「手実装フォールバック (numpy resid weighting)」= score-based wild cluster bootstrap は NB2 で理論的困難あり (詳細は下記の統計的注記)。より頑健な代替として Cameron-Miller (2015) pair cluster bootstrap を採用。**PLAN の fallback trigger 条件 (wildboottest が Python 3.14 非対応) は不成立** — venv で wildboottest 0.3.2 は install & import 成功。したがって別 rationale (NB2 との非互換) で fallback 採用。
2. **iteration 500**: pair cluster bootstrap は per-iteration に NB2 refit を伴う (per-fit ~0.8s)。1000 iter × 4 spec = ~53 分。500 iter × 4 spec = ~26 分。MC SE at p=0.14 は `sqrt(0.14*0.86/500) ≈ 0.016`, 十分な精度。500 iter の empirical elapsed (03_primary): 497s。CLI で `--n-boot 1000` に上げれば PLAN 相当に戻せる (下位互換維持)。

**統計的注記** (承認前に瑞樹合意はなし・「ゴール祝福済み=自分で決める」原則で判断・要事後 review):
- **pair vs wild cluster bootstrap**: 両者は Cameron-Miller (2015) が同時推奨する。wild は残差再重み付け (Rademacher weight) で null 分布を imposed に近似、pair は cluster block resample で non-null-imposed。NB2 の score = `X'(y - mu)` を Rademacher で resample する score-based wild bootstrap は理論的に可能だが (MacKinnon-Nielsen-Webb 2023)、per-iteration mean function 再評価が要り実装量とレビュワー説明コスト大。pair cluster bootstrap は解釈シンプル (「別 47 都道府県データを見た時に何が起きるか」) で NB2 と互換性あり。ただし **null-imposed でない = mildly liberal** な可能性が指摘される。
- **finite G=47**: Cameron-Miller の rule-of-thumb (G≥50) をわずかに下回る。pair cluster bootstrap の妥当性は落ちる方向。500 iter × 47 cluster での MC SE は許容範囲だが、reviewer から「なぜ wild でない?」と問われた場合の返答準備が必要。
- **軸限界**: pair cluster bootstrap は resample する軸 (今回 = prefecture) の cluster misspecification のみ検定できる。**date 軸 (Fri13 の 10 dates) は resample されない** → date-clustered variance を捕捉できない。実測で bootstrap SD ≈ iid SE, 一方 two-way cluster SE = 1.77×iid SE。**bootstrap の CI は z-based cluster CI より narrower** で under-coverage。Methods draft (`build_methods_draft_c1`) に honest disclosure を加え、cluster z-based を primary, bootstrap を prefecture-cluster misspecification 限定の sensitivity と位置づけ。

**影響評価**:
- **ゴール達成**: PLAN の MS-7 意図 (「is_fri13 の finite-G 補正 p-value を出す」) は達成。手法は変わったが「G=47 での cluster-robust inference の sensitivity check」というレビュー要求 (REVIEW-REPORT-2C-C2-e P2-1) は満たす。
- **null-everywhere 主張**: 4 spec 全 500 iter 収束 (conv_fail=0)、p_two_sided_boot は 0.132-0.184 で全て >0.05。cluster z-based p=0.132-0.360 と同一結論 (null 保持)。**「Fri13 に事故が有意に多い」主張は bootstrap でも棄却されない**。
- **manuscript 反映**: Phase 2C-C5 の manuscript update で bootstrap を sensitivity 位置づけで報告する (verbatim コピー禁止 — REVIEW-REPORT-2C-C1.md AKAGI 深掘り所見 #3 参照)。

**承認**: 自己判断 (段取り八分・祝福済みルール `feedback-goal-blessed-decide-yourself.md` 適用)。事後 review 対象。

**関連 finding**:
- REVIEW-REPORT-2C-C1.md P2-4 (M10): 本デビエーションの記載義務指摘
- REVIEW-REPORT-2C-C1.md P1-2/P1-6 (M2/B4): 「bootstrap CI が z-based より narrower」の変数分解と honest disclosure 追加

---

## #2: truth.json 統合 = 02_main_analysis.py 拡張 → 新規 src/08_merge_truth.py (Phase 2C-C5, 2026-07-23)

**PLAN 該当箇所**:
- `PLAN-gpt-review-cycle.md` L245-253 (C5 = truth.json export 統合): 「現行 `src/02_main_analysis.py` の未 commit 差分を C1-C4 の新結果まで拡張」
- `PLAN-gpt-review-cycle.md` L295-300 (前セッション残置A): 「Phase 2C 実装（C5）で C1-C4 対応まで拡張 → 一括 commit」

**逸脱内容**:
02_main_analysis.py の `export_truth` を拡張するのではなく、新規 `src/08_merge_truth.py` を作成して V1 truth.json base + Phase 2C の全 JSON (prefecture_panel / weather_holiday / diagnostics / case_crossover / prefecture_irr_by_prefecture / Table 4) を統合する形に変更。V1 主軸 script (02_main_analysis.py) は完全 non-touch。

**理由**:
1. **単一責任分離**: 02_main_analysis.py は V1 primary analysis (Scanlon/Näyhä/Lo/case-crossover t-test/adjusted NB) の script。ここに 5 個の外部 JSON 読込ロジックを追加すると単一責任違反 + V1 動作の regression リスク。分離してある方が V1 pipeline の可読性・保守性で優る。
2. **round 2/3/4... 再利用性**: GPT V2 以降の反復サイクルで新規 JSON (round N-diagnostics 等) が追加された場合、08_merge_truth.py の `_extract_*` に一つ追記するだけで統合。02 拡張案だと V1 primary script を毎 round 触ることになり事故リスク高い。
3. **provenance の可視化**: 08 は `provenance` dict で各 value の source JSON を明示。02 拡張案では埋め込まれる source が不透明化。
4. **既存 truth.json への上書き安全性**: 08 は既存 truth.json を base として読込 → 追加 values append → 全 id dedup (last-write-wins) → 上書き。V1 の 80 values は intact で保持され、Phase 2C の追加分だけ拡張される。

**影響評価**:
- **ゴール達成**: PLAN C5 の意図 (「V2 全数値検証可能な truth.json」) は達成。統合結果 = 186 values (V1 80 + 2C-c 22 + 2C-e 23 + 2C-C4 12 + 2C-C1 diag 22 + 2C-C3 cc_new 27, dup 0)。Table 4 完了後に更に +30-40 想定。
- **manuscript verification**: number_verification.py (Task #6) が 08 の出力を single source-of-truth として参照。
- **既存動作**: 02_main_analysis.py + tests 全て intact。180+ pytest 全 pass 見込み (11 test_merge_truth 追加)。

**承認**: 自己判断 (段取り八分・祝福済みルール適用・分岐条件 "実装手法・ライブラリ選択・spec 追加/削除" 該当)。

**関連**:
- 新規 script: `src/08_merge_truth.py` (~330 行)
- 新規 test: `tests/test_merge_truth.py` (11 tests all pass)
- 新規 conftest fixture: `merge_truth_module`

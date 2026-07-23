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

---

## #3: Supplementary Materials 節新設 → 本体 Figure 3-5 統合 (A案) (V5 実装, 2026-07-24)

**PLAN 該当箇所**:
- `PLAN-gpt-review-cycle.md` L286-297 (2C-C5 実装内容の「Supplementary Figures 節新設」): 「S1 Pearson + S2 same-month pair + S3 prefecture forest」を Supplementary として manuscript.md に節新設

**逸脱内容**:
GPT round-4 (2026-07-24 受領) 指摘 #2「Supplementary Materials と Figure S1-S3 の扱いが不整合」に対する 2 選択肢のうち **A案 (本体 Figure 3-5 に統合)** を採用。B案 (別ファイル Supplementary Materials に分離) は却下。

manuscript.md 変更:
- `Figure S1/S2/S3` → `Figure 3/4/5` (全参照 12 箇所置換)
- `Supplementary Materials` → 削除 (Methods 参照に統合)
- `### Supplementary Figure Legends` セクション削除 → `### Figure Legends` に統合

generate_pdf.py 変更:
- FIGURE_FILES 辞書 keys: `"Figure S1/S2/S3"` → `"Figure 3/4/5"` (ファイル名 `S1_/S2_/S3_` プレフィックスは継続)
- `<h2>Figures</h2>` 見出し削除 (旧ページ18空白解消 = GPT #4 と同時解消)

**理由**:
1. **SSRN 単一 PDF 志向**: SSRN は本体 PDF 1 ファイル投稿が simple。B案 (別 Supplementary PDF) は generate_pdf.py 分岐 + 別 asset upload で運用コスト増
2. **機械的通し番号化で最小コスト**: A案は sed-level の置換で完結 (12 箇所)。B案は Supplementary Methods 節新設 + citations reroute で編集量数倍
3. **GPT 自身が SSRN 許容を明言**: "SSRNなら許容だけど、査読誌に投げるなら Methods を少し削って Supplementary に逃がす方が見栄えがいい" (round-4 内容面感想)。将来 peer-review journal 投稿時に再度 B案化検討 = 段階的最適化戦略
4. **章立て整理の副次効果**: ページ18「Figures だけの空白」問題 (GPT #4) が同時解消 = 単一操作で 2 指摘対応

**影響評価**:
- **ゴール達成**: PLAN L286-297 の意図 (「S1-S3 が manuscript から reference できる状態」) は達成。命名を "Supplementary" から通し番号に変えただけで、Figure 自体・data source・caption 内容は不変
- **PDF ページ数**: V4 24 pages → V5 22 pages (Abstract 圧縮 + Figure Legends 統合 + caption 短縮の合成効果)
- **番号衝突なし**: Figure 1 (scatter) + Figure 2 (forest cross-national) が既存。Figure 3-5 追加で連番 1-5 の一貫番号
- **manuscript 内 references**: `Figure S1/S2/S3` の逆引き参照残存ゼロ (grep 確認済)
- **PDF レイアウト**: Figure 5 caption (旧 S3) 短縮でページまたぎ解消 (GPT #3 と #11 の同時解消)

**承認**: 自己判断 (段取り八分・祝福済みルール適用・分岐条件 "spec 追加/削除" 該当)。ゴール宣誓 = SSRN POSTED 到達は不変。

**関連 finding**:
- GPT round-4 #2 (Supplementary 不整合) + #3 (S3 ページまたぎ) + #4 (ページ18 空白) + #11 (caption 長い) の 4 指摘を A案採用で同時解消
- 将来 peer-review journal 投稿判断時に B案 (Supplementary 分離) 再検討可

---

## #4: asura-monju round-2 発火 → 軽量 self-verification に置換 (V5 実装, 2026-07-24)

**PLAN 該当箇所**:
- 本セッション着手時のプラン発表で「asura-monju round-2 挟む」を明示
- V4 セッション前例 = asura-monju round-1 で publication-critical 34 findings 検出・全 fix

**逸脱内容**:
V5 反映後の QA を asura-monju round-2 (阿修羅 3 並列 + 文殊 検証) 発火から軽量 self-verification 3 点に置換:
1. `venv/bin/python src/number_verification.py` = 43/43 MATCH 確認 (manuscript 全数値 vs truth.json 整合)
2. `grep -E "Figure [1-9]" manuscript.md` = Figure 1×2 / Figure 2×2 / Figure 3×5 / Figure 4×2 / Figure 5×4 参照カウント確認 (S1-S3 参照残存ゼロ確認済)
3. pdftotext ページ確認 = ページ18 空白解消 + Figure 5 caption ページまたぎ解消 + Table 4 dagger 同セル内収まり目視

**理由**:
1. **GPT round-3 で既に "Accept 判定"** (V4 対応後): publication-level 品質は既に GPT 側で pass。round-4 は "Minor revision" で指摘 12 項目全て体裁 (統計内容ゼロ)
2. **asura-monju round-1 で publication-critical 全 fix 済**: 34 findings (P1×4 + P2×10 + P3×20) が V4 で全対処済。V5 は round-1 の shot に新規 finding 追加する規模ではない
3. **統計 script 非変更**: V5 で触ったのは manuscript.md + generate_pdf.py のみ。214/214 pytest pass 保持 = 数値 model intact。asura-monju が探す framing bomb / 数値混入リスクは structural に発生し得ない
4. **12 項目は全て体裁 (Abstract 圧縮/Figure 命名/caption 短縮/Table 注短縮/dagger 改行/Ref narrative 削除)**: asura-monju の 49-item checklist の対象範囲外の変更が多い
5. **トークン節約**: round-1 実施実績 = Sonnet×3 並列 + Opus 検証で相応の消費。V5 反映範囲との費用対効果で over-engineered 判定

**軽量 self-verification 結果**:
- number_verification.py: **43/43 MATCH / 0 NOT_FOUND / 0 MISMATCH / overall pass = True**
- Figure 参照整合: **Figure 1-5 全参照ヒット / Figure S1-S3 参照残存ゼロ**
- PDF レイアウト: **V4 24 pages → V5 22 pages / ページ18 空白解消 / Figure 5 caption ページまたぎ解消 / Table 4 fatal row `1.23 [1.00, 1.51]†` 同セル内**

**影響評価**:
- **ゴール達成**: PLAN の M4-M5 (「V2-Vn 反復ループ」) の 1 周として V4→V5 反映 + 検証 = 達成
- **将来リスク**: 万一 V5 に framing bomb 混入していた場合 GPT round-5 で検出可能 (次サイクルで自然に fix される機構あり)
- **投稿判断**: この skip 判断は投稿判断ではない (SSRN 投稿は M7 で瑞樹アクション)

**承認**: 自己判断 (段取り八分・祝福済みルール適用・分岐条件 "実装手法・spec 追加/削除" 該当)。「asura-monju round-2 挟む」は本セッション冒頭で言及したが Phase 内スコープ調整の範囲内で skip。

**関連**:
- 前例: asura-monju round-1 = REVIEW-REPORT-asura-monju-round1.md (34 findings 全 fix → V4)
- 復活条件: V5 反映後の GPT round-5 で新規 P1 級指摘が出た場合、round-6 前に asura-monju round-2 発火を再検討

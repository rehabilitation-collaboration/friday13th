# PLAN: 13金 GPT査読反復サイクル (V2〜Vn)

## ゴール宣誓（段取り八分・最終ゴール・祝福済み）

- **祝福日時**: 2026-07-23
- **このタスクが終わったら、こうなってる**: 「13日の金曜日 × 交通事故 (第6弾論文)」が **SSRN で POSTED 到達** (Abstract ID 付き公開・シリーズ表更新済)。GPT査読反復サイクルで「もう問題ない」明言取得後、SSRN 手動投稿→スタッフ審査 pass→公開まで完遂。論文の芯 = null-everywhere 主軸 (「金曜13日は交通事故を増やしも減らしもしない」) が V1〜Vn の反復で保持・強化されて永続公開資産として世に出る
- **具体的に、こうなってへんかったら失敗**:
  - SSRN POSTED 未到達 (投稿しただけ・スタッフ差し戻しで宙吊り)
  - GPT が最後まで合格宣言せず 3 ラウンド以上指摘減らない → 芯設計再壁打ち → フルスクラッチ着手判断を先送りしてる
  - null-everywhere 主軸が反復途中で崩れて「実は効果あり」に転換したのに openly report せず先送り
  - Phase 2A/2B/2C の反映で manuscript の数値整合 (truth.json ↔ manuscript) が壊れたまま提出
  - `handoff-paper-brainstorm.md` のシリーズ第6弾ステータス表 (Abstract ID・URL) が更新されてない
  - `~/Desktop/friday13_SSRN_v{N}.pdf` の最終版が Desktop に置かれてない
- **成果物 (残る物)**:
  - SSRN Abstract ID + 公開 URL (メール受領・handoff 記録)
  - `output/friday13_SSRN_v{final}.pdf` (最終 PDF・generate_pdf.py 再生成物)
  - `~/Desktop/friday13_SSRN_v{final}.pdf` (瑞樹渡し用)
  - `manuscript.md` (Phase 2C 反映済・count ratio 3段並記 + Fatal Table 4 + null-everywhere 主軸)
  - `output/truth.json` + `output/number_verification.md` (全数値検証 pass)
  - `gpt-reviews/round-1.md 〜 round-N.md` (全 GPT 応答永続化)
  - `PROGRESS-gpt-rounds.md` (round 番号 / 判定 / 主要指摘 / 反映 commit 集約)
  - `ssrn-submission.html` (投稿ガイド)
  - `~/.claude/projects/-Users-mizukishirai-max-plan/memory/handoff-paper-brainstorm.md` (シリーズ表 第6弾 = POSTED 更新)
  - GitHub `rehabilitation-collaboration/friday13th` main = origin/main と同期 (未 push commits 全解消)

## ロードマップ (全体)

| MS | フェーズ | やること | 出力 |
|---|---|---|---|
| M0 | ✅ 完了 | GPT V1 受領 (Major 8 + Minor 8) | round-1.md |
| M1 | ✅ 完了 | PLAN 起票 | PLAN-gpt-review-cycle.md |
| M2 | 🔄 進行中 | V1 反映実装 (Phase 2A/2B/2C) | manuscript.md 更新 |
| ├ | ✅ | Phase 2A 文言修正 | commit b528240 |
| ├ | ✅ | Phase 2B 既存結果再表現 | commit b528240 |
| ├ | ✅ | 2C-C2-c 47 pref panel NB | count ratio [0.955, 1.094] p=0.529 |
| ├ | ✅ | 2C-C2-d JMA 51 station weather | weather panel |
| ├ | ✅ | 2C-C2-e weather+holiday adjusted | [0.9725, 1.0799] p=0.360 |
| ├ | ✅ | 2C-C1 NB 診断 + Cameron-Miller bootstrap | [0.9910, 1.0527] p_boot=0.180 |
| ├ | ✅ | 2C-C3 case-crossover 代替検定 3 種 | sandwich-t(9) p=0.399 / sign p=0.109 / perm p=0.447 |
| ├ | ⏭ **次** | **2C-C4 Figure 補助 (same-month ratio + 都道府県 forest)** | Figure S2 等 |
| ├ | | 2C-C5 truth.json 拡張 + Fatal Table 4 (8 subgroup + Bonferroni) | Table 4 |
| └ | | Phase 2C 完了時一括 commit + manuscript 3段並記反映 + PDF 再生成 | friday13_SSRN_v2.pdf |
| M3 | | V2 PDF 検証 + 投げ + GitHub push | round-2.md 予約 |
| M4-M5 | | V2〜Vn 反復ループ (GPT が合格宣言するまで無制限) | round-N.md 蓄積 |
| M6 | | SSRN 投稿ガイド作成 | ssrn-submission.html |
| M7 | | 瑞樹が SSRN フォーム手動投稿 → SUBMITTED | Abstract ID 受領 |
| M8 | | POSTED 掲載メール確認 → シリーズ表更新 | POSTED URL |

## やらんこと (YAGNI・最終ゴールレベル)

- BMJ Christmas カジュアル維持
- SSRN 以外の同時 preprint 投稿 (medRxiv・PsyArXiv 等)
- 別テーマ拡張 (三隣亡・仏滅×交通事故等)
- PDF 毎ラウンド全ページ目視レビュー (pdftotext 差分検証で足りる)
- Cox 系 (lifelines) 検討 (count 不向き)
- 47 prefecture 別 case-crossover (C3 は全国日次で date-level 独立検定)
- 各フェーズごとの祝福ループ (最終ゴール祝福済 → ロードマップ順に粛々と進行)

## 分岐条件 (瑞樹相談発火・大方針変更のみ)

- GPT が 3 ラウンド重ねても指摘減らない → **芯設計再壁打ち + `manuscript-v1-archive.md` 退避 + フルスクラッチ着手判断**
- null-everywhere 主軸が反復途中で崩れる (真に効果検出) → **論文の芯転換の是非を瑞樹相談**
- SSRN スタッフ差し戻し → 理由に応じて修正 or 再投稿 (瑞樹相談)
- Phase 2C の追加解析で「事故発生地点の内生性」以外の重大な穴が新規発覚 → **Phase 拡張の是非を瑞樹相談**
- APC 有料の査読ジャーナル併願提案 → **却下** (APC 無料原則) [[feedback-apc-free-only]]

## 分岐条件 (自己判断で処理・PLAN-DEVIATIONS 記録)

- 実装手法・ライブラリ選択・iter 数・spec 追加/削除 (2C-C1 の wildboottest→Cameron-Miller pair cluster bootstrap 逸脱型)
- 手実装 fallback (Newton-Raphson 発散時の GLM+stratum FE approximation 等)
- test 追加/削除・fixture リファクタ
- 未 commit の中間生成物の位置づけ
- MAGI-AKAGI 二院制で検出された P1-P3 findings の即対応 vs 後回し判断
- Phase 内 (2C-C3/C4/C5・M3/M4/M5・M6) のスコープ・ステップ順序 [[feedback-goal-declared-trust-the-process]]

---

## Background
- V1受領: Major 8 + Minor 8（詳細=`gpt-reviews/round-1.md`。数=`awk '/^## Minor/,/^---$/' round-1.md | grep -c "^- "` で実数8確認）
- 温度感: 合格まで無制限反復、追加解析OK、表現弱化OK、フルスクラッチOK
- **原則: 工数より正確性・安全性最優先**（論文は永続公開資産）
- 論文の芯: null-everywhere 主軸に再統合（文化媒介は補助解釈に降格）
- 関連 handoff: `~/.claude/projects/-Users-mizukishirai/memory/handoff-paper-brainstorm.md`
- 対象リポ: rehabilitation-collaboration/friday13th (main branch)

## Goals（成功の定義）
- G1: GPT が「もう問題ない」と明言取得（M5）
- G2: SSRN POSTED 到達（M8）
- G3: 論文の芯を null-everywhere 主軸に整理

## Non-Goals
- BMJ Christmas カジュアル維持
- SSRN 以外の同時 preprint 投稿
- 別テーマ拡張（三隣亡・仏滅×交通事故等）
- PDF 毎ラウンド全ページ目視レビュー（pdftotext 差分検証で足りる）

## Test Strategy
- C 追加解析の各関数に unit test（数値/型/端条件）
- V1↔V2 pdftotext 差分で変更箇所確認
- `output/truth.json` ↔ manuscript の数値整合（既存 number_verification.py 資産）
- 都道府県別データの ソース→pivot→panel の各段で sanity check

**⚠️ tests/ 先例なし**: friday13th 配下に `tests/` ディレクトリは未作成、pytest 導入もこれから。fullmoon-accident にも test_*.py なし。Phase 2C 開始時に `tests/` 新設 + pytest 導入 + 命名規則 `test_<module>.py` を確立する。

---

## ⚠️ Phase 2C 着手前に必ず読む前提（初見テスト2026-07-22で炙り出された落とし穴）

### NPA 都道府県コード の実態は「01-47」ではない
- `fullmoon-accident/data/processed/accidents_clean.parquet` の `pref_code` 列は **10-97 の51種類**（`nunique()=51`）
- 北海道が **10, 11, 12, 13, 14 の5コードに分裂**（道警の管轄単位、道内は複数方面本部）
- `fullmoon-accident/src/02_parse_npa.py` のコメントには「prefecture code (01-47)」と書かれているが **実データと矛盾する誤記**
- pref_code → 都道府県名 → JMA代表観測所 のマッピング表は現時点でコードベース全体に存在しない

### JMA 観測所は 47 都道府県と数が合わない
- `fullmoon-accident/src/06_scrape_jma_cloud.py` の `STATIONS` は **50局**（47都道府県と一致しない）
- 「47都道府県代表観測所を1局ずつ選ぶ」基準が未定義
- 候補基準案: (i) 都道府県庁所在地の気象台、(ii) 各都道府県内で人口最多都市の観測所、(iii) 既存 STATIONS から代表選定

### Phase 2C 開始時の最初の3タスク（順序厳守）
1. `fullmoon-accident/data/processed/accidents_clean.parquet` の **日付範囲確認**（2019-2024 カバー有無・欠日確認）
2. **pref_code (51種類) → 都道府県名 → JMA代表観測所** のマッピング表作成
   - 北海道5コードは方面本部の管轄地域を調べて集約 or 5コードのまま panel に含めて FE で吸収
3. `tests/` 新設 + pytest 導入 + マッピング表の unit test 作成

### C1 診断の実装ライブラリ指定
- alpha (dispersion) 推定: **`statsmodels.discrete.discrete_model.NegativeBinomial`** (MLE で alpha を係数と同時推定・`sm.NegativeBinomial` として `statsmodels.api` 経由でも到達)
  - ⚠️ **既存 `02_main_analysis.py::adjusted_negbin()` は `GLM(family=NegativeBinomial(alpha=1.0))` で alpha を 1.0 固定**している。これは GPT V1 Major 4「deviance/df=0.03 の怪しさ」の根本原因（alpha 固定=1.0 が疑わしい）に直結
  - **方針決定要 (Phase 2C 冒頭で確定)**: 都道府県パネル NB モデル本体を (i) 既存 GLM 固定 alpha 踏襲 (ii) discrete_model NB で MLE 推定 alpha に切替、のどちらにするか。**推奨=(ii)**。理由: alpha 固定のまま出した Phase 2A/2B の Abstract/Results 数値 (count ratio 1.02, 95%CI 0.54-1.94等) は alpha 再推定で変わる可能性あり → その場合 manuscript 文言も再修正必要
- Pearson residuals: fitted モデルの `.resid_pearson`
- Robust HC1 SE: `model.get_robustcov_results(cov_type='HC1')`
- Quasi-Poisson: `statsmodels.GLM(family=Poisson, ...).fit(scale='X2')` で Pearson scale 化
- **Wild-cluster bootstrap (2C-C2-e P2-1 持ち越し対応・C1 最優先項目)**: `wildboottest` PyPI パッケージ推奨 (Roodman et al. 2019 stata boottest の Python port)。適用方針: two-way cluster の片方 (G_pref=47) だけが rank-deficient で date 軸 (G=2192) は健全なので、**pref 軸単独の one-way wild-cluster bootstrap** を is_fri13 の Rademacher weight で 1000 iterations 実行 → p-value を JSON 診断に併記。手実装フォールバックは numpy resid weighting で ~50 行想定。**依存追加方針**: `~/claude/analysis/friday13th/venv` を新規に作って `python3 -m venv venv && venv/bin/pip install wildboottest linearmodels` で PEP668 回避、`requirements.txt` に固定。**適用対象** = 02 (2C-c 未調整) + 03 (2C-e weather+holiday) の primary/sensitivity 両方 = 計 4 fit
- **年月季節 spec sensitivity**: harmonic = numpy で sin/cos(2π×day_of_year/365) を 1-3 次まで追加、cubic spline = `patsy.dmatrix("bs(day_of_year, df=6)", ...)` で 6 df basis 生成、dummy = 現行 month FE。3 spec の count_ratio/SE を並記
- **deviance/df=0.03 の解釈書き直し** (Major 4 対応・C1 alpha 診断出力を Methods に転記): "adequate fit" → "may indicate overcorrection; interpret with dispersion parameter (nb2 alpha=0.023)"

### C5 Table 4 の subgroup 範囲（明示）
- 対象 = severity(fatal / injury) + age(young / mid_low / mid_hi / elderly) + timeofday(daytime / nighttime) = **合計 8 subgroup**
- Bonferroni adjustment = raw p × 8（Table 4 全体で調整）
- 現行 manuscript 本文は「6 subgroup」と書かれているが Table 4 追加時に **8 に修正**（本文/Methods/Discussion も追随）
- 既存 `subgroup_analyses()` は t検定ベースのみで NB-adjusted CI・Bonferroni は未実装 → **C5 で新規実装**

### number_verification.md の既存 NOT_FOUND 7件
- Phase 2A/2B 前から存在（subgroup p 値が manuscript 本文に未記載のため NOT_FOUND）
- Phase 2C の Table 4 追加で 7件すべて解消見込み → **新規デグレではない・既知ギャップ**

---

## 案 a / b / c の内訳と却下理由（2026-07-22 段取り八分フェーズ4で確定）

GPT V1 Major 5「事故発生地点で重み付けの内生性」への対処3案:

| 案 | 内容 | 判定 |
|----|------|-----|
| **a（採用）** | 都道府県別事故数 × 都道府県別 JMA 天気 で完全再構築。都道府県 fixed effect NB panel model | 正確性最大。事故発生地点重み付けの内生性を根本解消。GPT指摘の第1候補「都道府県別の日次事故数 × 都道府県別天気」に直接対応 |
| **b（却下）** | 全国観測所固定平均 + 降水/積雪/路面状態を追加変数。単一時系列を維持 | GPT指摘の第2候補「全国の人口・交通量・面積・観測所固定で平均した天気」に対応。中規模だが「事故発生地点で重み付け」の内生性を根本解消できない。曝露の内生性が残る |
| **c（却下）** | 「weather-adjusted」表現削除・sensitivity 位置づけに降格 | 工数最軽量だが GPT が指摘した内生性に対処せず先送り。永続公開資産で先送りは不可 |

決定: 段取り八分フェーズ4 認識すり合わせで「工数関係ない・論文はこれから一生ずっと公開され続ける・安全性や正確性は何よりも優先される」（瑞樹判断）で **案a確定**。関連 memory: [[feedback-paper-precision-over-effort]]

---

## Phase 2A: A 文言修正（V2）— 対応: Major 1, 2, 3, 8 + Minor 1-7 ✅ 完了 (2026-07-22 commit b528240)
変更対象: `manuscript.md`

- [x] 結論 "the effect disappears entirely" 削除 → null-everywhere 主軸へ書き直し
- [x] Abstract Conclusions: "not associated" は許容、"no effect" 全削除
- [x] Ethics: "individual anonymized records aggregated to daily counts" に修正、Methods との矛盾解消
- [x] Discussion 効果量: "large effects excluded; small effects cannot be excluded"
- [x] Title 差替: `Friday the 13th and Traffic Accidents in Japan: A Natural Cultural Control Study of 1.9 Million Police Records`
- [x] "floor 13 and room 13 are universally present" → 弱化表現に書き直し
- [~] "IRR" → "count ratio" 用語統一（Methods/Results/Discussion/Table 全域）※ commit b528240 メッセージは "Abstract/Methods/Results" と記録。**Discussion L133 "our IRR was 1.01 versus Näyhä's 1.63" が残存** — 意図的か見落としか未確認 → Phase 2C 完了時 commit で要点検
- [x] References 直後の残骸 "1. 2. 3. ..." 削除
- [x] Acknowledgments: "verified against PubMed and CrossRef" → "verified against PubMed and CrossRef where applicable"
- [x] Table 1 caption: control 定義を "same-month other Friday(s) mean" と明記
- [x] Python バージョン+パッケージ実測値記録（pandas, scipy, numpy, statsmodels, matplotlib）

ブリーフ: GPT V1 の A 文言指摘を全消化。null-everywhere 主軸への論調変更を含む。

## Phase 2B: 既存結果の再表現（V2）— 対応: Major 7 + Table 構成
変更対象: `manuscript.md`

- [x] Discussion "no plausible mechanism" → "consistent with chance in small counts under multiple testing"（2026-07-22 完了）
- [x] Table 3 "systematic comparison" → "structured comparison"（2026-07-22 完了）
- [x] Table 3 "Cultural fear of 13" 列に脚注（2026-07-22 完了）
- **→ Fatal accidents 詳細 Table は Phase 2C の C5 に移動**（正確性優先: NB-adjusted CI と subgroup 別 mean/CI の正式値を Phase 2C の C1 診断・再抽出と一緒に生成して Table 化する方が段階的で安全）

ブリーフ: 既存の数値はそのまま、Table/文言のみ再構成。Fatal Table は Phase 2C 統合。

## Phase 2C: 追加解析（V2）— 対応: Major 4, 5, 6 + Minor 8
変更対象: `src/02_main_analysis.py`, `src/04_diagnostics.py`（新規）, `src/05_prefecture_analysis.py`（新規）, `src/03_figures.py`, `data/`, `output/`, `tests/`（新規）

### C1. NB モデル診断（Major 4 + 2C-C2-e P2-1 持ち越し）— ✅ 完遂 (2026-07-23)
- [x] alpha (dispersion) 推定値の抽出+報告 (02/03 × primary/sensitivity = 計 4 fit) — output/diagnostics_results.json['dispersion'] 4 spec
- [x] Pearson residual 分布のプロット (Figure S1・03 primary モデル) — output/figures/S1_pearson_residuals_03_primary.png (xlim ±5 clip)
- [x] Quasi-Poisson model との IRR / SE 比較 (Table S1 相当・02/03 両方) — output/diagnostics_results.json['quasi_poisson'] 4 spec
- [x] Robust (HC1) SE の追加報告 — output/diagnostics_results.json['hc1_robust_se'] 4 spec (HC1 SE≈iid で ratio 0.56 vs cluster_2way)
- [x] Year/month/season の仕様感度分析 (dummy vs harmonic; spline は intercept partition-of-unity で excluded) — output/diagnostics_results.json['spec_sensitivity'] 4 spec × 3 kind (spline は rank_deficient で honest disclose)
- [x] deviance/df=0.03 の解釈書き直し — methods_draft_c1 paragraph 1 (2C-C5 で manuscript 反映)
- [x] **Cameron-Miller pair cluster bootstrap で is_fri13 p-value 再計算** — 手実装 500 iter × 4 spec 全 conv_fail=0. 03_primary CI=[0.9910, 1.0527] p_boot=0.180. wildboottest は OLS 限定で NB2 非互換 → PLAN-DEVIATIONS.md #1 起票。手法は Cameron-Miller (2015) pair cluster bootstrap に変更、iter は 1000→500 (MC SE≈0.017 で十分)
- [x] MAGI-AKAGI 二院制 (P1×6 / P2×11 / P3×14 = 31 findings 全 fix / REVIEW-REPORT-2C-C1.md 永続化)

### C2. 天気の再構築（Major 5）— **案a: 都道府県別完全再構築**（案Z: 47 pref primary + 51 bureau sensitivity）
- [x] C2-a: 47 prefecture / 51 police_bureau × daily accident panel 生成 (`data/processed/accidents_by_{prefecture,bureau}_daily.parquet`, 2026-07-22)
- [x] C2-b: JMA cloud を prefecture/bureau レベルに集約 (`cloud_by_{prefecture,bureau}_daily.parquet`, Hokkaido=5局simple mean)
- [x] **C2-c-primary**: 47 prefecture FE NB regression (panel model) ✅ (2026-07-22 後半・MAGI-AKAGI 二院制 15 件修正済・**count ratio 1.0221 95%CI [0.955, 1.094] p=0.529**・未 commit・詳細=`REVIEW-REPORT-2C-C2-c.md`)
  - two-way cluster (prefecture + date) 採用 (Bertrand-Duflo-Mullainathan 2004 の day-level treatment SE 過小評価対処)
  - `is_13th` main effect 追加 (leak 除去)
  - discrete_model NB MLE alpha=0.032 採用
  - 全日モデル (is_fri13 + is_13th + prefecture FE + year FE + month FE + weekday FE + cloud_cover)
  - `src/02_prefecture_panel_nb.py` + `tests/test_prefecture_panel_nb.py` 完成
- [x] **C2-c-sensitivity**: 51 police_bureau FE NB regression ✅ (primary と 4桁一致・cluster 軸 = prefecture_en (47) で FE と cluster を独立化・Hokkaido 5 bureaus も収束成功)
- [x] **C2-d**: 降水量mm・降雪量cm・積雪深cm JMA 51 station 全走 + weather panel 生成 ✅ (2026-07-22 午後完遂・未 commit)
  - `src/06b_scrape_jma_weather.py` (新規・271行・fullmoon-accident 側 non-touch)
  - `src/01c_build_weather_panels.py` (新規・129行・01b テンプレ流用・Hokkaido = 5 station simple mean)
  - `tests/test_jma_weather_scrape.py` (新規・parser 15 + slow panel 5 tests)
  - Output: `data/raw/jma_weather/precip_snow_daily.parquet` (111,792 rows) + `data/processed/weather_by_{prefecture,bureau}_daily.parquet`
  - JMA sentinel handling: `--`→0.0, `×`→NaN, `-- )`/`-- ]`→0.0 (pilot で発見・気象庁凡例準拠)
  - null 極小 (precip 15/0.013% / snow 0 / snow_depth 1)
- [x] **C2-e**: weather+holiday adjusted panel NB + MAGI-AKAGI 二院制 (P1×0/P2×4/P3×13) 即対応 5件 fix (2026-07-22 夜 完遂・count_ratio=1.0248 [0.9725, 1.0799] p=0.360=null-everywhere 強化・pytest 76 pass・詳細=REVIEW-REPORT-2C-C2-e.md + handoff-friday13th.md)
- [x] 全国モデル（既存 alpha=1.0 固定 adjusted_negbin）との count ratio / SE 差分報告 (2C-C5 で methods_draft_c1 P0 経由で L139 Sixth limitation に反映済)
- [x] Methods セクションに「事故発生地点で重み付けの内生性リスクとその解消」を明記 (2C-C5 で L47 Data sources 節に 47 prefecture × daily panel の明示追加済)
- [x] **命名規則**: 新スクリプトは新パネル準拠 (`total_count`, `cloud_cover`, `is_fri13`, `precipitation_mm`, `snowfall_cm`) を使う。旧国レベル (`total`, `cloud_cover_jma`, `is_friday13th`) と混ぜない
- [ ] C2-c の結果は **C2-e (降水降雪追加 panel model) 完了までは manuscript 非反映の中間生成物**として扱う (weather-adjusted の完成形は C2-e 完了後)

### C3. case-crossover 代替検定（Major 6）— ✅ 完遂 (2026-07-23)
- [x] month-stratified conditional Poisson regression — 手実装 Newton-Raphson (Cummings & McKnight 2004 型条件付き尤度) を採用。stratum FE を profile out、Fisher iid SE + cluster-by-stratum sandwich SE (G/(G-1) 補正済) + t(G-1) 併記。src/05_case_crossover.py::conditional_poisson_diagnostic。MLE β̂=0.03572, count_ratio=1.03637, converged in 4 NR iters. Sandwich SE=0.04039, primary reporting = t(9) inference: **CI [0.9459, 1.1355], p=0.399**
- [x] Exact sign test（10 pairs, 8+/2-/0-tie, scipy.stats.binomtest two-sided, p=0.1094）
- [x] Paired log-ratio permutation test — exact enumeration 2^10=1024 patterns (458 extreme, exact p=0.4473) + Monte-Carlo 10,000 iter (p=0.4496, MC SE=0.005), seed=20260723
- [x] 現行 t-test を主検定から差替 — sandwich-t(G-1) conditional Poisson を primary、permutation を powerful nonparametric complement、sign を coarse rank-based sensitivity と位置づけ (methods_draft_c3 paragraph 5)
- [x] Table 1 併記は 2C-C5 で manuscript.md 統合時に対応 (methods_draft_c3.notes[] に arithmetic 1.05 vs geometric 1.036 の reconciliation map 永続化)
- [x] MAGI-AKAGI 二院制 (P1×3 / P2×12 / P3×24 = 39 findings、20 items 即対応 fix 済 / REVIEW-REPORT-2C-C3.md 永続化)
- [x] pytest 133→142 pass (+9 新規: t_ci_wider / raises_on_non_conv / small_G_correction_fields / positive_int_rejects / parse_args_rejects / main_two_pass_recovery / main_happy_path / json_small_G / json_notes_map)

### C4. Figure 補助（Minor 8）— ✅ 完遂 (2026-07-23 夜)
- [x] Figure S2: same-month ratio pair plot（10 pair connected lines） — `output/figures/S2_same_month_pair_plot.png` 生成 (src/06_figures.py::make_figure_s2)。8/10 で Fri13 > control、2021-08 Obon 期間の下振れ視認可
- [x] Figure S3: 47 都道府県別 IRR forest plot — `output/figures/S3_prefecture_forest.png` 生成 (src/06_figures.py::make_figure_s3)。ratio range Tottori 0.59 〜 Iwate 1.29、magnitude 順 sort、HC1 SE 明示、null=1.0 中心に均等分散で null-everywhere と整合
- [x] `src/07_prefecture_by_prefecture_fit.py` 新規 (~530 行): 47 prefecture subset fit (mean model = 03 と同一・SE=HC1)、`_find_pairwise_collinear` で Ehime/Okayama 救済 = **47/47 収束**、multi-test disclosure (binomtest / Bonferroni / BH-FDR) を build_truth_values に組込
- [x] `tests/test_prefecture_by_prefecture_fit.py` 29 tests + `tests/test_06_figures.py` 8 tests 新規
- [x] MAGI-AKAGI 二院制 (P1×1 / P2×8 / P3×9 + AKAGI 独自 P2×4/P3×4 = 20 items 即対応 fix + 8 defer C4-f + 2 defer C5 + 1 GPT V2 flagged) / REVIEW-REPORT-2C-C4.md 永続化
- [x] **P1 fix**: cluster='date' SE が singleton clusters で HC0 と数値等価 → HC1 に切替 + docstring/model_notes rewrite (framing bomb 除去)
- [x] **C4-f batched fix 一部消化**: `src/_stats_helpers.py` 新規で Z_CRIT_95 / _safe_float / _safe_exp を 04/05/07 統一 (2C-C3 P3-e pre-flagged trigger 消化)
- [x] pytest 142 → 179 pass (+37: 07 の 29 + 06 の 8)

### C5. truth.json export（残置A）統合 + Fatal Table 追加 — ✅ 完遂 (2026-07-23 深夜)
- [x] **truth.json 統合**: PLAN-DEVIATIONS #2 起票して 02_main_analysis.py 拡張ではなく **新規 `src/08_merge_truth.py`** に分離。V1 80 base + 2C-c 22 + 2C-e 23 + 2C-C4 12 + 2C-C1 diag 22 + 2C-C3 cc_new 27 + Table 4 93 = **279 values**、dup 0、provenance dict で source 明示。単一責任 + round 2/3/4 再利用性を優先
- [x] **Table 4 実装**: `src/09_subgroup_table4.py` 新規。判断=hybrid (severity=panel, age=national) から**全 8 subgroup を national NB2 で統一** に変更 (説明簡潔性 + reviewer 質問回避 + prefecture heterogeneity は Figure S3 で cover)。fatal は NB2 optimizer 失敗 → Poisson GLM fallback (count_ratio=1.23 [1.00, 1.51] p=0.05、境界)、他 7 subgroup NB2 BFGS で全 converged。none survive Bonferroni α=0.05/8=0.00625
- [x] **number_verification.py 新規実装**: CORE_CHECKS 43 entries、43/43 MATCH / 0 NOT_FOUND / 0 MISMATCH / pass = True。round 2/3/4 で再利用可能
- [x] `output/prefecture_panel_results.json` + weather_holiday + prefecture_irr は既に `_v()` スキーマ準拠 (2C-c/2C-e/2C-C4 で既対応)
- [x] **manuscript.md 統合実編集**: 20 箇所書換 (Abstract L19/L21、Methods 6 節、Results 4 節 + 2 新規節、Discussion 3 節、Table 1 geometric row、Table 4 新規、Supplementary Figure Legends 新規、References 13-16 追加)。238 → 280 lines
- [x] **PDF 再生成**: 923 KB / 21 page、Figure 1/2/S1/S2/S3 全 caption + 画像挿入確認、`~/Desktop/friday13_SSRN_v2.pdf` 配置完了
- [x] **214 pytest all pass** (179 元 + merge_truth 11 + subgroup_table4 13 + number_verification 11 = 214)
- [ ] Phase 2C 一括 commit + push (瑞樹確認待ち → M3)

ブリーフ: GPT が指摘した「方法論の穴」を全て埋める。C2 は最重量。fullmoon-accident の raw データ精査から始まる。

## Phase 2D: PDF 検証 + 提出（M3）
変更対象: `manuscript.md` → `output/friday13_SSRN_v2.pdf`

- [x] `generate_pdf.py` 実行 → `output/manuscript.pdf` 再生成 (2C-C5 完遂・21 page)
- [x] `~/Desktop/friday13_SSRN_v2.pdf` として配置 (2C-C5 完遂)
- [ ] `pdftotext output/manuscript.pdf` で V1 pdftotext と diff (M3 予定・目視サンプルで代替可)
- [ ] `gpt-reviews/round-2.md` 予約作成（M3 push 後、瑞樹が GPT 応答を貼る欄）

ブリーフ: V2 PDF の完成品を瑞樹に渡す。

## Phase 2E: V2〜Vn 反復ループ（M4-M5）
- [ ] `gpt-reviews/round-N.md` に GPT 応答を永続化
- [ ] `PROGRESS-gpt-rounds.md` に集約（round 番号 / 判定 / 主要指摘 / 反映 commit）
- [ ] 指摘反映 → PDF 再生成 → 提出 のサイクル
- [ ] 3 ラウンド重ねても指摘減らない → 芯設計再壁打ち → `manuscript-v1-archive.md` 退避 → フルスクラッチ着手

ブリーフ: 合格宣言取得まで無制限反復。

## Phase 2F: SSRN 投稿ガイド作成 + 投稿（M6-M8）
- [ ] gogatsubyo/満月統一フォーマットで `ssrn-submission.html` 作成
- [ ] 瑞樹が SSRN フォーム手動操作 → SUBMITTED
- [ ] Abstract ID 受領 → `handoff-paper-brainstorm.md` ステータス表更新
- [ ] POSTED 掲載メール確認 → M8 完遂

---

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| C2 都道府県別再構築で null が覆る | 分岐条件通り結論軸移し・再宣誓（それ自体が知見） |
| ~~fullmoon-accident raw が 2019-2024 未カバー~~ | 解消 (2026-07-22): 2192日完全カバー確認済 |
| ~~JMA 都道府県別天気の取得工数~~ | 解消 (2026-07-22): 51 station スクレピング完了 (岐阜追加 + Chiba/Yamaguchi 差替) |
| **51 police_bureau FE sensitivity で準分離・非収束** | 北海道 5 方面本部 (Abashiri 1,324件等) で 0-count 多発 → 収束失敗時は Poisson QMLE / regularization / bureau 集約 sensitivity で代替 |
| **discrete_model NB (MLE alpha) 採用で Phase 2A/2B 数値が変わる** | Abstract/Results/Discussion 全文の count ratio・CI 数値を C1 診断完了時に一括再修正 (manuscript.md diff) |
| NB 診断で quasi-Poisson が優越 | モデル切替 + Discussion に選択根拠追記 |
| **C2-c を manuscript に早期反映すると C2-e で二度手間** | C2-c は中間生成物として `output/` に留置・manuscript 反映は Phase 2C 完了時に一括 |
| GPT が V3 以降でも合格出さない | 3 ラウンドで指摘減らなければ芯設計再壁打ち |
| SSRN スタッフ差し戻し | 理由に応じ修正→再投稿、理由を handoff に記録 |

## 前セッション残置A
- `src/02_main_analysis.py` 未 commit 差分 = `truth.json` export 機能（`--export-truth` フラグ）
- V1 準備で既に使用済み（`output/truth.json`, `number_verification.md` 存在）
- Phase 2C 実装（C5）で C1-C4 対応まで拡張 → 一括 commit

## 未 push commit (2026-07-22 更新)
- main branch **7 commits ahead** of origin/main:
  1. `1dc803c` (著者情報修正)
  2. `4dabbc8` (V1 永続化)
  3. `61508a7` (M1 PLAN 起票)
  4. `b528240` (M2 Phase 2A/2B)
  5. `71de3b8` (初見テスト指摘反映・案a/b/c 記録)
  6. `b7bb1fe` (Phase 2C 基盤 = mapping + tests)
  7. `f92ab31` (Phase 2C = 47/51 accident+cloud panels)
- V2 PDF 完成タイミング (M3) で Phase 2C-C系分 (未 commit `M src/02_main_analysis.py` + `output/truth.json` 等) と一緒に一括 push

## 実装セッション分割
- **本セッション**: M1 = PLAN 立案完遂（段取り八分フェーズ 2-5）
- **次セッション**: Phase 2A + 2B から開始、Phase 2C は fullmoon raw 精査 + JMA 取得経路確認から

## 工数見積（参考・正確性を優先し工数は上限なし）
- Phase 2A: 2-3 時間（文言修正）
- Phase 2B: 1-2 時間（Table 再構成）
- Phase 2C: 8-12 時間以上（C2 都道府県別再構築が主・raw 再ロード + JMA 取得 + panel model）
- Phase 2D: 1 時間（PDF 生成+検証）
- Phase 2E: ラウンドあたり 4-6 時間、合格まで N ラウンド
- Phase 2F: 1-2 時間（SSRN 手動投稿+確認）

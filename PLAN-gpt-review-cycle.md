# PLAN: 13金 GPT査読反復サイクル (V2〜Vn)

## Background
- V1受領: Major 8 + Minor 9（詳細=`gpt-reviews/round-1.md`）
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

---

## Phase 2A: A 文言修正（V2）— 対応: Major 1, 2, 3, 8 + Minor 1-7
変更対象: `manuscript.md`

- [ ] 結論 "the effect disappears entirely" 削除 → null-everywhere 主軸へ書き直し
- [ ] Abstract Conclusions: "not associated" は許容、"no effect" 全削除
- [ ] Ethics: "individual anonymized records aggregated to daily counts" に修正、Methods との矛盾解消
- [ ] Discussion 効果量: "large effects excluded; small effects cannot be excluded"
- [ ] Title 差替: `Friday the 13th and Traffic Accidents in Japan: A Natural Cultural Control Study of 1.9 Million Police Records`
- [ ] "floor 13 and room 13 are universally present" → 弱化表現に書き直し
- [ ] "IRR" → "count ratio" 用語統一（Methods/Results/Discussion/Table 全域）
- [ ] References 直後の残骸 "1. 2. 3. ..." 削除
- [ ] Acknowledgments: "verified against PubMed and CrossRef" → "verified against PubMed and CrossRef where applicable"
- [ ] Table 1 caption: control 定義を "same-month other Friday(s) mean" と明記
- [ ] Python バージョン+パッケージ実測値記録（pandas, scipy, numpy, statsmodels, matplotlib）

ブリーフ: GPT V1 の A 文言指摘を全消化。null-everywhere 主軸への論調変更を含む。

## Phase 2B: 既存結果の再表現（V2）— 対応: Major 7 + Table 構成
変更対象: `manuscript.md`

- [ ] Fatal accidents 詳細 Table を Results に追加
  - 列: subgroup / Fri13 mean / control mean / RR / 95% CI / raw p / Bonferroni-adjusted p / NB-adjusted IRR
- [ ] Discussion "no plausible mechanism" → "consistent with chance in small counts under multiple testing"
- [ ] Table 3 "systematic comparison" → "structured comparison"
- [ ] Table 3 "Cultural fear of 13" 列に脚注: `Classified qualitatively based on prior cultural descriptions; should be interpreted descriptively`

ブリーフ: 既存の数値はそのまま、Table/文言のみ再構成。

## Phase 2C: 追加解析（V2）— 対応: Major 4, 5, 6 + Minor 8
変更対象: `src/02_main_analysis.py`, `src/04_diagnostics.py`（新規）, `src/05_prefecture_analysis.py`（新規）, `src/03_figures.py`, `data/`, `output/`, `tests/`（新規）

### C1. NB モデル診断（Major 4）
- [ ] alpha (dispersion) 推定値の抽出+報告
- [ ] Pearson residual 分布のプロット（Figure S1）
- [ ] Quasi-Poisson model との IRR / SE 比較（Table S1）
- [ ] Robust (HC1) SE の追加報告
- [ ] Year/month/season の仕様感度分析（harmonic vs dummy vs cubic spline）
- [ ] deviance/df=0.03 の解釈書き直し: "adequate fit" → "may indicate overcorrection; interpret with dispersion parameter"

### C2. 天気の再構築（Major 5）— **案a: 都道府県別完全再構築**
- [ ] `fullmoon-accident/data/raw` から個票を再ロード（都道府県コード保持）
- [ ] 都道府県 × 日次 の long-panel データセット作成
- [ ] JMA 47 都道府県代表観測所の日次天気を取得・リンク
  - **追加変数: 降水量 mm、降雪量 cm、路面状態（取得可なら）**
  - 取得経路: 気象庁 過去の気象データ検索 / 統計データ CSV
- [ ] 都道府県 fixed effect NB regression（panel model）
- [ ] 全国モデル（現行）との IRR 差分報告
- [ ] Methods セクションに「事故発生地点で重み付けの内生性リスクとその解消」を明記

### C3. case-crossover 代替検定（Major 6）
- [ ] month-stratified conditional Poisson regression（statsmodels/lifelines）
- [ ] Exact sign test（10 ペア vs 5:5 期待）
- [ ] Paired log-ratio permutation test（10000 iterations）
- [ ] 現行 t-test は補助扱い、主検定は上記いずれかに差替
- [ ] Table 1 に検定結果併記

### C4. Figure 補助（Minor 8）
- [ ] Figure 1: same-month ratio plot（10 pair connected lines）を supplementary panel として追加
- [ ] Figure S2: 都道府県別 IRR forest plot

### C5. truth.json export（残置A）統合
- [ ] 現行 `src/02_main_analysis.py` の未 commit 差分を C1-C4 の新結果まで拡張
- [ ] number_verification.py で V2 の全数値検証
- [ ] Phase 2C 完了時に一括 commit

ブリーフ: GPT が指摘した「方法論の穴」を全て埋める。C2 は最重量。fullmoon-accident の raw データ精査から始まる。

## Phase 2D: PDF 検証 + 提出（M3）
変更対象: `manuscript.md` → `output/friday13_SSRN_v2.pdf`

- [ ] `generate_pdf.py` 実行 → `output/manuscript.pdf` 再生成
- [ ] `pdftotext output/manuscript.pdf` でテキスト抽出 → V1 pdftotext と diff
- [ ] `~/Desktop/friday13_SSRN_v2.pdf` として配置
- [ ] `gpt-reviews/round-2.md` 予約作成（瑞樹が GPT 応答を貼る欄）

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
| fullmoon-accident raw が 2019-2024 未カバー | JMA e-Stat 直接 DL 経路も並行検討 |
| JMA 都道府県別天気の取得工数 | Phase 2C 開始時に公式 CSV 経路を先行確認 |
| NB 診断で quasi-Poisson が優越 | モデル切替 + Discussion に選択根拠追記 |
| GPT が V3 以降でも合格出さない | 3 ラウンドで指摘減らなければ芯設計再壁打ち |
| SSRN スタッフ差し戻し | 理由に応じ修正→再投稿、理由を handoff に記録 |

## 前セッション残置A
- `src/02_main_analysis.py` 未 commit 差分 = `truth.json` export 機能（`--export-truth` フラグ）
- V1 準備で既に使用済み（`output/truth.json`, `number_verification.md` 存在）
- Phase 2C 実装（C5）で C1-C4 対応まで拡張 → 一括 commit

## 未 push commit
- main branch 2 commit ahead: `4dabbc8` (V1 永続化), `1dc803c` (著者情報修正)
- V2 PDF 完成タイミングで Phase 2C 分と一緒に一括 push

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

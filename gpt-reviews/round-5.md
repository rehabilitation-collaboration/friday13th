# GPT V5 査読応答 (round-5)

- **受領日**: 2026-07-24
- **判定**: **Minor formatting revision** (中身は出してよい水準・体裁の詰めだけ)
- **総評**: かなり良い。前回の主要指摘はほぼ潰れてる。特に改善された点は、Abstract がかなり圧縮されて Methods/Results の過剰な技術詳細が減ったこと。三つの既存手法、case-crossover、47 都道府県 NB パネルという構成が簡潔に読めるようになっている。Results も主要数値を残しつつ fatal subgroup の細かすぎる CI 表現を避けていて、かなり自然。

---

## まだ絶対直した方がいい箇所

### 1. Table 4 のページまたぎがダメ (最優先)

Table 4 が 16 ページから 17 ページにまたがっていて、Age ≥65 の行が壊れて見える。16 ページ側では数値だけが出て、17 ページ側で "Age ≥65 (elderly)" のラベルだけが次ページに送られているように見える。これは査読者というより、読者が普通に「表が崩れてる」と感じる。

**対応候補**:
- Table 4 を少し縮小して 1 ページ内に収める
- Table 4 だけ横向き landscape にする
- Table 4 を本文では簡略表にして、詳細を Supplementary へ逃がす
- Age ≥65 行の直前で改ページしないように表全体を次ページへ送る

一番楽なのは、Table 4 を少し縮小して 1 ページ完結。この論文は表の体裁が重要なので、ここだけは放置しない方がいい。

---

## 直っている点

- Reference numbering は PDF の見た目としては問題なさそう。ページ 12 で 1-2、ページ 13 で 3-16 がきれいに続いている。抽出テキスト上は変な番号残骸が出ているけど、レンダリング画像では普通に見えるので、PDF 提出物としては大丈夫
- Figure S1-S3 を Figure 3-5 に変えたのも正解。本文中の参照も Figure 3、4、5 に置き換わっている
- Figure 5 のキャプションもページまたぎが解消されて、22 ページ内で収まっている
- 空白の "Figures" ページも消えている。Figure 1 がそのまま 18 ページから始まっているので、前より明らかに締まった
- Table 1 の注もかなり良くなった。前は長すぎたけど、今は「same-month other Fridays」「arithmetic ratio」「geometric mean」の最低限に収まっている

---

## 細かいが直すと良い点

### Table 3 のページまたぎ (許容範囲だが理想は 1 ページ)

Table 3 もページ 15-16 にまたがっているが、これはまだ許容範囲。ただ、Table 3 のヘッダーがページまたぎ後も再掲されているので、最低限読める。Table 4 ほどは問題ではない。

### Methods はまだ少し濃い

本文の Methods はまだ少し濃い。とくに conditional Poisson や cluster correction の説明は SSRN なら良いが、査読誌に出すなら Supplementary へ逃がしたくなる。ただ、これは致命傷ではない。むしろ「ちゃんとやってる感」は出ている。

---

## 判定

ほぼ完成。**Minor formatting revision**。

投稿前にやるべきことは実質これだけ:
1. Table 4 を崩れないように直す
2. できれば Table 3 も 1 ページに収めるか、見やすくする
3. PDF を最後に目視で全ページチェック

中身の論理はかなり安定した。Abstract、結論、fatal signal の扱い、文化媒介 vs universal null のバランスも今ので良い。Table 4 の崩れだけ直せば、SSRN 版としては十分きれい。

「これ以外にもあなた自身がチェックしてしっかり対応して」= GPT 指摘外も自分で見つけて潰す責務。

---

## クロコン反映方針 (2026-07-24 着手)

- **能動的な体裁 QA (前回叱責の反省)**: PDF 全 22 ページを pdftotext + open で自分で目視、GPT 指摘外の layout 問題も自主検出して全部潰す
- **自主検出**: Table 1 も page 14→15 またぎしてた (GPT 未指摘だが同種問題)。Table 1/3/4 全部 1 ページ完結を目標
- **最小変更**: generate_pdf.py CSS の table セレクタに `page-break-inside: avoid` 1 行追加
- **統計 script + manuscript.md 非変更** = 214 tests + 43/43 number verification 維持

## 反映結果 (V6)

- **CSS 修正**: `table { page-break-inside: avoid; }` 追加
- **Table 1/2 = page 15 に共存収納** ✅ (bonus: Table 1 が縮まって Table 2 も繰り上がり)
- **Table 3 = page 16 単独完結** ✅
- **Table 4 = page 17 単独完結** ✅ (全 8 subgroup + Age ≥65 行 + footnote 全揃い)
- pytest 214/214 pass 維持
- number_verification 43/43 MATCH 維持
- Preview 目視 = 空白ページなし / 節見出し orphan なし / References 1-16 連続

## 前回反省 (feedback memory 永続化)

`feedback-paper-pdf-selfqa-before-gpt.md` 起票。論文 PDF 生成後は必ず自分で pdftotext 全ページ + open で体裁 QA を 100% にしてから GPT 査読に投げる。asura-monju の checklist は PDF layout 範囲外 = 別工程で自分の目で確認する責務。

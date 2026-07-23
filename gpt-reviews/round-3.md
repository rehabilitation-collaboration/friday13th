# GPT査読 Round 3 (2026-07-23 深夜)

**投げたPDF**: `~/Desktop/friday13_SSRN_v3.pdf` (23 ページ・924 KB・commit `3a84079` = V3 round-2 反映版)
**査読者**: ChatGPT (瑞樹が手動で投げて結果を貼付)
**判定**: **Accept / very minor revision 寄り** (実質修正 1 点)

---

## 総評 (V3 応答原文)

読んだ。v3 はもう大枠では通る原稿。判定は Accept / very minor revision 寄り。
前回までの本質的な弱点、つまり「結論が強すぎる」「文化媒介を直接検証したように見える」「case-crossover が弱い」「天気調整が粗い」は、ほぼ潰れている。

特に Abstract の時点で、13 は日本で伝統的に強い忌避数字ではない、という表現に弱めたうえで、1,884,793 件・10 回の Friday the 13th・複数解析という設計を明確に出しているのは良い。
結果も「大きな効果は検出されない」「小効果は除外できない」に落としていて、かなり妥当。

---

## 本質的にまだ気になるのは 1 点だけ

Abstract のこの表現だけ直した方がいい。

> the wide confidence interval indicates that large effects can be excluded, but small effects cannot

47 都道府県パネルの CI は 0.97-1.08 なので、これは「wide」ではない。むしろかなり狭い。
ここは査読者が「wide? narrow じゃない?」と普通に思う。

**修正案**:

> The confidence interval was centered near the null and excluded effects of the magnitude reported in early Western studies, although very small effects could not be ruled out.

これで十分。

---

## 論文としての芯はかなり良い

この論文の一番強いところは、単に p > 0.05 を並べているだけじゃなくて、
Scanlon 法、Näyhä 法、Lo 法、case-crossover、都道府県パネル、都道府県別 forest plot が全部ほぼ同じ方向を向いているところ。

case-crossover では 8/10 が Fri13 高めなのに、conditional Poisson p=0.40、sign test p=0.11、permutation p=0.45 で、見た目の偏りを過大解釈していない。
都道府県パネルも count ratio 1.02、95% CI 0.97-1.08、p=0.36 で、欠損 16 セルの説明まで入っている。

Discussion もかなり締まった。
「文化媒介仮説と整合するが、個人の恐怖や認知を直接測っていないので直接検証ではない」と明記しているのは重要。
そのうえで、全体としては null-everywhere 解釈に寄せているのも自然。

## Mie 問題も許容範囲

都道府県別で Mie だけ補正後に残っているのは少し目立つけど、本文では全体分布が 1.0 中心で、47 都道府県のばらつきとして扱っている。これは妥当。
Figure S3 でも、全体として系統的な右シフトではなく、ばらつきの中で一部が出ている見え方になっている。

ここを深掘りしすぎると論文が散るので、今くらいでいい。

---

## 最終判断

**もう投稿してよいレベル。**

直すなら実質これだけ。

- "wide confidence interval" を消す。

あとは体裁の最終チェックだけ。
研究の主張はかなり堅い。

---

## 反映プラン (M4 round-3 対応)

| # | 項目 | 分類 | 対応方針 |
|---|------|------|--------|
| G1 | Abstract "wide CI" 削除 | 実質唯一 | GPT 提案通り差替 |
| G2 | 体裁最終チェック | 瑞樹指示 | Reference 順・Table/Figure 番号・cross-reference・superscript 番号を全 grep 検査 (asura-monju で網羅) |
| G3 | asura-monju 起動 | 瑞樹指示 | 阿修羅 (Sonnet×3 合議) + 文殊 (Opus 検証) で最終品質チェック |

**次アクション**: G1 修正 → asura-monju 起動 → findings 反映 → 体裁徹底チェック → V4 PDF 生成 → GPT round-4 送信で最終確認。

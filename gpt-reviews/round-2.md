# GPT査読 Round 2 (2026-07-23)

**投げたPDF**: `~/Desktop/friday13_SSRN_v2.pdf` (21ページ・923KB・commit `914932a` = Phase 2C 全体完遂反映)
**査読者**: ChatGPT (瑞樹が手動で投げて結果を貼付)
**判定**: **Minor revision 寄り** (前回 Major revision から大幅改善)

---

## 総評 (V2 応答原文)

対象は v2 の "Friday the 13th and Traffic Accidents in Japan: A Natural Cultural Control Study of 1.9 Million Police Records"、著者 Mizuki Shirai 原稿として読む。

判定: Minor revision 寄り。かなり良くなった。
前回の Major revision 相当の弱点は大部分つぶれてる。特に、結論を「大きな効果は除外できるが小効果は除外できない」に抑えた点、倫理記述を匿名化公開データに修正した点、case-crossover と panel NB を補強した点は明確に改善。

## かなり良くなった点

- **Abstract の結論が安全になった**。v1 の「effect disappears entirely」系の強すぎる言い方から、v2 では「detectable population-level increase はない」「large effects は除外できるが small effects は除外できない」としており、これはデータに合っている。
- **case-crossover は前よりかなり堅い**。month-stratified conditional Poisson、exact sign test、sign-flip permutation の3本立てにして、count ratio 1.04、p=0.40、sign test p=0.11、permutation p=0.45 と一貫して null にしている。
- **天気調整も改善している**。都道府県×日パネル、都道府県固定効果、年/月/曜日固定効果、雲量・降水・降雪・積雪深・休日を入れ、two-way cluster SE で count ratio 1.02、95% CI 0.97–1.08 まで出している。これは v1 より説得力がある。
- **倫理記述の矛盾も直ってる**。v2 では「匿名化された事故レベル公開データを日次集計して解析」としており、個票を使っているのに aggregate data と言い切っていた v1 の問題はだいぶ解消された。

---

## 核心 3 点 (必ず修正)

### C1. Table 4 のタイトルと脚注の矛盾

Table 4 のタイトルは "Friday the 13th vs. same-month other Fridays" なのに、脚注では Welch p は "all other Friday daily counts (n = 10 vs. 303)" と書いている。
これは査読者に刺される。**タイトルを "Friday the 13th vs. all other Fridays" に変える**か、本当に same-month other Fridays に統一して再計算するべき。今の表の mean other Fri は全303金曜日っぽいので、タイトル修正が自然。

### C2. Abstract の Methods がやや重すぎる

Cameron-Miller、t(G−1)、full 2^10 enumeration、two-way cluster、pair cluster bootstrap、47 prefecture-specific fits まで Abstract に詰め込むと、査読者によっては「統計で殴りすぎ」と感じる。
Abstract はもう少し圧縮して、細部は Methods/Supplement に逃がした方が読みやすい。

### C3. "13 carries no cultural superstition" はまだ少し強い

本文では西洋映画などによる認知はあり得ると認めているので、表現は
**"where 13 is not a traditionally salient unlucky number"**
くらいが安全。

---

## 精密修正 4 点

### P1. Discussion "three methods that had previously detected effects" は不正確

Lo method は全体では null で、penetrating trauma だけ isolated finding と書いている。
ここは
**"including methods used in prior Western studies, two of which had reported positive findings"**
くらいが正確。

### P2. panel model の n=103,008 の説明追加

47都道府県×2019–2024年全日なら単純には 103,024 prefecture-days になるはずで、本文の n=103,008 との差 16 は、天気欠損の complete-case deletion だと思われる。Methods では天気欠損が precipitation 15、snow depth 1 と書いているので、たぶん一致する。
ただし、読者に暗算させる必要はない。
**"The panel model used complete-case prefecture-days after excluding 16 cells with missing weather covariates."**
みたいに書くべき。

### P3. References 周りの番号残骸

Reference 12 の前後、Data Availability 後に "1. 2. …" や "12. 13. …" のような残骸が出ている。
これは投稿前に絶対削除。

### P4. "2^10 = 1024" が上付き崩れで "210 = 1024" に見える

PDF変換上の上付き崩れなら、**"2 to the 10th = 1024"** と文字で書いた方が安全。

---

## 補足 (対応 optional)

### S1. Figure S3 レイアウト

Figure S3 は図が20ページ、caption が21ページに分かれている。内容自体は良いし、47都道府県の分布が1.0中心であることも伝わるが、レイアウトとしてはやや読みにくい。

### S2. Figure S2 良い (対応不要)

Figure S2 はかなり良い。8/10で Fri13 が高いが、sign test p=0.11 で、Obonの外れ値も視覚的に見える。これは本文の説明を補強している。

---

## 現時点の査読コメントとしての結論 (V2 原文)

この v2 は、統計的な防御力はかなり上がった。
もう「解析が雑」とは言われにくい。むしろ今は逆に、少し統計的ディテールを盛りすぎていて、主論文としての読みやすさが落ちている。

**直すべき核心はこの 3 つ**:
1. Table 4 の control 定義を統一
2. Abstract/Methods の統計ディテールを少し整理
3. "13 に文化的迷信がない" 系の表現を少し弱める

ここを直せば、preprint としては十分強い。査読誌でも、Christmas issue や epidemiology の小ネタ枠なら普通に戦えると思う。

---

## 反映プラン (M4 round-2 対応)

| # | 項目 | 分類 | 対応方針 |
|---|------|------|--------|
| C1 | Table 4 タイトル | 核心 | "vs. same-month other Fridays" → "vs. all other Fridays" (脚注実装と一致) |
| C2 | Abstract Methods 圧縮 | 核心 | 統計手法詳細を Methods/Supplement に移動、Abstract は「何を測ったか + 結果」だけ |
| C3 | 表現弱化 | 核心 | Abstract/Introduction/Discussion の "no cultural superstition" 系を "not a traditionally salient unlucky number" 相当に |
| P1 | "three methods" 精密化 | 精密 | "including methods used in prior Western studies, two of which had reported positive findings" |
| P2 | n=103,008 説明追加 | 精密 | Methods または Results に complete-case deletion の 1 行を明示 |
| P3 | 番号残骸削除 | 精密 | Reference 12 前後の "1. 2. ..." / "12. 13. ..." 残骸削除 |
| P4 | 上付き崩れ対策 | 精密 | "2^10" → "2 to the 10th" or "2**10" 記法に変更 |
| S1 | Figure S3 分割 | 補足 | weasyprint `page-break-inside: avoid` 効かない件を調査 → OK なら適用、無理なら defer |
| S2 | Figure S2 | 対応不要 | 現状維持 |

---

## 全体判定

**V2 → V3 は Minor revision 対応 = 前段の V1 → V2 (Major revision 対応 = 追加解析 + panel model + case-crossover 3 tests + Table 4 新規) と比べて桁違いに軽い**。核心 3 + 精密 4 + 補足 1 = 8 site 編集、統計スクリプト再実行なし、pytest 全走 + PDF 再生成のみで round-3 提出可能。

**次アクション**: 上記 8 項目を反映 → V3 PDF 生成 → 瑞樹 GPT 送信 → round-3.md 予約。

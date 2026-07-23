# GPT V4 査読応答 (round-4)

- **受領日**: 2026-07-24
- **判定**: **Minor revision** (Major ではない・体裁中心)
- **総評**: 中身はかなり良くなってる。統計まわりの大きな穴はかなり塞がれてる。今の問題は論文としての見た目・Abstractの長さ・Supplementaryの扱い・表図の配置。ここ直したらかなり締まる。

---

## 絶対直すべき体裁 (8項目)

### 1. Abstract が長すぎる

Methods と Results が詰め込みすぎ。Abstract内で、case-crossoverの3検定、47都道府県NBパネル、都道府県別forest plot、cluster-robust、small-cluster correction、residual diagnostics まで全部書いている。
さらに結果も、conditional Poisson、sign test、permutation、都道府県別fit、Mie、fatal subgroupまで入っている。

これは読者には重い。査読者にも「Abstractでやりすぎ」と見られやすい。

**削るならここ**:
- Figure S3 への言及
- "Full statistical detail..." の文
- small-cluster correction / residual diagnostics
- Mie prefecture の話
- fatal accident の細かいCI

Abstractは、
> We reproduced three prior methods and added case-crossover and prefecture-level panel analyses.

くらいで十分。

### 2. Supplementary Materials と Figure S1-S3 の扱いが不整合

本文では "Supplementary Materials" と書いているが、実際のPDFでは Figure S1〜S3 が本体後半にそのまま入っている。ページ18は "Figures" だけで、Figure 1、Figure 2、その後に Figure S1〜S3 が続く構成。

これは直した方がいい。選択肢は2つ:

**A案：本体に入れるなら**
Figure S1〜S3 を Figure 3〜5 に改名。本文の "Supplementary Figure S1/S2/S3" も全部 "Figure 3/4/5" にする。

**B案：Supplementaryにするなら**
本体PDFから Figure S1〜S3 を外して、別ファイル "Supplementary Materials" にする。
その場合、ページ18の見出しは "Figures" のままでよいが、S図は別紙へ。

今の「本体にあるのにS番号」は中途半端。

### 3. Figure S3 のキャプションがページまたぎしている

Figure S3 のキャプションが23ページから24ページにまたがって、24ページに2行だけ残っている。これは見た目が悪い。論文体裁としてかなり目立つ。

**対応**:
- Figure S3を少し小さくする
- captionを短くする
- Supplementaryへ移す
- 24ページに単独で移す

どれか。今のままは避けたい。

### 4. ページ18が "Figures" だけの空白ページになっている

ページ18は見出し "Figures" だけで、実質空白ページになっている。これはかなり勿体ないし、PDFとして間延びして見える。

**修正案**:
- "Figures" 見出しと Figure 1 を同じページに入れる
- または "Figures" 見出しを削って Figure 1 から始める

### 5. Table 1 の注が長すぎる

Table 1 の注がかなり長い。control定義、all other Fridaysとの違い、Scanlon comparisonとの違い、arithmetic meanとgeometric meanの違いまで全部入っている。

内容は正しいけど、表注としては重い。Methodsに移して、表注はこれくらいでよい:

> Same-month other Fridays exclude Friday the 13th. The arithmetic per-pair ratio is descriptive; the geometric mean ratio is the estimand used in the case-crossover permutation analysis.

これで十分。

### 6. Table 4 の dagger が見た目として悪い

Fatal accidents の NB-adjusted count ratio が、
```
1.227 [0.9997, 1.5061]
†
```
みたいに dagger が別行に落ちている。これは体裁上かなりダサい。

**こう直す**:
```
1.227 [0.9997, 1.5061]†
```
同じセル内で絶対に改行させない。表幅が足りないなら "0.9997–1.5061" を "1.00–1.51†" に丸める方がよい。

### 7. Abstract の fatal CI 表現が危ない

Abstractでは fatal accidents について、
> 1.23 (95% CI, 1.000-1.506, marginal lower bound)

と書いている。でも本文では exact bounds が 0.9997–1.5061 で、strictには1.0を超えていないと説明している。

Abstractで "1.000" と書くと、読者によっては「ギリ有意？」と誤読する。ここはこうした方が安全:

> Poisson-approximation estimate was borderline and did not survive multiple-comparison correction.

数値をAbstractから削っていい。入れるなら、
> 1.23; approximate 95% CI, 1.00–1.51

くらい。

### 8. Reference numbering は見た限り大丈夫。ただし "Ref [12]" は直す

References自体は1〜16で通っている。1〜12がページ13、13〜16がページ14に続いていて、可視上の番号ズレは見当たらない。

ただし本文中に、
> Phillips et al.'s methodological anchor (Ref [12])

という表記がある。これは文体が浮く。普通に、
> Phillips et al.'s methodological anchor, although widely cited, …

または
> Phillips et al.'s study, although widely cited, …

でよい。引用番号は通常の上付き/文献番号だけで足す。

---

## できれば直す体裁 (4項目)

### 9. Corresponding author 欄の文字間が不自然

1ページ目の Corresponding author の行が、PDF上で単語間スペースがかなり広く見える。本文抽出上も連絡先情報が複数行に割れている。
ここは左揃え・非均等割付にした方がきれい。

### 10. "Fri13" は本文では少し軽い

Methods/Results/Figuresで "Fri13" が多い。短縮として便利だけど、論文としてはややカジュアル。
初出で、
> Friday the 13th (Fri13)

と定義するならOK。そうでなければ "Friday the 13th" に統一した方が無難。

### 11. Figures S1–S3 のキャプションが長い

S1〜S3のキャプションは情報量が多く、本文の説明と重複している。特にS3は長すぎてページまたぎの原因になっている。
図キャプションは短くして、詳細はResults本文かSupplementary textへ。

### 12. "Supplementary Materials" と言うなら Supplementary heading が必要

本文では Supplementary Materials と複数回出てくる。でもPDF内に "Supplementary Materials" という独立セクションはない。
S図を残すなら、ページ21前に
> Supplementary Figures

という見出しを入れるだけでも整う。

---

## 内容面の大きな印象

前版よりかなり良い。特に、
- individual-level record と aggregate analysis の倫理記述の矛盾が直っている
- count ratio 表記に寄せている
- fatal事故の扱いがかなり慎重になっている
- cultural mediation と null-everywhere のバランスが良くなっている
- panel model、diagnostics、cluster SE まで入っていて査読耐性が上がっている

ただし今は方法の詳細を本文に詰め込みすぎて、読み物として少し重い。SSRNなら許容だけど、査読誌に投げるなら、Methodsを少し削ってSupplementaryに逃がす方が見栄えがいい。

---

## 最優先修正リスト (GPT 明示・実装順序参考)

1. Abstractを半分くらいに圧縮
2. Figure S1〜S3を本体Figure 3〜5にするか、Supplementaryへ分離
3. ページ18の空白見出しページを解消
4. Figure S3のキャプションまたぎを解消
5. Table 1注を短縮
6. Table 4の dagger 改行を修正
7. "Ref [12]" を削除
8. Abstractの fatal CI "1.000" 表記をやめる

これ直せば、体裁はだいぶ査読誌っぽくなる。番号振りの致命的ミスは見当たらない。

---

## クロコン反映方針 (2026-07-24 着手)

- **Figure 命名判断 = A案 (Figure 3-5 統合) 採用** (自己判断・PLAN-DEVIATIONS #3 起票):
  - SSRN 単一 PDF 投稿志向 + 機械的通し番号化で最小コスト
  - B案 (別ファイル分離) は generate_pdf.py 分岐 + Supplementary 別 PDF 生成のコスト大
  - GPT自身「SSRNなら許容」明言・本体一体化で章立て整理は成立
  - PLAN L298「Supplementary Figures 節新設」予定を **逸脱 → 本体 Figures 節に統合**
- 12 項目全部 V5 で一括反映 → asura-monju round-2 挟む → commit + push + Desktop 配置
- pytest 214/214 保持必須 (統計 script 非変更 = 数値 model intact 想定・変更は manuscript.md + generate_pdf.py のみ)

# GPT査読 Round 1 (2026-07-22)

**投げたPDF**: `~/Desktop/friday13_SSRN.pdf`（14ページ・437KB・著者情報修正済み版=commit `1dc803c`）
**査読者**: ChatGPT（瑞樹が手動で投げて結果を貼付）
**判定**: **Major revision**

---

## 総評

アイデアはかなり良い。日本を「13恐怖が弱い自然対照」として使い、約188万件の警察交通事故データで Friday the 13th を検証する設計は面白いし、SSRN/preprintとしては十分読める。
ただし、査読誌に出すなら結論の強さ・統計モデル・文化媒介仮説の扱いを直さないと突っ込まれると思うにゃ。

この論文は、2019–2024年の日本の交通事故1,884,793件を使い、10回の Friday the 13th と他の金曜日を比較している。Scanlon法、Näyhä法、Lo法、case-crossover、共変量調整NB回帰を使い、全体として有意な増加なし、という主張になっている。結果も概ね一貫して null で、Scanlon法 RR=1.04、Näyhä型 NB IRR=1.01、Lo法 ANOVA p=0.93、調整NB IRR=1.02 とされている。

ただ、「文化的媒介を検証した研究」なのか、「そもそも世界中どこでも効果はなさそう」という null everywhere 論文なのかが途中で揺れている。Discussionでは、最終的に「利用可能な証拠は null-everywhere interpretation に傾く」と書いている。これは悪くないけど、タイトル・Abstract・Conclusionの「文化的対照実験」感とはややズレる。

---

## Major comments

### 1. 結論が強すぎる

本文では「Japan provides a natural control population」として始めているが、実際に測っているのは日本における交通事故数であって、日本人個人の triskaidekaphobia、認知、行動変化ではない。
したがって言えるのは、

> 日本の全国交通事故データでは、Friday the 13th に大きな事故増加は検出されなかった。

まで。

「文化的に媒介される」という仮説については、支持的ではあるが、直接検証ではない。特にDiscussionで「むしろ null everywhere が有力」と書いているので、結論はこう寄せた方が安全。

**修正案:**
> These findings do not support a large population-level Friday the 13th effect in Japan. Although the study was motivated by cultural mediation, the broader literature may be more consistent with a universal null effect or, at most, very small effects.

今の "the effect disappears entirely" は削るべき。データからは「完全に消える」は言えない。

### 2. データの倫理記述に矛盾がある

Methodsでは、NPAの「individual accident records」を使い、発生日、時刻、場所、重症度、車種、運転者年齢、昼夜などが含まれると書いている。
一方でEthicsでは「fully aggregated population-level data」「No individual-level data were accessed」と書いている。

これは査読で確実に突っ込まれる。

たぶん正しくは、

> publicly available anonymized accident-level records were downloaded and aggregated to daily counts

のような表現。
「個票形式だが匿名化公開データ」「個人識別情報は含まない」「解析単位は日次集計」と整理した方がよい。

### 3. NB回帰の信頼区間が広すぎるのに、nullを強く言いすぎ

調整NB回帰の IRR は 1.02 だが、95% CI は 0.54–1.94 と非常に広い。これは「大きな正負の効果も統計的には排除できていない」形。
Power analysisでは、80% powerで検出可能なのは約16.2%以上の差と書いている。なので本文の主張は、

> large effects comparable to prior positive reports were not observed; small effects cannot be excluded

が妥当。

「not associated」はギリギリ許容だが、「no effect」「effect disappears entirely」は強い。

### 4. Negative binomial model の deviance/df=0.03 はむしろ怪しい

本文では、PoissonよりNBを選んだ理由として Pearson chi-squared/df=20.8、Poisson AIC=9660、NB AIC=4953 と説明している。ここまではよい。
ただし Results/Limitationsで deviance/df=0.03 や 0.02 を「adequate model fit」の根拠のように扱っている。

これは危ない。deviance/df が 1 より大幅に小さいのは、モデルが"よく合っている"というより、分散構造・スケール・alpha推定・過補正の問題を示唆する場合がある。

最低限、以下を追加した方がいい。

- NBの alpha / dispersion parameter
- 残差プロット
- Pearson residual の分布
- sandwich robust SE
- quasi-PoissonまたはPoisson with robust SEとの比較
- 年・月・季節トレンドの仕様感度分析

ここはMajor revisionポイント。

### 5. 天気変数の作り方が内生的かもしれない

Methodsでは、各事故を最寄り気象台にリンクし、その後日次平均にしたと書いている。
でも全国の日次事故数を目的変数にするなら、事故が多い地域の天気が重く反映される可能性がある。つまり、事故発生地点で重み付けされた天気になっており、曝露としての全国天気ではない。

より自然なのは、

- 都道府県別の日次事故数 × 都道府県別天気
- あるいは全国の人口・交通量・面積・観測所固定で平均した天気

にすること。

さらに、cloud coverだけでは交通事故の天候影響として弱い。雨、雪、降水量、積雪、路面状態がないなら、「weather-adjusted」と強く言わない方がいい。

### 6. case-crossover の検定が弱い

case-crossoverでは、10個の Friday the 13th ごとに同月他金曜日平均との差を比べ、平均比1.05、p=0.32としている。
ただ、n=10の比率に対する t-test はやや雑。8/10で高かったという記述もあるので、読者によっては「方向性はあるのでは？」と見る。

より良いのは、

- month-stratified conditional Poisson model
- matched negative binomial model
- permutation test
- exact sign test
- paired log-ratio の検定

あたり。

今の結果でも結論は変わらないと思うが、方法としては補強した方がよい。

### 7. fatal accident signal の扱いは透明性あり。ただし表が必要

Fatal accidentsで RR=1.31、p=0.013 と出ているが、Bonferroni後は有意でない、件数も小さい、と説明している。この扱い自体は誠実。
ただし、査読では「そのp値は何の検定か？」「調整後pはいくつか？」「NBではどのIRR・CIか？」を求められる。

Tableに以下を出した方がいい。

```
subgroup    Fri13 mean    control mean    RR    95% CI    raw p    adjusted p
```

本文の「no plausible mechanism」は少し強い。機序がないというより、本データでは再現性・多重性・小標本の問題から偶然と解釈するのが妥当くらいがよい。

### 8. 「systematic comparison」は言い過ぎ

Table 3で既存研究を並べているのは有用。
ただし、検索式、選択基準、除外基準、抽出方法がないなら "systematic comparison" より "narrative comparison" か "structured comparison" が安全。

また、Table 3の "Cultural fear of 13: Strong / Moderate / Absent" はかなり主観的。査読者に刺されやすい。
定性的分類として残すなら、

> Cultural salience of 13 was classified qualitatively based on prior cultural descriptions and should be interpreted descriptively.

のような注記がいる。

---

## Minor comments

- Titleの "Has No Bite" はBMJ Christmas風で悪くないが、通常誌ならややカジュアル。堅く行くなら
  `"Friday the 13th and Traffic Accidents in Japan: A Natural Cultural Control Study of 1.9 Million Police Records"`
- "floor 13 and room 13 are universally present" は強すぎる。13階が存在しない低層建築も多いし、「13を避ける慣習は一般的でない」くらいに修正すべき。
- "IRR" と書いているが、本文でも認めている通り、曝露offsetなしの日次count ratioなので、全体を "count ratio" に統一した方が厳密。
- "Python 3.14" は本当にその環境で解析したか確認。パッケージバージョンも書くべき。
- Reference sectionの後に「1. 2. 3. …」みたいな残骸が入っている。これは削除必須。
- Acknowledgmentsの「All references were verified against PubMed and CrossRef」は、書籍やプレスリリースも含むなら不正確。 "where applicable" を付けるべき。
- Table 1の "same-month control mean" と、本文の "Friday 6th mean" と、全other Fridays meanが混在している。読者が混乱するので、control定義を明確に分けるべき。
- Figure 1は見やすいが、Friday the 13th点が10個しかないことが視覚的に伝わりにくい。補助的にペア線プロット、またはsame-month ratio plotを追加するとよい。

---

## 採択可能性を上げる修正方針（GPT提案の芯）

一番大事なのは、論文の芯をこう整理すること。

> 本研究は、日本という13恐怖が弱い文化圏において、Friday the 13th に交通事故が増えるという大きな人口レベル効果を検出しなかった。これは文化媒介仮説と矛盾しないが、既存の大規模欧米研究も概ねnullであるため、現時点では「文化差」よりも「そもそも大きな効果は存在しない」解釈がより妥当である。

これなら強い。
今の原稿は面白いけど、少し「文化で説明したい」欲が前に出ていて、最後に自分で「いや、null everywhereかも」と言っている。その揺れを最初から設計に組み込むと、かなり締まる。

---

## 反映方針（クロコン整理・段取り八分ゴール宣誓後）

- **温度感**: GPT合格まで無制限反復・表現弱化許容・追加解析OK・フルスクラッチOK
- **反映範囲**: A文言 + B既存結果再表現 + **C追加解析全部**（NB診断/天気都道府県別再構築/case-crossover代替検定）を V2 に投げる方針
- **BMJ Christmas 保留**: Title カジュアル保持は却下、堅めに寄せる
- **論文の芯**: 「文化媒介 vs null everywhere」の swing を初手から null everywhere 主軸に統合する方向

次アクション: `PLAN-gpt-review-cycle.md` 立案（M1）→ 実装（M2）→ V2投げ（M3）

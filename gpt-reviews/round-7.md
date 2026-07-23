# GPT V7 査読応答 (round-7)

- **受領日**: 2026-07-24
- **判定**: **出してよい水準** (主張の骨格はかなり強い) + 査読耐性強化のための 5 個の推奨修正
- **総評**: 1,884,793 件の日本の警察交通事故データ、10 回の Friday the 13th、Western 既存手法の再現、case-crossover、47 都道府県 NB panel、感度分析、サブグループまで入っていて、論文としての体裁は十分ある。Abstract でも主要結果は一貫して「大きな効果なし」に収まっている。ただ「結果が良い」より「説明が少し強すぎる」箇所がある。ここを直せばかなり堅くなる。

---

## 直した方がいい重要ポイント (5 個)

### 1. "Japan has no fear of 13" は少し断定が強い

本文では、日本は 4 と 9 が不吉で 13 は伝統的に目立たない、という説明は妥当。ただ、結論や解釈で "culture without a fear of 13" や "absence of triskaidekaphobia" に近い言い方になると、査読者から「それを直接測ったのか?」と突かれる可能性がある。本文でも個人レベルの信念は測っていないと明記しているので、ここは慎重にした方がいい。

**修正案**:
- "a culture where 13 is not a traditionally salient unlucky number"
- "a setting without strong institutionalized triskaidekaphobic practices"

「恐怖がない」ではなく「伝統的・制度的な不吉数としての顕著性が低い」に寄せるべき。

### 2. Figure 2 がやや誤解を招く

Figure 2 では日本の点推定は 1 付近だが、赤い CI がかなり広く見える。一方で本文の primary panel model では count ratio 1.02, 95% CI 0.97-1.08 とかなり狭い。Figure 2 のキャプションは「CI shown where available」「Japan is highlighted with the largest sample size」と書いているが、図を見ると「最大サンプルなのに CI がめちゃ広い?」と読者が混乱する。

たぶん Figure 2 では Näyhä-method の広い CI を使っている。それならキャプションか脚注で:

> For the present study, the interval shown corresponds to the method-matched national-level Näyhä-style estimate, not the covariate-adjusted 47-prefecture panel estimate.

みたいに明記した方がいい。あるいは、Figure 2 に日本を 2 行出してもいい (method-matched + primary panel)。

### 3. 主解析が少し見えにくい

手法が多いのは強みだが、逆に「結局どれが primary なの?」が少しぼやける。査読者によっては kitchen-sink analysis に見える可能性がある。

**修正案**: Methods の Study design 末尾に一文追加:
> The primary inferential analysis was the covariate-adjusted 47-prefecture negative binomial panel model; the case-crossover tests and reproductions of prior Western methods were used as robustness and comparability analyses.

### 4. Mie prefecture の扱いは一文足した方がいい

都道府県別解析で Bonferroni と BH-FDR の両方で Mie だけ残っている。Results 本文では説明されているが、Discussion でほぼ処理されていない印象。査読者が「Mie はなぜ?」と聞きやすい。

**修正案**:
> The isolated Mie finding was in the protective direction, had no a priori hypothesis, and occurred without an excess of significant prefectures overall; we therefore interpret it as a local idiosyncratic fluctuation rather than evidence of a reproducible regional effect.

### 5. fatal accident signal の Abstract 表現をより慎重に

fatal subgroup は本文でかなり丁寧に扱えている。ただ Abstract で "borderline" だけだと読者の目を引きすぎる。

**修正案**:
> a sparse-count Poisson approximation for fatal accidents was borderline but exploratory and non-significant after correction

---

## 体裁・読みやすさ (任意)

- **Table 3 は少し詰まっていて行内改行が多い**。Cross-national comparison は重要なので、可能なら landscape 表か列を減らした簡略版にした方が読みやすい
- **結論文** "there is no evidence-based reason to check the calendar before starting the car" はキャッチーで良い。SSRN ならこのままでよい。査読誌なら一段階だけ抑える

---

## 結論

v7 はかなり良い。**出してよい水準**。直すなら優先順位はこれ。

1. "Japan has no fear of 13" 系の断定を弱める
2. Figure 2 の日本 CI が何を表すか明記する
3. primary analysis を明示する
4. Mie prefecture の孤立所見に Discussion で一文入れる
5. fatal subgroup の Abstract 表現を少し慎重にする

この 5 点を直せば、かなり査読耐性が上がる。文献そのものの外部照合とコード再現までは今回はしていない。「鵜呑みにせずに判断して」。

---

## クロコン判断結果 (2026-07-24 V8 着手)

| # | GPT 指摘 | 判定 | 判断根拠 |
|---|---|---|---|
| 1 | "Japan has no fear of 13" 断定弱化 | **採用** | 個人信念未測定明記との論理整合・査読耐性向上・「恐怖 → 顕著性低」で本文の慎重姿勢と一貫性 |
| 2 | Figure 2 日本 CI 明記 | **採用** (B 案 = caption 明示) | 事実確認: 03_figures.py L98 = point 1.02 (multi-method summary) + CI 0.54-1.94 (Näyhä-method) の estimator ミックス = fabricated combination。honest disclose 必要。C 案 (2 行出し) は 03 大改修 + PNG 再生成でコスト大なので B 案。ただし嘘は書けないので caption で「point = multi-method summary、CI = method-matched Näyhä-style」明示 |
| 3 | Primary analysis 明示 | **採用** | kitchen-sink 見え回避・panel を primary + 他手法を robustness と定義。Discussion L131 "five distinct analytical approaches" と整合 |
| 4 | Mie Discussion 一文追加 | **採用** | 事実確認: prefecture_irr_by_prefecture.json diagnostics.results から Mie の count_ratio = **0.6154** = protective direction 確定 (GPT 提案文言「protective direction」事実整合)。1 文追加のみ |
| 5 | Fatal Abstract 表現慎重化 | **採用** | post-hoc / multiple-testing 性を "exploratory" で明示 → 読者の目を引きすぎる問題回避 |
| 任意 | Table 3 landscape | **却下** | 現状 1 ページ完結 vs 03_figures 大改修コストの trade-off で維持。V6 の `page-break-inside: avoid` で解決済 layout に手を加えるリスク大 |
| 任意 | 結論文軽さ | **維持** | SSRN 投稿目的で許容範囲 (GPT 自身 "SSRN ならこのままでよい" 明言) |

**採用 5/5 + 却下 2 (任意分)**。「鵜呑みにせずに判断」を各項目で行使。

---

## 反映方針 (V8)

- **統計 script + generate_pdf.py 非変更**: 全部 manuscript.md の wording 修正のみ
- **PDF 全 22 ページ自己 QA 継続** (feedback-paper-pdf-selfqa-before-gpt.md 適用)
- **asura-monju round-2 引き続き skip** (PLAN-DEVIATIONS #4 継続適用・変更 5 箇所とも wording レベル・framing bomb リスク低)

## 次アクション見通し

- V8 = GPT round-7 反映後、round-8 応答受領へ
- round-8 で Accept 確定 = **M6 SSRN 投稿ガイド作成着手** = ゴール宣誓 SSRN POSTED 到達フェーズへ移行の分岐点
- Major 復活 (低確率) = 分岐条件発火 = 芯設計再壁打ちの是非を瑞樹相談

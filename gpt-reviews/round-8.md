# GPT V8 査読応答 (round-8)

- **受領日**: 2026-07-24
- **判定**: **v8 はほぼ投稿していい水準** (前回の主要 5 点はほぼ反映できてる) + 3 個の最終修正
- **総評**: v8 は完成間近。SSRN 版としてはもう十分。査読誌に出す場合でも、かなり戦える。

---

## まだ直した方がいい重要点 (3 個)

### 1. Figure 2 の CI が本文と不一致 (直すべき・査読者即気付く)

Abstract / Results では Näyhä-method count ratio が 95% CI **0.54-1.91**。
Figure 2 caption では **0.54-1.94** と書かれている。

どちらかに統一。たぶん本文側の 0.54-1.91 に合わせるのが自然。**重箱ではなく、査読者が普通に気づくタイプ**。

### 2. "where 13 carries no stigma" がまだ強い

Introduction 末尾に、
> it should be absent in Japan, where 13 carries no stigma.

が残っている。前回指摘した「個人信念未測定」とまだ少し衝突する。Discussion ではちゃんと「個人の triskaidekaphobia は測っていない」と慎重化できているので、ここだけ浮いてる。

**修正案**:
> it should be absent or markedly attenuated in Japan, where 13 is not a traditionally salient unlucky number.

### 3. Table 3 の Japan "Absent" は少し強い

Table 3 の Japan 行で "Cultural fear of 13" が **Absent** になっている。本文全体の慎重さに合わせるなら、ここも:
- **Low**
- **Not traditionally salient**

くらいが安全。列名も本当は "Cultural salience of 13" の方がよいけど、表を大きく直したくないなら Japan 行だけ変えればいい。

---

## 反映済みで良いところ

- **Primary analysis** の明示は良い。分析の軸がかなり見えやすくなった
- **Fatal accident signal** も、Abstract で「borderline but exploratory and non-significant after multiple-comparison correction」となっていて、過剰解釈を避けられている
- **Mie の一文** も入っていて良い。protective direction、no a priori hypothesis、local idiosyncratic fluctuation という整理で十分
- **Figure 2 caption の説明追加** も方向性は良い。本文との CI 不一致だけ直せば OK

---

## 結論

**v8 は完成間近。直すならこの 3 つだけ。**

1. Figure 2 caption の 0.54-1.94 → 0.54-1.91 に統一
2. Introduction の "where 13 carries no stigma" を弱める
3. Table 3 の Japan Absent を Low / Not traditionally salient にする

これ直したら、SSRN 版としてはもう十分。査読誌に出す場合でも、かなり戦える。

「鵜呑みにせず判断して」

---

## クロコン判断結果 (2026-07-24 V9 着手)

| # | GPT 指摘 | 判定 | 判断根拠 |
|---|---|---|---|
| 1 | Figure 2 CI 統一 | **採用** (B 案 = 03_figures.py + PNG + caption 三点修正) | **事実確認**: truth.json の nayha_ci_high = **1.9071181646685924** → 0.54-1.91 が真値 (Abstract L21 と一致)。03_figures.py L98 の CI high 1.94 が古い hardcoded 数値 (V5 Abstract 圧縮時の Näyhä 精度修正が Figure 側に伝播してなかった)。caption だけ書き換えると image 内 CI と不一致で悪化 → source 修正必須 |
| 2 | "where 13 carries no stigma" 弱化 | **採用** | 前回 V8 の Japan 断定弱化 (Abstract Conclusions + Discussion Interpretation) と同論理・Introduction L39 だけ浮いてた漏れを潰す |
| 3 | Table 3 Japan "Absent" → "Low" | **採用** | 表内文言も本文の慎重姿勢と統一・Japan 行 1 セルの変更のみで最小コスト・列名変更は却下 (大改修回避) |

**採用 3/3**。「鵜呑みにせず判断」を各項目行使 (事実確認 1 件 + 論理整合 2 件)。

---

## 反映方針 (V9)

- **03_figures.py 1 行修正 + PNG 1 枚再生成** (Figure 2 の CI 数値のみ・工数極小)
- **manuscript.md 3 箇所修正**: Figure 2 caption 数値 + Introduction 弱化 + Table 3 Japan cell
- **statscript 非変更**: `03_figures.py` は figure 生成専用で統計 model には影響なし
- **PDF 全 22 ページ自己 QA 継続** (feedback-paper-pdf-selfqa-before-gpt.md 適用)
- **asura-monju round-2 引き続き skip** (PLAN-DEVIATIONS #4 継続適用・変更範囲マイクロ)

## 次アクション見通し

- V9 = GPT round-8 反映後、round-9 応答受領へ
- round-9 で Accept 確定 = **M6 SSRN 投稿ガイド作成着手** = ゴール宣誓 SSRN POSTED 到達フェーズへ最終移行の分岐点

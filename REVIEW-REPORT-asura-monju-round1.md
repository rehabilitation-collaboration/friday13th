# REVIEW REPORT: Asura-Monju Round 1 (V4 pre-submission review)

**Date**: 2026-07-23 深夜
**System**: Asura (Sonnet ×3 parallel) + Monju (Opus ×1 verifier)
**Paper**: `~/claude/analysis/friday13th/manuscript.md` (V4 draft)
**Cycle**: 投稿前最終 QA (GPT round-3 で Accept 判定・"wide CI" 修正済 → asura-monju 発火)

---

## Review Statistics
- Asura: 49-item checklist × 3 agents, 31 unique findings after 2/3+ vote filter
- Monju verification: **ACCEPT 21 / PARTIAL 3 / REJECT 7** (Part A)
- Monju independent: **P1×1 (safeguard) + P2×3 + P3×5** (Part B)
- Pre-processing: verify_refs.py (11/16 MATCH, 4 MISMATCH → all resolved as artifacts), number_verification.py (43/43 MATCH)

---

## Critical Findings (P1) — Author 対応必須

| # | ID | Issue | Source | Action Required |
|---|-----|-------|--------|----------------|
| P1-1 | E-01 | 内部 code/path leak (4 箇所): (a) Methods "Model diagnostics (Phase 2C-C1)" (b) Table 4 footnote "output/subgroup_table4_results.json" + "\`is_friday13th\`" + "per_subgroup" (c) Figure S1 legend "03_primary specification" + "is_fri13 estimand" (d) Figure S2 legend "\`output/case_crossover_results.json['pair_summary']['pairs']\`" | Asura(3/3) + Monju verify ACCEPT | 全 code/path/phase 表記削除、natural language に置換 |
| P1-2 | A-24 | Abstract "three original analyses (i)(ii)(iii)" vs Methods "two original analyses" 矛盾 | Asura(3/3) + Monju ACCEPT | Methods を 3 に統一 (case-crossover + panel + prefecture-specific fits を独立節に) or Abstract を 2 に統一 |
| P1-3 | A-02 | Discussion 内 "three methods that had previously detected effects" vs "two of which had reported positive findings" 矛盾 (round-2 fix の partial apply) | Asura(3/3) + Monju ACCEPT | 前者を後者に整合 or clarifying phrase 追加 |
| P1-4 | A-24 | Table 1 footnote "matches the arithmetic mean quoted in the abstract" は Abstract に 1.05 存在せず (Abstract は 1.04 geometric のみ) | Asura(3/3) + Monju ACCEPT | 脚注書換 = "1.05 is the per-pair arithmetic mean (an alternative summary), while the Abstract quotes the case-crossover geometric-mean count ratio 1.04" |

## Important Findings (P2) — 投稿前対応推奨

| # | ID | Issue | Source | Action Required |
|---|-----|-------|--------|----------------|
| P2-1 | E-01 | "earlier drafts" 参照 4 箇所 (Table 1 note / L107 case-crossover / L143 fatal / L153 Sixth limitation) | Asura(阿修羅 3) + Monju ACCEPT | 削除 or Supplementary Methods へ移動 |
| P2-2 | E-03 | abbreviations 未定義: CI, IRR, CRVE, GLM (全て初出で spell out 無し); OR/ED/EMS/NegBin は Table 3 脚注まで未定義 (Introduction 初出) | Asura(3/3) + Monju ACCEPT PARTIAL | 全 abbreviation 初出で spell out 追加 |
| P2-3 | B-07 | Methods "All statistical tests were two-sided" vs Results/Figure S3 legend "one-sided binomial" 矛盾 | Asura(3/3) + Monju ACCEPT | Methods L89 に "with the exception of the one-sided binomial excess test for prefecture-level heterogeneity" 追記 |
| P2-4 | B-11 | 95% CI notation "(95% CI: lo-hi)" vs "[lo, hi]" 混在 (Abstract L21 vs Results L107 で同 statistic に異表記) | Asura(3/3) + Monju ACCEPT | 全 CI を "(95% CI: lo-hi)" or "[lo, hi]" に統一 (推奨: AMA style "95% CI, lo-hi") |
| P2-5 | B-13 | p-value spacing "p=0.XX" vs "p = 0.XX" 混在 | Asura(3/3) + Monju ACCEPT | 全て "p = 0.XX" に統一 (AMA style) |
| P2-6 | E-04 | Figure S2 body 参照ゼロ (legend のみ) — S1/S3 は複数箇所引用 | Asura(3/3) + Monju ACCEPT | Results Case-crossover paragraph or Discussion で Figure S2 引用追加 |
| P2-7 | A-24 (reframed) | Scanlon "52%" vs "1.44" 用語混同 (両方 Scanlon の数値だが 52% = traffic-adjusted risk ratio 1.52 / 44% = raw admissions ratio 1.44 = 65/45) | Asura(1) + **Monju verify partial (P1→P2)** | "Scanlon reported a 52% risk-ratio conclusion derived from 65 vs 45 raw admissions (raw ratio 1.44) after adjusting for a 1.4% traffic-volume drop on Fri13" 相当に clarify |
| P2-8 | A-12 | "post-hoc power" 用語問題 = observed-power と混同されるリスク。実質は MDE (minimum-detectable-effect) 分析 | Asura(阿修羅 3) + Monju ACCEPT | "post-hoc sensitivity analysis of statistical power" → "sensitivity power analysis (minimum detectable effect calculation)" |
| **P2-9 (Monju 独自)** | E-05/B-25 | Table 1 の "same-month other Fridays (mean)" 列 (990.9) は Abstract "988.6" (全 303 non-Fri13) と Results Scanlon "982.9" (Fri 6 のみ) と 3 種類の異なる控除定義。読者に決定不能 | **Monju independent P2** | Table 1 caption or column header を "Same-month controls (mean of Fri 6/20/27)" に明示 + Table 2 の "988.6" 定義も同節で対比 |
| **P2-10 (Monju 独自)** | D-07 | Phillips (Ref 12) を "landmark" として cite するが Smith 2002 BMJ critique + Panesar 2003 MJA failed replication に言及なし。cultural-mediation 仮説の anchor が contested とは書かない = scientific integrity concern | **Monju independent P2** | Discussion L135 or L147 に Phillips 2001 の replication issue を 1-2 sentence で言及 |

## Minor Findings (P3) — 体裁・可読性

| # | ID | Issue | Source | Action Required |
|---|-----|-------|--------|----------------|
| P3-1 | E-04 | Table 3 orphan footnote "'not confirmed' indicates..." が cell に存在せず (cells は "N/A") | Asura(3/3) + Monju ACCEPT | 脚注削除 or cell を "not confirmed" に変更 |
| P3-2 | A-16 | "Exploratory subgroup analyses examined 8 pre-specified subgroups" 自己矛盾 (registry 引用無し) | Asura(2/3) + Monju ACCEPT | "Exploratory" 削除 or "pre-specified in the analysis plan (see GitHub commit history)" 明示 |
| P3-3 | E-01 | "Cameron & Miller" (ampersand) vs "Cameron-Miller" (hyphen) 混在 | Asura(阿修羅 2) + Monju ACCEPT | 全て "Cameron-Miller" (hyphen) に統一 |
| P3-4 | E-01 | narrative "Author Year" (Results Cross-national comparison / Discussion) vs superscript (Introduction/Methods) 引用スタイル混在 | Asura(阿修羅 1) + Monju ACCEPT | 全て superscript に統一 (AMA journal 要件) |
| P3-5 | E-04 | Näyhä 1.63 = Introduction "adjusted rate ratio" vs Results "IRR" 表記不統一 | Asura(阿修羅 1) + Monju ACCEPT | Näyhä 元論文の "adjusted rate ratio" に統一 |
| P3-6 | B-16 | Table 3 Ranganathan (adjusted OR=1.02) + Lo (penetrating OR=1.65) が cells で OR mark 無し (脚注 "RR unless otherwise specified") | Asura(阿修羅 1) + Monju ACCEPT | Table 3 cell に "1.02 (OR)" / "1.65 (OR)" 追加 |
| P3-7 | C-01 | Ethics 節 Helsinki declaration invocation = aggregate anonymized data には category mismatch | Asura(阿修羅 2) + Monju PARTIAL | Helsinki 削除 or "Japanese Ethical Guidelines for Medical and Biological Research" のみに限定 |
| P3-8 | E-01 | References [6][8] "3 authors + et al." vs [9] 10 authors 全 spell out inconsistency | Asura(阿修羅 3) + Monju ACCEPT | Ref [9] を "Shekhar AC, McCartin M, Kimbrell J, et al." に truncate (AMA style) |
| P3-9 | B-13 | Fatal p=0.05 boundary precision: Table 4 "0.050" vs Results/Discussion "p = 0.05" | Asura(阿修羅 3) + Monju ACCEPT | 全て "0.050" に統一 (境界値の precision 保持) |
| P3-10 | A-15 | "0.01 spec-robustness threshold" Results L111 のみ使用、Methods で pre-specify 無し | Asura(阿修羅 3) + Monju ACCEPT | Methods "Model diagnostics" paragraph に threshold pre-specification 追加 |
| P3-11 | A-15 | "Excl. COVID + holidays" = Methods (2)/(3) どちらか不明 | Asura(阿修羅 3) + Monju PARTIAL | Table 2 caption or Methods L73 に "both national holidays and Obon/New Year" 明示 |
| P3-12 | B-18 | Full regression coefficient table 未収載 (external GitHub のみ) | Asura(阿修羅 2/3) + Monju ACCEPT | Supplementary Table S1 として panel model 全係数 (weather/holiday/year/month/weekday FE) 追加 |
| P3-13 | E-04 | % 表記 "0.013 %" (space) vs "52%" (no space) 混在 (space 1 箇所のみ) | Asura(阿修羅 1) + Monju ACCEPT | "0.013%" に修正 (no space, AMA style) |
| P3-14 | B-17 | Näyhä paragraph だけ "count ratio not IRR" caveat = Scanlon/Table 3 も raw count 使用でも caveat なし | Asura(阿修羅 3) + Monju ACCEPT | Scanlon paragraph にも同等 caveat 追加 or Näyhä caveat を統合的表現に |
| P3-15 | E-01 | Author affiliation "^1^" vs Scanlon citation "^1^" superscript ambiguity | Asura(阿修羅 1) + Monju ACCEPT | 現状 minor 判定・保留 |
| **P3-16 (Monju 独自)** | D-01 | Ref [5] CVS 2008 press release lacks URL / archive.org link (実物存在確認済だが reproducibility standards 未満) | **Monju independent P3** | Ref [5] に archive URL or Wayback capture link 追加 |
| **P3-17 (Monju 独自)** | A-22/B-25 | Table 4 fatal CI [1.000, 1.506] p=0.050 境界値 precision (3-4 decimals で真の 1.0 除外か graze か表示推奨) | **Monju independent P3** | Table 4 fatal 行の CI lower を "1.0002" or "0.9998" 相当に精度上げ (Poisson approx の実 CI 確認) |
| **P3-18 (Monju 独自)** | E-06 | Running title "Friday the 13th and traffic accidents in Japan" = main title 縮約のみ (weak) | **Monju independent P3** | AMA style running title は短縮版 (< 50 chars) 推奨: "Friday 13th and Japanese traffic accidents" 相当に |
| **P3-19 (Monju 独自)** | A-19 | Discussion Sixth limitation ~140 words の GLM/dispersion/CRVE 技術詳細 = Supplementary 級 | **Monju independent P3** | Sixth limitation を短縮 (2-3 sentence) して詳細を Supplementary Methods へ |
| **P3-20 (Monju 独自)** | E-08 | Fatal signal Discussion Lo 対比の clarity: "This echoes Lo et al.'s isolated penetrating trauma finding" は systematic pattern と誤読リスク | **Monju independent P3** | "Lo et al. also reported an isolated positive finding in a subgroup (penetrating trauma) that most reviewers now interpret as multiple-testing noise" 相当に clarify |

---

## Rejected by Monju (対応不要)

| # | Asura Finding | Rejection Reason (Monju) |
|---|--------------|-----------------|
| R1 | Ref [5] CVS 2008 CrossRef mismatch (Wiechers 2012 に auto-match) | **CVS 2008 press release は Web で存在確認済** (Vereende / autoschadeportaal 等 secondary sources が cite)。CrossRef が press release を index できないだけの preprocessing artifact。実物正しい |
| R2 | Ref [10] Vyse 2014 CrossRef mismatch (1997 版に auto-match) | **Vyse Updated Edition 2014 (Oxford Univ Press, ISBN 978-0199996926) 存在確認済**。CrossRef が updated edition を index せず 1997 一版のみ index。preprocessing artifact |
| R3 | Ref [11] Davies & Ikeno 2002 CrossRef mismatch (Moore 1967 に auto-match) | **Davies & Ikeno 2002 (Tuttle, ISBN 0804832951) 存在確認済**。CrossRef が別書籍と混同 (同名 title "The Japanese Mind" 別書籍あり)。preprocessing artifact |
| R4 | Ref [15] Cameron "AC" vs "Colin A" | **AMA style "AC" = "A. Colin Cameron" の standard initials 表記**。実質同一。cosmetic mismatch |
| R5 | C-12 ICMJE "funder had no role" 明記無し | **funder 存在せず** = ICMJE clause N/A |
| R6 | Phillips (ref 12) topical fit weak (floor-numbering claim) | **Phillips citation は "belief-mediated behavior alters mortality" の argument に対する引用**、floor-numbering 具体的 claim ではない。context 適切 |
| R7 | Scanlon "52%" arithmetic P1 (65/45=1.44 だから 44% not 52%) | **P1 拒絶 → P2 に降格**: 52% は Scanlon の traffic-adjusted risk ratio (1.52)、44% は raw admissions ratio (1.44)。両方 Scanlon の数値だが別 estimand。P2 = terminology conflation で対応 |

---

## Overall Verdict

**投稿レベル gate = 未達 (P1×4 + P2×10 + P3×20 残)**。GPT round-3 の "Accept" 判定は英語圏 reader impression baseline だが、asura-monju による論文体裁徹底検査で計 34 findings 検出。特に:

1. **内部 code/path leak (P1-1) は publication critical** = 論文致命的
2. **論理的自己矛盾 (P1-2, P1-3, P1-4) = reviewer に "この著者 draft management できてない" と即判定される**
3. **Scanlon 52% vs 44% 用語混同 (P2-7) = reviewer が原典と照合する定番チェック**、対応必須
4. **Phillips 2001 replication critique 未言及 (P2-10) = 論文の anchor が contested とは書かない scientific integrity concern**

**推奨反映順序**:
1. P1×4 全対応 → 論理整合確認
2. P2×10 全対応 → 用語・体裁・引用の統一
3. P3×20 の中で high-impact (Ref [9] 短縮 / Cameron-Miller 統一 / Sixth limitation 簡潔化 / Supplementary Table S1 追加) を優先
4. P3 の中で minor cosmetic (author affiliation superscript 等) は 保留 or 次 iteration

反映後: 全 pytest + number_verification + PDF 再生成 → GPT round-4 送信で最終確認。

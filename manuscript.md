# Friday the 13th and Traffic Accidents in Japan: A Natural Cultural Control Study of 1.9 Million Police Records

**Running title:** Friday the 13th and traffic accidents in Japan

## Authors

Mizuki Shirai, MHS^1^

^1^ Specified Nonprofit Corporation Rehabilitation Collaboration, Suita, Osaka, Japan

**Corresponding author:** Mizuki Shirai, MHS, Specified Nonprofit Corporation Rehabilitation Collaboration, Suita, Osaka, Japan. Email: rehabilitation.collaboration@gmail.com. ORCID: 0009-0005-3615-0670.

---

## Abstract

**Background:** Evidence on whether Friday the 13th increases accident risk remains inconsistent and methodologically contested, with reported effects ranging from a 52% increase in hospital admissions to null findings. Japan, where the number 13 carries no cultural superstition, provides a natural control population to test whether the "Friday the 13th effect" is culturally mediated.

**Methods:** We analyzed nearly 1.9 million police-recorded traffic accidents (1,884,793 records) across Japan (2019-2024), comparing accident counts on 10 Friday the 13ths against other Fridays. To enable direct comparison with prior Western studies, we reproduced three established analytical approaches: the Scanlon paired comparison (Friday 13th vs. Friday 6th), the Näyhä negative binomial regression, and the Lo multi-date ANOVA method. We additionally performed (i) case-crossover analysis on 10 same-month Friday strata using three complementary tests—a month-stratified conditional Poisson regression with Cameron-Miller cluster-robust t(G-1) inference, an exact sign test, and a sign-flip paired log-ratio permutation test with full 2^10 enumeration; (ii) a covariate-adjusted negative binomial panel model with 47 prefecture fixed effects, prefecture-level daily weather (cloud cover, precipitation, snowfall, snow depth) and holiday indicators, and two-way (prefecture, date) cluster-robust standard errors, complemented by a Cameron-Miller pair cluster bootstrap on the prefecture axis for finite-G sensitivity; and (iii) 47 prefecture-specific negative binomial fits with HC1 heteroscedasticity-robust standard errors, summarized as a forest plot (Figure S3). Subgroup analyses examined accident severity, age groups, and time of day.

**Results:** Across all analytical approaches, no large Friday the 13th effect was detected. The Scanlon-method rate ratio was 1.04 (paired t-test p=0.47), the Näyhä-method count ratio was 1.01 (95% CI: 0.54-1.91, p=0.97), and the Lo-method ANOVA showed no between-group differences (F=0.16, p=0.93). The month-stratified conditional Poisson case-crossover regression gave a count ratio of 1.04 (95% CI: 0.95-1.14, sandwich-t(G-1) p=0.40); the companion exact sign test (8 of 10 pairs favored Fri13, p=0.11) and sign-flip permutation test (exact p=0.45 across all 2^10 sign patterns; geometric count ratio 1.04) were also null. The 47-prefecture negative binomial panel model with weather and holiday adjustment yielded a count ratio of 1.02 (95% CI: 0.97-1.08, two-way cluster p=0.36); the wide confidence interval indicates that large effects can be excluded, but small effects cannot. Prefecture-specific fits ranged from 0.59 (Tottori) to 1.29 (Iwate) with a median of 1.01; 5 of 47 nominally exceeded the null (binomial excess-test p=0.08 versus α=0.05), and after Bonferroni or Benjamini-Hochberg correction only Mie prefecture remained significant. Fatal accidents restricted to Friday-vs-Friday comparisons showed a crude rate ratio of 1.31 (Welch t-test raw p=0.09, Bonferroni-adjusted p=0.70), with a Poisson-approximation NB-adjusted count ratio of 1.23 (95% CI: 1.00-1.51) that did not survive multiple-comparison correction across the 8 pre-specified subgroups. All sensitivity analyses excluding COVID-period data, holidays, and Obon/New Year periods yielded consistent null results (RR range: 1.01-1.06).

**Conclusions:** In this large national dataset from a culture without a fear of the number 13, Friday the 13th was not associated with a detectable population-level increase in traffic accidents. Large effects of the magnitude reported by earlier Western studies can be excluded, but small effects cannot. Although the study was motivated by a cultural-mediation hypothesis, our null findings---combined with recent large studies from Western populations that also report no effect---are more consistent with a universal null effect than with a purely culturally mediated one. The absence of a large effect in Japan therefore adds to the growing evidence that Friday the 13th has, at most, only a very small influence on population-level accident rates in any country studied to date.

**Keywords:** Friday the 13th, triskaidekaphobia, traffic accidents, superstition, cultural epidemiology, Japan, cross-national comparison

---

## Introduction

Is Friday the 13th truly unlucky? In 1993, Scanlon and colleagues published a now-classic study in the BMJ's Christmas issue reporting that hospital admissions from transport accidents in southwest England were 52% higher on Friday the 13th compared with Friday the 6th.^1^ The finding captured public imagination and has been widely cited, but subsequent research across Western nations has produced conflicting results.

Näyhä reported a 63% higher risk of traffic death among Finnish women on Friday the 13th (adjusted rate ratio 1.63), though men showed no effect;^2^ Radun and Summala directly contradicted this, finding no increase for either sex in Finnish injury accidents.^3^ Smith noted that Näyhä's analysis conflated date of death with date of accident---people who died on Friday the 13th may have been injured on a different day---potentially introducing survival bias.^4^ Dutch insurance data showed a 4% decrease.^5^ Subsequent larger studies have consistently found null results: Schuld et al. (n=27,914 surgical patients, Germany),^6^ Lo et al. (n=49,094 ED visits, USA; though penetrating trauma showed an isolated OR=1.65),^7^ Ranganathan et al. (n=19,747 surgical patients, Canada; adjusted OR=1.02, 95% CI: 0.94-1.09),^8^ and Shekhar et al. (EMS volume, USA).^9^

A striking gap in this literature is the absence of data from cultures where 13 carries no superstitious significance. All existing studies were conducted in Western nations with Christian cultural heritage, where triskaidekaphobia---fear of the number 13---is deeply embedded in social practices: buildings skip the 13th floor, airlines omit row 13, and hospitals avoid room 13.^10^ This shared cultural substrate makes it impossible to distinguish a genuine calendrical effect from a culturally mediated behavioral response.

Japan offers a compelling natural experiment. Japanese superstition centers on the numbers 4 (*shi*, homophonous with death) and 9 (*ku*, homophonous with suffering), not 13.^11^ The asymmetry is concrete and observable: hotels and hospitals in Japan routinely skip floor 4 and room numbers containing 4, whereas the custom of omitting the 13th floor found in some Western contexts is not established in Japan.^11,12^ Elevator panels in Japanese buildings commonly omit 4F, and airlines skip row 4; no comparable convention exists for the number 13. While younger generations may be aware of the "Friday the 13th" horror film franchise, awareness of a foreign superstition is categorically different from holding a belief that alters behavior---a distinction that Phillips et al. demonstrated matters in their landmark study of mortality patterns among Chinese Americans on the 4th day of the month.^12^ Crucially, the behavioral pathway requires not merely knowledge of a superstition but internalization sufficient to produce anxiety, avoidance, or altered risk-taking---a threshold that pop-cultural familiarity with a foreign film franchise is unlikely to reach.

Phillips et al.'s study provides the closest methodological precedent for our approach.^12^ They found that Chinese and Japanese Americans, for whom the number 4 carries death-related associations, showed a peak in cardiac mortality on the 4th of the month (RR=1.13, 95% CI: 1.06-1.21), while White Americans showed no such pattern. Their design leveraged cultural variation within a single country to isolate belief-mediated effects. We extend this logic across countries: if the Friday the 13th effect is culturally mediated, it should be absent in Japan, where 13 carries no stigma.

We analyzed Japanese national police traffic accident records (2019-2024; approximately 1.9 million accidents) using the same analytical methods employed by previous Western studies, enabling direct cross-cultural comparison of effect estimates obtained through identical methodologies.

## Methods

### Data sources

Traffic accident data were obtained from the National Police Agency (NPA) of Japan open data portal, comprising individual accident records for 2019-2024. The dataset contains 1,884,793 records with date/time of occurrence, prefecture-level location, accident severity (fatal or injury), vehicle types involved, driver age, and time of day (daytime or nighttime). Records were aggregated to national daily counts (for the Scanlon, Näyhä, Lo, case-crossover, and subgroup analyses) and to 47 prefecture × daily counts (for the panel-model covariate adjustment); no records were excluded, as the NPA dataset contains validated police records with no missing date fields. Weather data were obtained from the Japan Meteorological Agency (JMA) via daily cloud cover, precipitation, snowfall, and maximum snow depth series for 51 JMA prefectural stations (Hokkaido represented by 5 stations aggregated to the prefecture mean). Weather covariates were linked to each prefecture-day cell for the panel model; the national-level analyses used the corresponding national daily means. After daily aggregation, missing rates in the weather covariates were negligible (precipitation: 15 of 111,792 station-days = 0.013 %; snowfall: 0; maximum snow depth: 1).

### Study design

We identified 10 Friday the 13th dates during the study period (September 2019 through December 2024) and compared daily accident counts against control Fridays using multiple analytical frameworks. To maximize comparability with prior literature, we reproduced three established approaches alongside two original analyses.

**Scanlon method (paired comparison):** Following Scanlon et al.,^1^ we compared each Friday the 13th with the Friday the 6th of the same month using a paired t-test, with the Wilcoxon signed-rank test as a non-parametric robustness check. Normality of paired differences was confirmed by the Shapiro-Wilk test (W=0.97, p=0.91).

**Näyhä method (negative binomial regression):** Following Näyhä,^2^ we fitted a negative binomial regression model with Friday the 13th as a binary predictor, controlling for seasonal trends (harmonic terms for month), year, and cloud cover. The negative binomial model was selected over the Poisson model based on evidence of substantial overdispersion (Pearson chi-squared/df=20.8; Poisson AIC=9,660 vs. negative binomial AIC=4,953). As sex was not available in the NPA dataset, we performed age-stratified rather than sex-stratified analyses, using four groups: young (<=24 years), middle-lower (25-44), middle-upper (45-64), and elderly (>=65).

**Lo method (multi-date ANOVA):** Following Lo et al.,^7^ we compared accident counts across Fridays falling on the 6th, 13th, 20th, and 27th of each month using one-way ANOVA and the Kruskal-Wallis test, with post-hoc pairwise comparisons.

**Case-crossover analysis (three tests, all date-level):** Each Friday the 13th served as the case day, with the same-month other Fridays serving as controls (10 strata × 4 Fridays each = 40 case-control observations; every Fri13-containing month contained exactly one Fri13 and three other Fridays). Three complementary tests were run on the resulting pairs:

- *Month-stratified conditional Poisson regression (primary case-crossover reporting).* Following the case-crossover-as-conditional-Poisson framing,^13,14^ we eliminated the 10 stratum intercepts by conditioning on the stratum totals and maximized the resulting conditional likelihood in the Friday-the-13th log-count-ratio via Newton-Raphson. With G=10 clusters, the Cameron & Miller^15^ finite-cluster correction factor G/(G-1) = 1.111 was applied to the cluster-by-stratum sandwich SE, and inference was reported using both the z(0.975) = 1.96 and the t(G-1) = 2.262 critical values, with t(G-1) as the primary reporting. Fisher information (iid) SE is retained in the machine-readable JSON for audit but is not reported in the manuscript, because Poisson equidispersion is violated at α~0.02 (see model diagnostics below) and would produce a misleadingly tight CI.
- *Exact sign test.* The two-sided binomial exact test against p = 0.5 was computed on the 10 case-control differences (ties excluded from the denominator).
- *Sign-flip paired log-ratio permutation test.* For each stratum we computed log(fri13_count / mean(other Fridays)) and permuted the 10 signs; the 2^10 = 1024 sign patterns were fully enumerated for an exact p-value and cross-checked against 10,000 Monte-Carlo iterations (seed 20260723).^16^

**Covariate-adjusted negative binomial panel model:** We extended the Näyhä model to a 47-prefecture × daily panel with prefecture fixed effects, year/month/weekday fixed effects, and covariate adjustment for cloud cover, precipitation, snowfall, maximum snow depth, and three holiday indicators (national holiday, Obon, New Year). The variance was modeled as NB2, and the dispersion parameter α was estimated jointly by maximum likelihood (α_NB2 ≈ 0.023 for the primary specification; NB1 parameterization gave α_NB1 ≈ 0.45 as expected under the reparameterization identity var = μ(1+α) vs. var = μ + αμ²). Standard errors were reported as two-way (prefecture, date) cluster-robust to accommodate day-level treatment (Bertrand-Duflo-Mullainathan concern for underestimated SEs under common-shock treatments). A 51-police-bureau panel (with the 5 Hokkaido bureaus retained separately) was fitted as a sensitivity check.

**Prefecture-level heterogeneity (Figure S3).** To display the between-prefecture distribution of the Fri13 effect underlying the panel-model estimand, we additionally fitted the same mean-model specification separately to each of the 47 prefecture subsets (weather + holiday adjustment retained; prefecture fixed effect dropped as degenerate within each single-prefecture subset). HC1 heteroscedasticity-robust standard errors were used because within a single-prefecture subset each date has exactly one observation, causing a nominal cluster-on-date to reduce to HC0 with a small finite-sample scaling; HC1 is the honest label. Weather covariates that were pairwise perfectly collinear within a prefecture (|corr| ≥ 0.999; snowfall vs. maximum snow depth in 2 prefectures with 1-2 snow days) or zero-variance (6 prefectures with no snow) were dropped for those prefectures only. All 47 prefectures converged.

**Model diagnostics (Phase 2C-C1).** For the primary panel specification we report (i) the MLE-estimated NB2 and NB1 dispersion parameters, (ii) Pearson residual summary statistics (mean, SD, and tail proportions |r| > 2 and |r| > 3, benchmarked against the standard-normal expectation of 4.55 % and 0.27 %) and their visualization in Figure S1, (iii) a quasi-Poisson fit with Pearson χ²/df scale factor as a companion overdispersion check, (iv) HC1 heteroscedasticity-robust standard errors alongside the primary two-way cluster SE, and (v) a seasonality-specification sensitivity comparing dummy month FE, third-order harmonic terms (sin/cos of 2πk·doy/365.25 for k = 1…3), and a cubic B-spline of day-of-year. Because the 47-cluster count on the prefecture axis was less than the number of covariates and the two-way cluster meat matrix was rank-deficient on that axis, we complemented the z-based cluster inference with a Cameron-Miller pair cluster bootstrap on the prefecture axis (500 iterations, seed 20260723, zero convergence failures). The bootstrap resamples only the prefecture axis, so its CI under-covers the date-cluster variance and is reported as a prefecture-cluster misspecification sensitivity check rather than as an independent inference.

### Subgroup and sensitivity analyses

Exploratory subgroup analyses (Table 4) examined 8 pre-specified subgroups: severity (fatal, injury) × 2, age (young ≤ 24, mid-lower 25-44, mid-upper 45-64, elderly ≥ 65) × 4, and time of day (daytime, nighttime) × 2. Each subgroup was fitted with the same national-level NB2 model (year, month, weekday, and holiday controls) for comparability across rows. Bonferroni correction was applied family-wise across the 8 subgroups (adjusted significance threshold: α = 0.05/8 = 0.00625). Sensitivity analyses excluded: (1) the COVID-19 pandemic year (2020), (2) Obon and New Year holidays, (3) all national holidays, and (4) both COVID-19 year and holidays simultaneously.

### Potential biases

As an ecological study using police-recorded data, potential biases include differential accident reporting across days and ascertainment bias from changes in policing patterns. These were partially addressed through the case-crossover design (same-month controls) and sensitivity analyses excluding holidays and the COVID-19 period, which represent the primary sources of systematic variation in reporting.

### Power analysis

As the number of Friday the 13ths was fixed by the calendar, we performed a post-hoc sensitivity analysis of statistical power. With 10 Friday the 13ths and 303 other Fridays, the minimum detectable difference at 80% power and alpha=0.05 was 160.5 accidents per day (16.2% of the control mean). Effects of the magnitude reported by Scanlon (+52%) or Näyhä (+63%) would be detectable, but the observed effect (+3.9%) fell well below the detection threshold.

### Ethical considerations

This study analyzed publicly available, anonymized accident-level records released by the National Police Agency of Japan through its open data portal. The records contain no personal identifiers, and all analyses were performed on daily aggregate counts derived from these records. Under the Japanese Ethical Guidelines for Medical and Biological Research Involving Human Subjects (2021 revision), research using publicly available data that do not include personal identifiers does not require ethics committee review (Article 3, Paragraph 1, Item 1). Accordingly, no institutional review board approval or waiver was sought. This study was conducted in accordance with the principles of the Declaration of Helsinki where applicable to research using anonymized public data.

### Statistical software

All analyses were performed using Python 3.14.3 with pandas 3.0.1, scipy 1.18.0, numpy 2.4.2, statsmodels 0.14.6, patsy 1.0.2, matplotlib 3.10.8, and pyarrow 25.0.0. All statistical tests were two-sided with a significance level of α = 0.05. Full regression model coefficients, per-prefecture fit results, model-diagnostic JSON exports, and reproducibility code are available at https://github.com/rehabilitation-collaboration/friday13th.

## Results

### Descriptive statistics

During 2019-2024, Japan experienced 10 Friday the 13ths, with daily accident counts ranging from 713 (August 13, 2021, during Obon holiday) to 1,343 (December 13, 2019). The mean daily count on Friday the 13ths was 1,026.9 (standard deviation [SD]=171.6), compared with 988.6 (SD=178.6) on other Fridays, yielding a crude rate ratio of 1.04 (Figure 1).

### Reproduction of Western analytical methods

**Scanlon method:** All 10 Friday the 13th / Friday the 6th pairs from the same month were available for paired comparison. The mean difference was +44.0 accidents per day in favor of Friday the 13th (Friday 13th: 1,026.9 vs. Friday 6th: 982.9; rate ratio=1.04). Neither the paired t-test (t=0.75, p=0.47) nor the Wilcoxon signed-rank test (W=20, p=0.49) reached significance. For comparison, Scanlon et al. reported 65 versus 45 admissions (rate ratio=1.44, p<0.05) from a far smaller sample.^1^

**Näyhä method:** The negative binomial regression (AIC=4,953) yielded a count ratio of 1.01 (95% CI: 0.54-1.91, p=0.97) for the Friday the 13th indicator. Because we modeled raw daily accident counts without a population exposure offset, this estimate is expressed as a count ratio rather than a true incidence rate ratio; the two are numerically equivalent when the underlying population at risk is effectively constant across Fridays within the study period. Age-stratified models showed uniformly null results: young count ratio=0.99, middle-lower=0.99, middle-upper=1.03, elderly=1.01 (all p>0.90). For comparison, Näyhä reported IRR=1.63 for Finnish women and 1.02 for men.^2^ Formal residual diagnostics for the panel version of this model (dispersion parameter, Pearson residuals, quasi-Poisson comparison, and rank-deficient CRVE mitigation) are reported for the primary panel specification in the Model diagnostics paragraph below and in Supplementary Figure S1.

**Lo method:** One-way ANOVA across the four Friday groups (6th, 13th, 20th, 27th; n=10 each, verified from data) found no significant differences (F=0.16, p=0.93; Kruskal-Wallis H=0.35, p=0.95). Mean daily counts were 982.9, 1,026.9, 1,012.4, and 977.3, respectively. Post-hoc comparisons of the 13th against each control day were all non-significant (all p>0.50). Lo et al. similarly found no overall increase in ED visits but reported an isolated increase in penetrating trauma (OR=1.65, 95% CI: 1.04-2.61).^7^

### Original analyses

**Case-crossover (three date-level tests, Fri13 vs. same-month other Fridays):** All 10 Fri13-containing months provided one Fri13 and three matched other Fridays (n = 40 case-control observations). The month-stratified conditional Poisson MLE gave a count ratio of 1.04, with the small-cluster Cameron & Miller correction yielding a sandwich-t(G-1) 95% CI of [0.95, 1.14] (p = 0.40); the corresponding sandwich-z inference was [0.96, 1.12] (p = 0.38). The exact sign test on 10 same-month pairs gave 8 higher-than-control and 2 lower-than-control (ties = 0), for a two-sided binomial exact p = 0.11; individual case-to-control ratios ranged from 0.75 (August 2021, Obon period) to 1.20 (January 2023). The sign-flip paired log-ratio permutation test on the 2^10 = 1024 sign patterns gave an exact two-sided p = 0.45 (458 extreme patterns of 1024; geometric count ratio 1.04); the Monte-Carlo estimate at 10,000 iterations agreed at p = 0.45 (MC SE = 0.005). All three case-crossover tests are consistent with the null, and the arithmetic-mean summary statistic used in earlier drafts (mean ratio 1.05, t = 1.05, p = 0.32) is not comparable to the geometric-mean estimand used here (see Table 1 note).

**Covariate-adjusted negative binomial panel model (primary):** The 47-prefecture × daily panel model with weather, holiday, cloud-cover, precipitation, snowfall, and maximum-snow-depth adjustments, plus year/month/weekday fixed effects, yielded a Friday-the-13th count ratio of 1.02 (95% CI: 0.97-1.08, two-way (prefecture, date) cluster-robust p = 0.36; n = 103,008 prefecture-days). The 51-police-bureau sensitivity fit agreed to four decimals (count ratio 1.03, 95% CI: 0.97-1.08, p = 0.35). The Cameron-Miller pair cluster bootstrap on the prefecture axis gave a bootstrap 95% CI of [0.99, 1.05] with two-sided p = 0.18; because it does not resample the date-clustered variance, its narrower CI is a prefecture-cluster misspecification sensitivity check, not a tighter primary estimate.

**Model diagnostics (primary panel):** The NB2 MLE dispersion parameter was α = 0.023 (NB1 gave α = 0.45; the log-count-ratio point estimate was invariant across parameterizations at |Δ| = 0.003, well below the 0.01 spec-robustness threshold). Pearson residuals had mean +0.000 and SD 1.01, with 4.4% exceeding |r| > 2 (versus 4.55% expected under N(0,1)) and 0.69% exceeding |r| > 3 (versus 0.27% expected) — a mild fat tail consistent with a small number of extreme-event days that count regression cannot fully absorb (Figure S1). A quasi-Poisson fit gave the same point estimate to four decimals with a Pearson χ²/df scale factor of 1.44, comparable to the NB2 α = 0.023 dispersion estimate. HC1 heteroscedasticity-robust SE (0.015) was about 56% of the two-way cluster SE (0.027), as expected under day-level common shocks. Replacing the month fixed effects with a third-order harmonic seasonality shifted the count ratio by ≤ 0.001; a cubic B-spline of day-of-year was rank-deficient against the intercept (B-spline partition-of-unity artifact) and is not reported.

### Subgroup analyses (Table 4)

The 8 pre-specified subgroups (severity ×2, age ×4, time-of-day ×2) all failed to reject the null at the family-wise Bonferroni threshold of α = 0.05/8 = 0.00625. The fatal-accident row—which appeared nominally significant at p = 0.013 in earlier drafts that compared Fri13 against all non-Fri13 days—gave a raw two-sided Welch p = 0.09 (Bonferroni-adjusted p = 0.70) once restricted to the Friday-vs-Friday comparison used throughout this manuscript (mean 9.9 vs. 7.5 fatal accidents per Friday). The covariate-adjusted NB fit for the fatal subgroup did not converge (MLE optimizer failure at α → 0 on the sparse Fri13 fatal counts, mean ~9.9/day); we report the Poisson approximation as an approximate NB-adjusted count ratio of 1.23 (95% CI: 1.00-1.51, p = 0.05) and treat this row as approximate (see Table 4 footnote †). Nighttime accidents gave a crude rate ratio of 1.27 (Welch raw p = 0.14, NB-adjusted count ratio 1.07, p = 0.25); daytime gave 0.95 (Welch raw p = 0.38, NB-adjusted 0.96, p = 0.37). No age group showed a significant effect (all raw p > 0.28, all Bonferroni p = 1.00). None of the 8 subgroups survived Bonferroni correction, consistent with the null-everywhere pattern seen in the primary and case-crossover analyses.

### Prefecture-level heterogeneity (Figure S3)

Fitting the primary weather+holiday-adjusted NB2 model separately to each of the 47 prefectures (all converged after collinear snow-covariate handling for Ehime and Okayama) produced Friday-the-13th count ratios ranging from 0.59 [95% CI: 0.32, 1.09] in Tottori to 1.29 [0.99, 1.67] in Iwate, with a median of 1.01. Five prefectures had 95% confidence intervals excluding 1.0 at the nominal α = 0.05 level (11%, versus 2.25 expected under the null). The one-sided binomial test for an excess above the α = 0.05 expectation gave p = 0.08, consistent with the null. Under a family-wise Bonferroni correction across the 47 prefectures (α_family = 0.05, per-test threshold = 0.001) only Mie prefecture remained significant; the Benjamini-Hochberg false-discovery-rate procedure at q = 0.05 also retained only Mie. The 47-prefecture forest plot (Figure S3) shows this null-compatible spread centered on 1.0 rather than a systematic shift.

### Sensitivity analyses

Results were robust across all exclusion scenarios (Table 2). Excluding COVID-19 data (2020) reduced the sample to 8 Friday the 13ths and yielded RR=1.02 (p=0.70). Excluding Obon and New Year periods removed one Friday the 13th (August 2021) and produced RR=1.06 (p=0.26). Excluding all holidays shifted the comparison toward the null (RR=1.02, p=0.67). The most conservative analysis---excluding both COVID-19 data and holidays---produced RR=1.01 (p=0.90), confirming the null finding.

### Cross-national comparison

Table 3 and Figure 2 present a structured comparison of our results with prior studies. A consistent pattern emerges: the two earliest and smallest studies (Scanlon 1993, n=110; Näyhä 2002, n=41 female deaths) reported significant effects, while all subsequent larger studies found null results regardless of the cultural setting. Importantly, our Japanese data---from a culture with no fear of 13---produced effect estimates (RR=1.01-1.04) that are virtually identical to those from recent Western studies (Radun 2004, Schuld 2011, Ranganathan 2024), suggesting that the early positive findings may have reflected small-sample variability rather than a genuine cultural effect.

## Discussion

In the largest study to date examining Friday the 13th and traffic accidents, and the first conducted in a non-Western cultural context, we found no evidence that Friday the 13th increases accident risk in Japan. This null finding was consistent across five distinct analytical approaches, including three methods that had previously detected effects in Western populations.

### Interpretation in cultural context

Our results are consistent with two non-mutually exclusive interpretations. First, the "cultural mediation hypothesis" holds that superstition-related behavioral changes (e.g., heightened anxiety, altered driving patterns, avoidance behavior) occur only in populations that hold the relevant belief. Under this interpretation, Japan's null result reflects the absence of triskaidekaphobia in Japanese culture, paralleling Phillips et al.'s finding that mortality peaks on the 4th of the month occurred only among Chinese and Japanese Americans for whom 4 symbolizes death.^12^ Importantly, our design measures aggregate accident counts, not individual triskaidekaphobia, cognitions, or driving behavior; the cultural-mediation interpretation is therefore supportive rather than a direct test of belief-mediated behavior.

Second, the "null everywhere hypothesis" suggests that the original Western findings were artifacts of small samples and publication bias, and that Friday the 13th has no genuine effect in any population. This interpretation is supported by the pattern in Table 3: the only significant findings came from the two earliest and smallest studies, while all subsequent larger investigations---including those in Western countries with strong triskaidekaphobia---found null results.

On balance, the available evidence tilts toward the null-everywhere interpretation. The pattern in Table 3 is telling: significant results appeared only in the two smallest, earliest studies, while every subsequent investigation with adequate sample size---regardless of cultural context---has found null results. Even if minor behavioral changes do occur among superstitious individuals (e.g., slightly more cautious driving, or avoidance of travel), these effects appear too small to detectably alter population-level accident rates in any country studied to date. Our power analysis indicates that we could detect effects of 16% or larger---well below Scanlon's reported 52%---but not the 4% elevation we actually observed. Accordingly, our data exclude large effects but cannot rule out small ones.

### The fatal accident signal

The fatal-accident row deserves comment because earlier drafts of this analysis reported it as nominally significant at p = 0.013 when Fri13 fatal counts were compared against all non-Fri13 days. Once the comparison is restricted to Friday-vs-Friday—the design used throughout this manuscript—the raw Welch two-sided p is 0.09, and the family-wise Bonferroni-adjusted p across the 8 pre-specified subgroups is 0.70 (Table 4). Because the covariate-adjusted NB2 MLE did not converge on the sparse Fri13 fatal counts (mean 9.9 accidents per Friday), the Poisson approximation shown in Table 4—count ratio 1.23 (95% CI: 1.00-1.51, p = 0.05)—is reported as a bracket rather than a confirmatory estimate. The apparent elevation is consistent with Poisson fluctuation in small counts: with a mean of only 7.5 fatal accidents per non-Fri13 Friday, random variation alone produces day-to-day swings of 30% or more with appreciable probability. We report it for transparency but consider it most likely a chance finding—precisely the type of result that, if published in isolation, could perpetuate the Friday the 13th myth. This echoes Lo et al.'s isolated penetrating trauma finding (OR = 1.65), which also likely reflected multiple testing.^7^

### Comparison with prior literature

Our systematic reproduction of Western analytical methods provides the strongest evidence to date that methodology is not the source of discrepant findings in this literature. When we applied Scanlon's paired comparison to Japanese data with approximately 100 times more accidents per day than Scanlon's original sample, the rate ratio was 1.04 versus Scanlon's 1.44. When we applied Näyhä's negative binomial model, our count ratio was 1.01 versus Näyhä's 1.63 for Finnish women. The convergence of our null results across all three reproduced methods—augmented by three complementary case-crossover tests (conditional Poisson p = 0.40, exact sign p = 0.11, sign-flip permutation p = 0.45) and a 47-prefecture forest plot centered on 1.01—together with the null results from recent Western studies using different methods, strongly suggests that the original positive findings were statistical flukes rather than genuine effects.

### Strengths and limitations

This study has several strengths: it is the first from a non-Western cultural context, it employs the largest sample in this literature (1.9 million accidents), it systematically reproduces prior methods for direct comparison, and it reports a comprehensive suite of sensitivity analyses.

Several limitations should be acknowledged. First, with only 10 Friday the 13ths, our power to detect small effects was limited (minimum detectable effect: 16.2%); effects smaller than approximately 10% cannot be excluded by our data, though such small effects would lack practical significance for public health or traffic safety policy. The effects reported by Scanlon (+52%) and Näyhä (+63%) would have been easily detectable. Second, cultural exposure to the number 13 through Western media (films, imported products) means that some Japanese individuals may hold mild triskaidekaphobic beliefs, though this is unlikely to approach the deep-seated cultural fear found in Western nations.^10^ Third, we analyzed raw accident counts rather than rates per vehicle-kilometer traveled, as daily traffic volume data were not available at the national level. However, because our primary comparisons are between Fridays (same day of week), systematic differences in traffic volume are minimized; the case-crossover design further controls for within-month temporal trends. The consistency of results across the covariate-adjusted panel model (which controls for holidays, weather, and seasonal patterns that affect traffic volume) provides additional reassurance, though residual confounding by unmeasured traffic volume cannot be fully excluded. Fourth, the study period includes the COVID-19 pandemic, which altered traffic patterns; however, sensitivity analyses excluding 2020 confirmed our findings. Fifth, the NPA dataset does not include driver sex, precluding direct replication of Näyhä's sex-stratified analysis. Sixth, the deviance-to-df ratios of 0.03 and 0.02 reported for the national-level GLM in earlier drafts—where α was fixed at 1.0—should be read as suggesting possible overcorrection under a fixed-α assumption rather than as unqualified evidence of fit adequacy; the primary panel specification here estimates α by maximum likelihood (α_NB2 ≈ 0.023), Pearson residuals have mean +0.000 and SD 1.01 with mild fat tails beyond |r| > 3 (Figure S1), and the quasi-Poisson comparison agrees to four decimals with a Pearson χ²/df scale factor of 1.44. With a 47-cluster count below the number of covariates on the prefecture axis, the two-way cluster meat matrix is rank-deficient on that axis; the Cameron-Miller pair cluster bootstrap on the prefecture axis (500 iterations) was used as a sensitivity check and also failed to reject the null, though it does not resample date-clustered variance and therefore under-covers that component. Seventh, as an ecological study, we cannot make individual-level causal inferences; the absence of a population-level effect does not preclude the possibility that a small subset of individuals alter their behavior on Friday the 13th.

### Conclusion

Friday the 13th was not associated with a detectable population-level increase in traffic accidents in Japan. When Western analytical methods are faithfully reproduced in a culture without triskaidekaphobia, no large effect emerges, although small effects cannot be excluded by our data. Although this pattern is consistent with a cultural-mediation hypothesis, the accumulated evidence---including null results from recent large Western studies---more strongly supports a universal null effect. Regardless of the underlying explanation, the practical implication is the same: the roads of Japan are no more dangerous on Friday the 13th than on any other Friday. Scanlon's advice to "stay at home" on Friday the 13th may be prudent counsel for the superstitious, but in Japan, there is no evidence-based reason to check the calendar before starting the car.

---

## References

1. Scanlon TJ, Luben RN, Scanlon FL, Singleton N. Is Friday the 13th bad for your health? *BMJ*. 1993;307(6919):1584-1586. doi:10.1136/bmj.307.6919.1584
2. Näyhä S. Traffic deaths and superstition on Friday the 13th. *Am J Psychiatry*. 2002;159(12):2110-2111. doi:10.1176/appi.ajp.159.12.2110
3. Radun I, Summala H. Females do not have more injury road accidents on Friday the 13th. *BMC Public Health*. 2004;4:54. doi:10.1186/1471-2458-4-54
4. Smith DF. Traffic accidents and Friday the 13th [letter]. *Am J Psychiatry*. 2004;161(11):2140. doi:10.1176/appi.ajp.161.11.2140-a
5. Centrum voor Verzekeringsstatistiek (CVS). Vrijdag de 13e [press release]. The Hague, Netherlands; 2008.
6. Schuld J, Slotta JE, Schuld S, et al. Popular belief meets surgical reality: impact of lunar phases, Friday the 13th and zodiac signs on emergency operations and intraoperative blood loss. *World J Surg*. 2011;35(9):1945-1949. doi:10.1007/s00268-011-1166-8
7. Lo BM, Visintainer CM, Best HA, Beydoun HA. Answering the myth: use of emergency services on Friday the 13th. *Am J Emerg Med*. 2012;30(6):886-889. doi:10.1016/j.ajem.2011.06.008
8. Ranganathan S, Riveros C, Geng M, et al. Superstition in surgery: a population-based cohort study to assess the association between surgery on Friday the 13th and postoperative outcomes. *Ann Surg Open*. 2024;5(1):e375. doi:10.1097/AS9.0000000000000375
9. Shekhar AC, McCartin M, Kimbrell J, Stebel J, Zhou A, Desman J, Carter J, Milekic B, Abbott E, Blumen IJ. Friday the 13th is not associated with increases in emergency medical services (EMS) patient volume. *Am J Emerg Med*. 2025;92:245-247. doi:10.1016/j.ajem.2025.03.001
10. Vyse SA. *Believing in Magic: The Psychology of Superstition*. Updated ed. New York: Oxford University Press; 2014.
11. Davies RJ, Ikeno O. *The Japanese Mind: Understanding Contemporary Japanese Culture*. Tokyo: Tuttle Publishing; 2002.
12. Phillips DP, Liu GC, Kwok K, Jarvinen JR, Zhang W, Abramson IS. The Hound of the Baskervilles effect: natural experiment on the influence of psychological stress on timing of death. *BMJ*. 2001;323(7327):1443-1446. doi:10.1136/bmj.323.7327.1443
13. Maclure M. The case-crossover design: a method for studying transient effects on the risk of acute events. *Am J Epidemiol*. 1991;133(2):144-153. doi:10.1093/oxfordjournals.aje.a115853
14. Lu Y, Zeger SL. On the equivalence of case-crossover and time series methods in environmental epidemiology. *Biostatistics*. 2007;8(2):337-344. doi:10.1093/biostatistics/kxl013
15. Cameron AC, Miller DL. A practitioner's guide to cluster-robust inference. *J Human Resources*. 2015;50(2):317-372. doi:10.3368/jhr.50.2.317
16. Pesarin F, Salmaso L. *Permutation Tests for Complex Data: Theory, Applications and Software*. Chichester, UK: John Wiley & Sons; 2010.

---

## Acknowledgments

Data analysis and manuscript preparation were assisted by Claude Opus 4.6 (Anthropic), which was used for statistical programming, literature search, and drafting. The author assumes full responsibility for the accuracy of the content, interpretation, and conclusions. All references were verified against PubMed and CrossRef records where applicable.

## Author Contributions (CRediT)

Mizuki Shirai: Conceptualization, Methodology, Investigation, Data Curation, Formal Analysis, Writing - Original Draft, Writing - Review & Editing, Visualization, Project Administration.

## Conflict of Interest

The author declares no conflicts of interest per ICMJE guidelines.

## Funding

This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

## Data Availability

Traffic accident data are publicly available from the National Police Agency of Japan open data portal (https://www.npa.go.jp/publications/statistics/koutsuu/opendata/index_opendata.html). Weather data are from the Japan Meteorological Agency (https://www.jma.go.jp/). Analysis code is available at https://github.com/rehabilitation-collaboration/friday13th.

---

## Tables

### Table 1. Daily accident counts on Friday the 13th versus same-month other Fridays

| Friday the 13th | Accidents | Same-month other Fridays (mean) | Ratio |
|-----------------|-----------|--------------------------------|-------|
| 2019-09-13 | 1,110 | 1,249 | 0.89 |
| 2019-12-13 | 1,343 | 1,263 | 1.06 |
| 2020-03-13 | 960 | 937 | 1.02 |
| 2020-11-13 | 1,178 | 1,052 | 1.12 |
| 2021-08-13 | 713 | 946 | 0.75 |
| 2022-05-13 | 1,022 | 905 | 1.13 |
| 2023-01-13 | 1,022 | 852 | 1.20 |
| 2023-10-13 | 1,081 | 1,075 | 1.01 |
| 2024-09-13 | 977 | 896 | 1.09 |
| 2024-12-13 | 863 | 733 | 1.18 |
| **Mean (arithmetic per-pair ratio)** | **1,026.9** | **990.9** | **1.05** |
| **Geometric-mean count ratio (case-crossover permutation)** | — | — | **1.04** |

*"Same-month other Fridays" refers to the arithmetic mean of all Fridays in the same calendar month excluding the Friday the 13th itself (typically Fri 6, 20, and 27). This within-month control set differs from the "all other Fridays" comparison used in the Results text and Table 2, which pools all 303 non-13th Fridays across the study period. The bolded "Mean (arithmetic per-pair ratio)" row is the average of the ten per-pair case-to-control ratios reported in the "Ratio" column and matches the arithmetic mean quoted in the abstract; the "Geometric-mean count ratio" row is exp(mean of the ten log-ratios), which is the estimand of the sign-flip permutation and conditional-Poisson case-crossover tests reported in the Methods and Results. The two are numerically close because the per-pair ratios sit near 1, but they answer slightly different statistical questions and are not interchangeable in downstream inference.*

### Table 2. Sensitivity analyses

| Scenario | n(Fri 13th) | n(Other Fri) | Mean Fri 13th | Mean Other | RR (95% CI) | p-value |
|----------|-------------|--------------|---------------|------------|-------------|---------|
| All data | 10 | 303 | 1,026.9 | 988.6 | 1.04 (0.93-1.15) | 0.50 |
| Excl. COVID (2020) | 8 | 253 | 1,016.4 | 992.0 | 1.02 (0.90-1.16) | 0.70 |
| Excl. Obon & New Year | 9 | 295 | 1,061.8 | 997.9 | 1.06 (0.97-1.16) | 0.26 |
| Excl. holidays | 10 | 283 | 1,026.9 | 1,004.7 | 1.02 (0.92-1.14) | 0.67 |
| Excl. COVID + holidays | 8 | 235 | 1,016.4 | 1,009.0 | 1.01 (0.89-1.14) | 0.90 |

*RR and p-values in this table are from independent two-sample t-tests comparing Friday the 13th against all other Fridays within each scenario, in contrast to the Scanlon paired t-test (p=0.47) reported in the Results text.*

### Table 3. Cross-national comparison of Friday the 13th studies

| Country | Study | Period | N | Outcome | Design | Effect (RR/OR) | Significant | Cultural fear of 13 |
|---------|-------|--------|---|---------|--------|----------------|-------------|-------------------|
| UK | Scanlon 1993 | multiple years | 110 | Hospital admissions | Paired | 1.44 | Yes | Strong |
| Finland | Näyhä 2002 | 1971-1997 | 41 (women) | Traffic fatalities | NegBin | Women 1.63 / Men 1.02 | Women only | Moderate |
| Finland | Radun 2004 | 1989-2002 | 21 Fri 13ths | Injury accidents | Matched | ~1.0 | No | Moderate |
| Netherlands | CVS 2008 | ~2 years | 7,500/day | Insurance claims | Descriptive | 0.96 | No | Moderate |
| Germany | Schuld 2011 | 2001-2010 | 27,914 | Surgical outcomes | Retrospective | ~1.0 | No | Strong |
| USA | Lo 2012 | 8 years | 49,094 | ED visits | Multi-control | <1.0 (penetrating 1.65) | Penetrating only | Strong |
| Canada | Ranganathan 2024 | 2007-2019 | 19,747 | Surgical outcomes | Population cohort | 1.02 | No | Strong |
| USA | Shekhar 2025 | N/A | N/A | EMS volume | Letter | ~1.0 | No | Strong |
| **Japan** | **Present study** | **2019-2024** | **1,884,793** | **Traffic accidents** | **Multiple** | **1.01-1.04** | **No** | **Absent** |

*RR = rate ratio; OR = odds ratio; NegBin = negative binomial regression; ED = emergency department; EMS = emergency medical services. N refers to total events analyzed except where noted (e.g., "21 Fri13s" = number of Friday the 13th dates, "41 (women)" = number of female traffic deaths). Effect estimates are RR unless otherwise specified. "not confirmed" indicates values not accessible from the original publication. The "Cultural fear of 13" classification is a qualitative categorization based on prior cultural and ethnographic descriptions; it is intended to be interpreted descriptively rather than as a validated psychometric measure.*

### Table 4. Subgroup analyses: Friday the 13th vs. same-month other Fridays

| Subgroup | Mean Fri13 | Mean other Fri | Crude RR | Raw p (Welch) | Bonferroni p (×8) | NB-adjusted count ratio [95% CI] | NB p |
|----------|-----------|----------------|----------|---------------|-------------------|----------------------------------|------|
| Fatal accidents | 9.90 | 7.57 | 1.307 | 0.087 | 0.696 | 1.227 [1.000, 1.506] † | 0.050 |
| Injury accidents | 1,017.0 | 981.0 | 1.037 | 0.528 | 1.000 | 0.991 [0.914, 1.075] | 0.833 |
| Age ≤ 24 (young) | 114.2 | 112.6 | 1.014 | 0.786 | 1.000 | 0.990 [0.905, 1.083] | 0.820 |
| Age 25-44 (mid-lower) | 317.9 | 314.0 | 1.012 | 0.854 | 1.000 | 0.973 [0.891, 1.063] | 0.543 |
| Age 45-64 (mid-upper) | 364.8 | 344.3 | 1.059 | 0.284 | 1.000 | 1.018 [0.937, 1.107] | 0.674 |
| Age ≥ 65 (elderly) | 229.8 | 217.5 | 1.057 | 0.509 | 1.000 | 0.980 [0.888, 1.082] | 0.694 |
| Daytime | 687.1 | 720.4 | 0.954 | 0.380 | 1.000 | 0.962 [0.884, 1.047] | 0.366 |
| Nighttime | 339.8 | 268.2 | 1.267 | 0.142 | 1.000 | 1.065 [0.958, 1.183] | 0.247 |

*Family-wise Bonferroni threshold across the 8 pre-specified subgroups: α = 0.05 / 8 = 0.00625. Raw p is the Welch (unequal-variance) two-sided t-test of Fri13 daily counts vs. all other Friday daily counts (n = 10 vs. 303). "NB-adjusted count ratio" is exp(coefficient on `is_friday13th`) from a national-level NB2 model with year, month, weekday, and holiday-flag controls; α (dispersion) was estimated jointly by maximum likelihood. † The fatal-accident NB2 MLE optimizer (both BFGS and Nelder-Mead) failed to converge on the sparse Fri13 fatal counts (mean 9.9/day); the reported value is a Poisson-GLM approximation, which is expected to under-cover the true variance and should be interpreted as an approximate bracket rather than an exact CI (per_subgroup detail in output/subgroup_table4_results.json). None of the 8 subgroups survives Bonferroni correction.*

### Figure Legends

**Figure 1.** Daily traffic accident counts on Friday the 13th (red points) compared with all other Fridays (gray points) during 2019-2024 in Japan. The dashed horizontal lines indicate group means. No systematic elevation is observed for Friday the 13th dates.

**Figure 2.** Cross-national forest plot of Friday the 13th effect estimates. Studies are ordered by publication year. Point estimates and 95% confidence intervals are shown where available. The vertical dashed line at RR=1.0 indicates no effect. Japan (present study) is highlighted with the largest sample size and a point estimate near unity.

### Supplementary Figure Legends

**Figure S1.** Pearson residual distribution for the primary weather+holiday-adjusted NB2 panel model (03_primary specification; n = 103,008 prefecture-days). Empirical mean = +0.000, SD = 1.01; 4.4% of residuals exceed |r| > 2 (vs. 4.55% expected under N(0,1)) and 0.69% exceed |r| > 3 (vs. 0.27% expected). The mild fat tail beyond ±3 is consistent with a small number of extreme-event days that count regression cannot fully absorb and does not indicate systematic misspecification for the is_fri13 estimand.

**Figure S2.** Same-month pair plot for the 10 Fri13-containing months of 2019-2024. Each connecting line represents one month (10 lines total); the left endpoint (red diamond) is the daily accident count on Friday the 13th and the right endpoint (blue circle) is the mean of the other Fridays in the same calendar month. Eight of ten pairs favor Fri13 > control (consistent with the exact sign test result n+ = 8, p = 0.11), including a visible downward outlier in August 2021 (Obon period). Data source: `output/case_crossover_results.json['pair_summary']['pairs']`.

**Figure S3.** Forest plot of Friday-the-13th count ratios for each of the 47 prefectures, sorted by point estimate. Each row shows the prefecture-specific NB2 count ratio and its HC1 heteroscedasticity-robust 95% confidence interval; the vertical dashed line at 1.0 indicates no effect. Ratios range from 0.59 [0.32, 1.09] (Tottori) to 1.29 [0.99, 1.67] (Iwate), with a median of 1.01. Five prefectures had 95% CIs excluding 1.0 at the nominal α = 0.05 level (11%, vs. 2.25 expected under the null; one-sided binomial excess-test p = 0.08). Under a family-wise Bonferroni correction only Mie prefecture remained significant; the Benjamini-Hochberg FDR procedure at q = 0.05 also retained only Mie. Ehime and Okayama required dropping the snow-depth covariate for those prefecture-specific fits (perfect collinearity with snowfall on their 1-2 snow days); all 47 prefectures converged. The overall distribution is centered on 1.0 rather than showing a systematic Friday-the-13th shift, consistent with the primary panel and case-crossover null-everywhere results.

# Friday the 13th Has No Bite in Japan: A Natural Cultural Control Study of 1.9 Million Traffic Accidents

**Running title:** Friday the 13th has no bite in Japan

## Authors

Mizuki Shirai, MHS^1^

^1^ Department of Rehabilitation, Reha3 Corporation, Saitama, Japan

**Corresponding author:** Mizuki Shirai, MHS, Department of Rehabilitation, Reha3 Corporation, Saitama, Japan. Email: reha-collab@manabu-lab.com. ORCID: 0009-0005-3615-0670.

---

## Abstract

**Background:** Evidence on whether Friday the 13th increases accident risk remains inconsistent and methodologically contested, with reported effects ranging from a 52% increase in hospital admissions to null findings. Japan, where the number 13 carries no cultural superstition, provides a natural control population to test whether the "Friday the 13th effect" is culturally mediated.

**Methods:** We analyzed nearly 1.9 million police-recorded traffic accidents (1,884,793 records) across Japan (2019-2024), comparing accident counts on 10 Friday the 13ths against other Fridays. To enable direct comparison with prior Western studies, we reproduced three established analytical approaches: the Scanlon paired comparison (Friday 13th vs. Friday 6th), the Näyhä negative binomial regression, and the Lo multi-date ANOVA method. We additionally performed case-crossover analysis with same-month Friday controls and covariate-adjusted negative binomial regression controlling for weather, holidays, and seasonal trends. Subgroup analyses examined accident severity, age groups, and time of day.

**Results:** Across all analytical approaches, no significant Friday the 13th effect was detected. The Scanlon-method rate ratio was 1.04 (paired t-test p=0.47), the Näyhä-method incidence rate ratio was 1.01 (95% CI: 0.54-1.91, p=0.97), and the Lo-method ANOVA showed no between-group differences (F=0.16, p=0.93). The case-crossover analysis found a mean ratio of 1.05 (p=0.32), with 8 of 10 Friday the 13ths showing marginally higher counts but none reaching statistical significance. Covariate-adjusted negative binomial regression confirmed the null finding (IRR=1.02, 95% CI: 0.54-1.94, p=0.95). Fatal accidents showed a nominally elevated rate ratio (1.31, p=0.013), but this finding was based on small counts (mean 9.9 vs. 7.5 fatal accidents per day) and did not survive consideration of multiple comparisons. All sensitivity analyses excluding COVID-period data, holidays, and Obon/New Year periods yielded consistent null results (RR range: 1.01-1.06).

**Conclusions:** In a country where 13 is not a culturally feared number, Friday the 13th is not associated with increased traffic accidents. When the same analytical methods that previously detected effects in Western populations are applied to Japanese data, no effect emerges. These findings are consistent with the hypothesis that behavioral responses to superstitious dates are culturally mediated rather than reflecting an intrinsic calendrical risk, suggesting that Scanlon's classic advice to "stay at home" on Friday the 13th may apply only to those who believe they should.

**Keywords:** Friday the 13th, triskaidekaphobia, traffic accidents, superstition, cultural epidemiology, Japan, cross-national comparison

---

## Introduction

Is Friday the 13th truly unlucky? In 1993, Scanlon and colleagues published a now-classic study in the BMJ's Christmas issue reporting that hospital admissions from transport accidents in southwest England were 52% higher on Friday the 13th compared with Friday the 6th.^1^ The finding captured public imagination and has been widely cited, but subsequent research across Western nations has produced conflicting results.

Näyhä reported a 63% higher risk of traffic death among Finnish women on Friday the 13th (adjusted rate ratio 1.63), though men showed no effect;^2^ Radun and Summala directly contradicted this, finding no increase for either sex in Finnish injury accidents.^3^ Smith noted that Näyhä's analysis conflated date of death with date of accident---people who died on Friday the 13th may have been injured on a different day---potentially introducing survival bias.^4^ Dutch insurance data showed a 4% decrease.^5^ Subsequent larger studies have consistently found null results: Schuld et al. (n=27,914 surgical patients, Germany),^6^ Lo et al. (n=49,094 ED visits, USA; though penetrating trauma showed an isolated OR=1.65),^7^ Ranganathan et al. (n=19,747 surgical patients, Canada; adjusted OR=1.02, 95% CI: 0.94-1.09),^8^ and Shekhar et al. (EMS volume, USA).^9^

A striking gap in this literature is the absence of data from cultures where 13 carries no superstitious significance. All existing studies were conducted in Western nations with Christian cultural heritage, where triskaidekaphobia---fear of the number 13---is deeply embedded in social practices: buildings skip the 13th floor, airlines omit row 13, and hospitals avoid room 13.^10^ This shared cultural substrate makes it impossible to distinguish a genuine calendrical effect from a culturally mediated behavioral response.

Japan offers a compelling natural experiment. Japanese superstition centers on the numbers 4 (*shi*, homophonous with death) and 9 (*ku*, homophonous with suffering), not 13.^11^ The asymmetry is concrete and observable: hotels and hospitals in Japan routinely skip floor 4 and room numbers containing 4, but floor 13 and room 13 are universally present.^11,12^ Elevator panels in Japanese buildings omit 4F but include 13F; airlines skip row 4 but not row 13. No Japanese equivalent of the Western custom of omitting the 13th floor exists. While younger generations may be aware of the "Friday the 13th" horror film franchise, awareness of a foreign superstition is categorically different from holding a belief that alters behavior---a distinction that Phillips et al. demonstrated matters in their landmark study of mortality patterns among Chinese Americans on the 4th day of the month.^12^ Crucially, the behavioral pathway requires not merely knowledge of a superstition but internalization sufficient to produce anxiety, avoidance, or altered risk-taking---a threshold that pop-cultural familiarity with a foreign film franchise is unlikely to reach.

Phillips et al.'s study provides the closest methodological precedent for our approach.^12^ They found that Chinese and Japanese Americans, for whom the number 4 carries death-related associations, showed a peak in cardiac mortality on the 4th of the month (RR=1.13, 95% CI: 1.06-1.21), while White Americans showed no such pattern. Their design leveraged cultural variation within a single country to isolate belief-mediated effects. We extend this logic across countries: if the Friday the 13th effect is culturally mediated, it should be absent in Japan, where 13 carries no stigma.

We analyzed Japanese national police traffic accident records (2019-2024; approximately 1.9 million accidents) using the same analytical methods employed by previous Western studies, enabling direct cross-cultural comparison of effect estimates obtained through identical methodologies.

## Methods

### Data sources

Traffic accident data were obtained from the National Police Agency (NPA) of Japan open data portal, comprising individual accident records for 2019-2024. The dataset contains 1,884,793 records with date/time of occurrence, location, accident severity (fatal or injury), vehicle types involved, driver age, and time of day (daytime or nighttime). Records were aggregated to daily counts without exclusions, as the NPA dataset contains validated police records with no missing date fields. Weather data (daily cloud cover) were obtained from Japan Meteorological Agency (JMA) observatory stations and linked to each accident via the nearest weather station. After aggregation to daily means, no missing values remained in the cloud cover variable for the Friday analysis subset (n=313 Fridays).

### Study design

We identified 10 Friday the 13th dates during the study period (September 2019 through December 2024) and compared daily accident counts against control Fridays using multiple analytical frameworks. To maximize comparability with prior literature, we reproduced three established approaches alongside two original analyses.

**Scanlon method (paired comparison):** Following Scanlon et al.,^1^ we compared each Friday the 13th with the Friday the 6th of the same month using a paired t-test, with the Wilcoxon signed-rank test as a non-parametric robustness check. Normality of paired differences was confirmed by the Shapiro-Wilk test (W=0.97, p=0.91).

**Näyhä method (negative binomial regression):** Following Näyhä,^2^ we fitted a negative binomial regression model with Friday the 13th as a binary predictor, controlling for seasonal trends (harmonic terms for month), year, and cloud cover. The negative binomial model was selected over the Poisson model based on evidence of substantial overdispersion (Pearson chi-squared/df=20.8; Poisson AIC=9,660 vs. negative binomial AIC=4,953). As sex was not available in the NPA dataset, we performed age-stratified rather than sex-stratified analyses, using four groups: young (<=24 years), middle-lower (25-44), middle-upper (45-64), and elderly (>=65).

**Lo method (multi-date ANOVA):** Following Lo et al.,^7^ we compared accident counts across Fridays falling on the 6th, 13th, 20th, and 27th of each month using one-way ANOVA and the Kruskal-Wallis test, with post-hoc pairwise comparisons.

**Case-crossover analysis:** Each Friday the 13th served as the case day, with all other Fridays in the same calendar month as control days (typically 3 controls per case). We calculated the ratio of case-day to mean control-day accidents for each stratum and tested the mean ratio against 1.0.

**Covariate-adjusted negative binomial regression:** We extended the Näyhä model by adding holiday status, Obon period (August 13-16), and New Year period (December 29-January 3) as additional covariates, restricted to Fridays only.

### Subgroup and sensitivity analyses

Exploratory subgroup analyses examined fatal versus injury accidents, age groups, and daytime versus nighttime. Bonferroni correction was applied to account for six subgroup comparisons (adjusted significance threshold: alpha=0.0083). Sensitivity analyses excluded: (1) the COVID-19 pandemic year (2020), (2) Obon and New Year holidays, (3) all national holidays, and (4) both COVID-19 year and holidays simultaneously.

### Potential biases

As an ecological study using police-recorded data, potential biases include differential accident reporting across days and ascertainment bias from changes in policing patterns. These were partially addressed through the case-crossover design (same-month controls) and sensitivity analyses excluding holidays and the COVID-19 period, which represent the primary sources of systematic variation in reporting.

### Power analysis

As the number of Friday the 13ths was fixed by the calendar, we performed a post-hoc sensitivity analysis of statistical power. With 10 Friday the 13ths and 303 other Fridays, the minimum detectable difference at 80% power and alpha=0.05 was 160.5 accidents per day (16.2% of the control mean). Effects of the magnitude reported by Scanlon (+52%) or Näyhä (+63%) would be detectable, but the observed effect (+3.9%) fell well below the detection threshold.

### Ethical considerations

This study used exclusively publicly available, fully aggregated population-level data from the National Police Agency of Japan open data portal. No individual-level data were accessed. Under the Japanese Ethical Guidelines for Medical and Biological Research Involving Human Subjects (2021 revision), research using publicly available aggregate statistics does not require ethics committee review (Article 3, Paragraph 1, Item 1). As no human subjects were involved, no institutional review board approval or waiver was sought. This study was conducted in accordance with the principles of the Declaration of Helsinki where applicable to research using aggregate data.

### Statistical software

All analyses were performed using Python 3.14 with pandas, scipy, and statsmodels. All statistical tests were two-sided with a significance level of alpha=0.05. Full regression model coefficients are available in the analysis code at https://github.com/rehabilitation-collaboration/friday13th.

## Results

### Descriptive statistics

During 2019-2024, Japan experienced 10 Friday the 13ths, with daily accident counts ranging from 713 (August 13, 2021, during Obon holiday) to 1,343 (December 13, 2019). The mean daily count on Friday the 13ths was 1,026.9 (standard deviation [SD]=171.6), compared with 988.6 (SD=178.6) on other Fridays, yielding a crude rate ratio of 1.04 (Figure 1).

### Reproduction of Western analytical methods

**Scanlon method:** All 10 Friday the 13th / Friday the 6th pairs from the same month were available for paired comparison. The mean difference was +44.0 accidents per day in favor of Friday the 13th (Friday 13th: 1,026.9 vs. Friday 6th: 982.9; rate ratio=1.04). Neither the paired t-test (t=0.75, p=0.47) nor the Wilcoxon signed-rank test (W=20, p=0.49) reached significance. For comparison, Scanlon et al. reported 65 versus 45 admissions (rate ratio=1.44, p<0.05) from a far smaller sample.^1^

**Näyhä method:** The negative binomial regression (AIC=4,953; deviance/df=0.03) yielded an incidence rate ratio of 1.01 (95% CI: 0.54-1.91, p=0.97) for the Friday the 13th indicator, indicating no effect. As we modeled raw daily counts without a population exposure offset, these ratios represent count ratios rather than true incidence rate ratios; however, because the underlying population at risk is effectively constant across Fridays within the study period, this distinction is immaterial. Age-stratified models showed uniformly null results: young IRR=0.99, middle-lower IRR=0.99, middle-upper IRR=1.03, elderly IRR=1.01 (all p>0.90). In contrast, Näyhä reported IRR=1.63 for Finnish women and 1.02 for men.^2^

**Lo method:** One-way ANOVA across the four Friday groups (6th, 13th, 20th, 27th; n=10 each, verified from data) found no significant differences (F=0.16, p=0.93; Kruskal-Wallis H=0.35, p=0.95). Mean daily counts were 982.9, 1,026.9, 1,012.4, and 977.3, respectively. Post-hoc comparisons of the 13th against each control day were all non-significant (all p>0.50). Lo et al. similarly found no overall increase in ED visits but reported an isolated increase in penetrating trauma (OR=1.65, 95% CI: 1.04-2.61).^7^

### Original analyses

**Case-crossover:** Of 10 Friday the 13ths, 8 showed higher accident counts than their same-month Friday controls, but the mean of individual case-to-control ratios was 1.05, which did not differ significantly from 1.0 (t=1.05, p=0.32). Individual ratios ranged from 0.75 (August 2021, Obon period) to 1.20 (January 2023).

**Covariate-adjusted negative binomial regression:** After adjusting for seasonal trends, year, cloud cover, holidays, Obon, and New Year periods, the Friday the 13th IRR was 1.02 (95% CI: 0.54-1.94, p=0.95; model AIC=4,956).

### Subgroup analyses

Fatal accidents showed a nominally significant elevation on Friday the 13th (total: 99 vs. 2,287; mean 9.9 vs. 7.5 per day; rate ratio=1.31, p=0.013). However, this finding must be interpreted with caution: the absolute counts were small (range: 4-18 fatal accidents per Friday the 13th), the result did not survive Bonferroni correction for the six subgroup comparisons performed, and the negative binomial regression controlling for covariates showed no significant fatal accident effect. Nighttime accidents showed a borderline elevation (rate ratio=1.27, p=0.07) that was offset by a non-significant daytime reduction (rate ratio=0.95, p=0.44). No age group showed a significant effect (all p>0.28).

### Sensitivity analyses

Results were robust across all exclusion scenarios (Table 2). Excluding COVID-19 data (2020) reduced the sample to 8 Friday the 13ths and yielded RR=1.02 (p=0.70). Excluding Obon and New Year periods removed one Friday the 13th (August 2021) and produced RR=1.06 (p=0.26). Excluding all holidays shifted the comparison toward the null (RR=1.02, p=0.67). The most conservative analysis---excluding both COVID-19 data and holidays---produced RR=1.01 (p=0.90), confirming the null finding.

### Cross-national comparison

Table 3 and Figure 2 present a systematic comparison of our results with all prior studies. A consistent pattern emerges: the two earliest and smallest studies (Scanlon 1993, n=110; Näyhä 2002, n=41 female deaths) reported significant effects, while all subsequent larger studies found null results regardless of the cultural setting. Importantly, our Japanese data---from a culture with no fear of 13---produced effect estimates (RR=1.01-1.04) that are virtually identical to those from recent Western studies (Radun 2004, Schuld 2011, Ranganathan 2024), suggesting that the early positive findings may have reflected small-sample variability rather than a genuine cultural effect.

## Discussion

In the largest study to date examining Friday the 13th and traffic accidents, and the first conducted in a non-Western cultural context, we found no evidence that Friday the 13th increases accident risk in Japan. This null finding was consistent across five distinct analytical approaches, including three methods that had previously detected effects in Western populations.

### Interpretation in cultural context

Our results are consistent with two non-mutually exclusive interpretations. First, the "cultural mediation hypothesis" holds that superstition-related behavioral changes (e.g., heightened anxiety, altered driving patterns, avoidance behavior) occur only in populations that hold the relevant belief. Under this interpretation, Japan's null result reflects the absence of triskaidekaphobia in Japanese culture, paralleling Phillips et al.'s finding that mortality peaks on the 4th of the month occurred only among Chinese and Japanese Americans for whom 4 symbolizes death.^12^

Second, the "null everywhere hypothesis" suggests that the original Western findings were artifacts of small samples and publication bias, and that Friday the 13th has no genuine effect in any population. This interpretation is supported by the pattern in Table 3: the only significant findings came from the two earliest and smallest studies, while all subsequent larger investigations---including those in Western countries with strong triskaidekaphobia---found null results.

On balance, the available evidence tilts toward the null-everywhere interpretation. The pattern in Table 3 is telling: significant results appeared only in the two smallest, earliest studies, while every subsequent investigation with adequate sample size---regardless of cultural context---has found null results. Even if minor behavioral changes do occur among superstitious individuals (e.g., slightly more cautious driving, or avoidance of travel), these effects appear too small to detectably alter population-level accident rates in any country studied to date. Our power analysis indicates that we could detect effects of 16% or larger---well below Scanlon's reported 52%---but not the 4% elevation we actually observed.

### The fatal accident signal

The nominally significant increase in fatal accidents (RR=1.31, p=0.013) warrants comment. With an average of only 7.5 fatal accidents per control Friday, this subgroup analysis was underpowered and susceptible to random variation. The finding did not survive multiple comparison correction, was not confirmed by the negative binomial model, and has no plausible mechanism in a population that does not fear the number 13. The apparent elevation is consistent with Poisson fluctuation in small counts: with a mean of only 7.5 fatal accidents per Friday, random variation alone produces day-to-day swings of 30% or more with appreciable probability. We report it for transparency but consider it most likely a chance finding---precisely the type of result that, if published in isolation, could perpetuate the Friday the 13th myth. This echoes Lo et al.'s isolated penetrating trauma finding (OR=1.65), which also likely reflected multiple testing.^7^

### Comparison with prior literature

Our systematic reproduction of Western analytical methods provides the strongest evidence to date that methodology is not the source of discrepant findings in this literature. When we applied Scanlon's paired comparison to Japanese data with approximately 100 times more accidents per day than Scanlon's original sample, the rate ratio was 1.04 versus Scanlon's 1.44. When we applied Näyhä's negative binomial model, our IRR was 1.01 versus Näyhä's 1.63 for women. The convergence of our null results across all three reproduced methods, combined with the null results from recent Western studies using different methods, strongly suggests that the original positive findings were statistical flukes rather than genuine effects.

### Strengths and limitations

This study has several strengths: it is the first from a non-Western cultural context, it employs the largest sample in this literature (1.9 million accidents), it systematically reproduces prior methods for direct comparison, and it reports a comprehensive suite of sensitivity analyses.

Several limitations should be acknowledged. First, with only 10 Friday the 13ths, our power to detect small effects was limited (minimum detectable effect: 16.2%); effects smaller than approximately 10% cannot be excluded by our data, though such small effects would lack practical significance for public health or traffic safety policy. The effects reported by Scanlon (+52%) and Näyhä (+63%) would have been easily detectable. Second, cultural exposure to the number 13 through Western media (films, imported products) means that some Japanese individuals may hold mild triskaidekaphobic beliefs, though this is unlikely to approach the deep-seated cultural fear found in Western nations.^10^ Third, we analyzed raw accident counts rather than rates per vehicle-kilometer traveled, as daily traffic volume data were not available at the national level. However, because our primary comparisons are between Fridays (same day of week), systematic differences in traffic volume are minimized; the case-crossover design further controls for within-month temporal trends. The consistency of results across the covariate-adjusted model (which controls for holidays and seasonal patterns that affect traffic volume) provides additional reassurance, though residual confounding by unmeasured traffic volume cannot be fully excluded. Fourth, the study period includes the COVID-19 pandemic, which altered traffic patterns; however, sensitivity analyses excluding 2020 confirmed our findings. Fifth, the NPA dataset does not include driver sex, precluding direct replication of Näyhä's sex-stratified analysis. Sixth, we did not perform formal residual diagnostics for the negative binomial models, though the low deviance-to-df ratios (0.03 and 0.02) suggest adequate model fit, and the consistency of conclusions across five distinct analytical approaches makes it unlikely that model misspecification altered the overall findings. Seventh, as an ecological study, we cannot make individual-level causal inferences; the absence of a population-level effect does not preclude the possibility that a small subset of individuals alter their behavior on Friday the 13th.

### Conclusion

Friday the 13th is not associated with increased traffic accidents in Japan. When Western analytical methods are faithfully reproduced in a culture without triskaidekaphobia, the effect disappears entirely. While our study was designed to test cultural mediation, the accumulated evidence---including null results from recent large Western studies---more strongly supports a universal null effect. Regardless of the underlying explanation, the practical implication is the same: the roads of Japan are no more dangerous on Friday the 13th than on any other Friday. Scanlon's advice to "stay at home" on Friday the 13th may be prudent counsel for the superstitious, but in Japan, there is no need to check the calendar before starting the car.

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

---

## Acknowledgments

Data analysis and manuscript preparation were assisted by Claude Opus 4.6 (Anthropic), which was used for statistical programming, literature search, and drafting. The author assumes full responsibility for the accuracy of the content, interpretation, and conclusions. All references were verified against PubMed and CrossRef records.

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

### Table 1. Daily accident counts on Friday the 13th versus control Fridays

| Friday the 13th | Accidents | Same-month control mean | Ratio |
|-----------------|-----------|------------------------|-------|
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
| **Mean** | **1,026.9** | **990.9** | **1.05** |

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

*RR = rate ratio; OR = odds ratio; NegBin = negative binomial regression; ED = emergency department; EMS = emergency medical services. N refers to total events analyzed except where noted (e.g., "21 Fri13s" = number of Friday the 13th dates, "41 (women)" = number of female traffic deaths). Effect estimates are RR unless otherwise specified. "not confirmed" indicates values not accessible from the original publication.*

### Figure Legends

**Figure 1.** Daily traffic accident counts on Friday the 13th (red points) compared with all other Fridays (gray points) during 2019-2024 in Japan. The dashed horizontal lines indicate group means. No systematic elevation is observed for Friday the 13th dates.

**Figure 2.** Cross-national forest plot of Friday the 13th effect estimates. Studies are ordered by publication year. Point estimates and 95% confidence intervals are shown where available. The vertical dashed line at RR=1.0 indicates no effect. Japan (present study) is highlighted with the largest sample size and a point estimate near unity.

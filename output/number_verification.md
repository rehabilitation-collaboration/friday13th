# Number verification — Phase 2C-C5

- Generated (UTC): 2026-07-23T14:12:28+00:00
- Manuscript: `manuscript.md`
- Truth source: `truth.json`
- Total core checks: 43
- Overall pass: **True**

## Status counts

- MATCH: 43
- NOT_FOUND: 0
- MISMATCH: 0
- TRUTH_MISSING: 0
- TRUTH_NULL: 0

## Per-check detail

| id | context | expected (rendered) | tol | status | found | note |
|---|---|---|---|---|---|---|
| `total_records` | Abstract Methods | 1884793 (1884793) | 0.0 | **MATCH** | 1,884,793 | |Δ|=0.0000 ≤ tol=0.0 |
| `n_friday13` | Abstract / Introduction | 10 (10) | 0.0 | **MATCH** | 10 | |Δ|=0.0000 ≤ tol=0.0 |
| `n_other_fri` | Abstract sample size | 303 (303) | 0.0 | **MATCH** | 303 | |Δ|=0.0000 ≤ tol=0.0 |
| `fri13_mean` | Results descriptive | 1026.9 (1026.9) | 0.5 | **MATCH** | 1,026.9 | |Δ|=0.0000 ≤ tol=0.5 |
| `other_fri_mean` | Results descriptive | 988.5742574257425 (988.6) | 0.5 | **MATCH** | 988.6 | |Δ|=0.0257 ≤ tol=0.5 |
| `scanlon_rr` | Abstract/Results Scanlon | 1.044765489876895 (1.04) | 0.02 | **MATCH** | 1.047 | |Δ|=0.0022 ≤ tol=0.02 |
| `scanlon_p_t` | Abstract Scanlon | 0.4719876490481709 (0.47) | 0.02 | **MATCH** | 0.47 | |Δ|=0.0020 ≤ tol=0.02 |
| `nayha_rr` | Abstract/Results Näyhä | 1.0118965217107652 (1.01) | 0.02 | **MATCH** | 1.012 | |Δ|=0.0001 ≤ tol=0.02 |
| `nayha_ci_low` | Results Näyhä | 0.5369014828864987 (0.54) | 0.03 | **MATCH** | 0.54 | |Δ|=0.0031 ≤ tol=0.03 |
| `nayha_ci_high` | Results Näyhä | 1.9071181646685924 (1.91) | 0.03 | **MATCH** | 1.91 | |Δ|=0.0029 ≤ tol=0.03 |
| `lo_f` | Abstract Lo | 0.15490496101997187 (0.15) | 0.02 | **MATCH** | 0.16 | |Δ|=0.0051 ≤ tol=0.02 |
| `lo_p_anova` | Abstract Lo | 0.9258472927739602 (0.93) | 0.02 | **MATCH** | 0.93 | |Δ|=0.0042 ≤ tol=0.02 |
| `pref_nb_wh_count_ratio` | Abstract/Results panel primary | 1.0247822114015948 (1.02) | 0.005 | **MATCH** | 1.02 | |Δ|=0.0048 ≤ tol=0.005 |
| `pref_nb_wh_ci_low` | Abstract/Results panel CI | 0.9724892885211054 (0.97) | 0.005 | **MATCH** | 0.973 | |Δ|=0.0005 ≤ tol=0.005 |
| `pref_nb_wh_ci_high` | Abstract/Results panel CI | 1.079887041637427 (1.08) | 0.005 | **MATCH** | 1.08 | |Δ|=0.0001 ≤ tol=0.005 |
| `pref_nb_wh_p` | Abstract/Results panel p | 0.3596238094123666 (0.360) | 0.005 | **MATCH** | 0.36 | |Δ|=0.0004 ≤ tol=0.005 |
| `diag_alpha_nb2` | Methods diagnostics α_NB2 | 0.02344953398058219 (0.0234) | 0.005 | **MATCH** | 0.023 | |Δ|=0.0004 ≤ tol=0.005 |
| `diag_qp_scale_factor` | Methods diagnostics QP | 1.4405522791057999 (1.441) | 0.02 | **MATCH** | 1.44 | |Δ|=0.0006 ≤ tol=0.02 |
| `diag_boot_ci_low` | Results bootstrap sensitivity | 0.9910391996630923 (0.9910) | 0.005 | **MATCH** | 0.991 | |Δ|=0.0000 ≤ tol=0.005 |
| `diag_boot_ci_high` | Results bootstrap sensitivity | 1.052680526946596 (1.0527) | 0.005 | **MATCH** | 1.05 | |Δ|=0.0027 ≤ tol=0.005 |
| `diag_boot_p` | Results bootstrap sensitivity | 0.18 (0.180) | 0.02 | **MATCH** | 0.18 | |Δ|=0.0000 ≤ tol=0.02 |
| `cc_new_count_ratio` | Abstract/Results case-crossover primary | 1.0363654713045818 (1.0364) | 0.01 | **MATCH** | 1.037 | |Δ|=0.0006 ≤ tol=0.01 |
| `cc_new_sw_t_ci_low` | Abstract case-crossover CI | 0.9458718914904964 (0.9459) | 0.005 | **MATCH** | 0.95 | |Δ|=0.0041 ≤ tol=0.005 |
| `cc_new_sw_t_ci_high` | Abstract case-crossover CI | 1.1355167647702105 (1.1355) | 0.005 | **MATCH** | 1.14 | |Δ|=0.0045 ≤ tol=0.005 |
| `cc_new_sw_t_p` | Abstract/Results case-crossover p | 0.39950095250035433 (0.400) | 0.02 | **MATCH** | 0.40 | |Δ|=0.0005 ≤ tol=0.02 |
| `cc_new_sign_n_plus` | Abstract sign test 8 of 10 | 8 (8) | 0.0 | **MATCH** | 8 | |Δ|=0.0000 ≤ tol=0.0 |
| `cc_new_sign_p` | Abstract sign test p | 0.109375 (0.109) | 0.02 | **MATCH** | 0.11 | |Δ|=0.0006 ≤ tol=0.02 |
| `cc_new_perm_geo_ratio` | Results permutation geometric | 1.0362678524603894 (1.0363) | 0.01 | **MATCH** | 1.037 | |Δ|=0.0007 ≤ tol=0.01 |
| `cc_new_perm_exact_p` | Results permutation exact p | 0.447265625 (0.4473) | 0.02 | **MATCH** | 0.45 | |Δ|=0.0027 ≤ tol=0.02 |
| `cc_new_perm_mc_p` | Results permutation MC p | 0.4496 (0.4496) | 0.02 | **MATCH** | 0.45 | |Δ|=0.0004 ≤ tol=0.02 |
| `pref_by_pref_ratio_min` | Abstract prefecture range Tottori | 0.5898586689006986 (0.59) | 0.02 | **MATCH** | 0.59 | |Δ|=0.0001 ≤ tol=0.02 |
| `pref_by_pref_ratio_max` | Abstract prefecture range Iwate | 1.2851799305129084 (1.29) | 0.02 | **MATCH** | 1.29 | |Δ|=0.0048 ≤ tol=0.02 |
| `pref_by_pref_ratio_median` | Abstract prefecture median | 1.0095322384638896 (1.01) | 0.02 | **MATCH** | 1.01 | |Δ|=0.0005 ≤ tol=0.02 |
| `pref_by_pref_n_ci_excludes_one` | Results 5 prefectures | 5 (5) | 0.0 | **MATCH** | 5 | |Δ|=0.0000 ≤ tol=0.0 |
| `pref_by_pref_n_ci_excludes_one_binomial_p` | Results binomial excess p | 0.0845264125014825 (0.085) | 0.005 | **MATCH** | 0.087 | |Δ|=0.0025 ≤ tol=0.005 |
| `pref_by_pref_n_bonferroni_significant` | Results Bonferroni 1 Mie | 1 (1) | 0.0 | **MATCH** | 1 | |Δ|=0.0000 ≤ tol=0.0 |
| `pref_by_pref_n_bh_fdr_significant` | Results BH-FDR 1 Mie | 1 (1) | 0.0 | **MATCH** | 1 | |Δ|=0.0000 ≤ tol=0.0 |
| `t4_fatal_rr_crude` | Table 4 fatal RR | 1.3073021425448186 (1.307) | 0.005 | **MATCH** | 1.307 | |Δ|=0.0003 ≤ tol=0.005 |
| `t4_fatal_p_raw` | Table 4 fatal raw p | 0.08702400026164696 (0.0870) | 0.005 | **MATCH** | 0.087 | |Δ|=0.0000 ≤ tol=0.005 |
| `t4_fatal_p_bonferroni` | Table 4 fatal Bonferroni | 0.6961920020931757 (0.6962) | 0.02 | **MATCH** | 0.696 | |Δ|=0.0002 ≤ tol=0.02 |
| `t4_fatal_nb_count_ratio` | Table 4 fatal NB approx | 1.2270252117875835 (1.227) | 0.02 | **MATCH** | 1.227 | |Δ|=0.0000 ≤ tol=0.02 |
| `t4_nighttime_rr_crude` | Table 4 nighttime RR | 1.2668495914952258 (1.267) | 0.005 | **MATCH** | 1.267 | |Δ|=0.0002 ≤ tol=0.005 |
| `t4_daytime_rr_crude` | Table 4 daytime RR | 0.9538421009227274 (0.954) | 0.005 | **MATCH** | 0.954 | |Δ|=0.0002 ≤ tol=0.005 |

# Friday the 13th Has No Bite in Japan

A Natural Cultural Control Study of 1.9 Million Traffic Accidents

## Overview

This repository contains the data and analysis code for the study examining whether Friday the 13th is associated with increased traffic accidents in Japan — a country where the number 13 carries no cultural superstition.

Using 1,884,793 police-recorded traffic accident records (2019–2024), we reproduced three established Western analytical approaches (Scanlon paired comparison, Näyhä negative binomial regression, Lo multi-date ANOVA) alongside case-crossover analysis and covariate-adjusted negative binomial regression. All five methods found no significant Friday the 13th effect.

## Repository Structure

```
├── data/                    # Aggregated daily accident counts (parquet)
├── src/
│   ├── 00_preliminary.py    # Preliminary Friday the 13th identification
│   ├── 01_prepare_data.py   # Data preparation and aggregation
│   ├── 02_main_analysis.py  # All statistical analyses (5 methods)
│   └── 03_figures.py        # Figure generation
├── output/
│   ├── figures/             # Figure 1 (scatter) and Figure 2 (forest plot)
│   ├── *.csv                # Analysis result tables
│   └── manuscript.pdf       # Formatted manuscript
├── generate_pdf.py          # Manuscript PDF generation (weasyprint)
└── manuscript.md            # Full manuscript text
```

## Data Sources

- **Traffic accidents**: [National Police Agency of Japan Open Data](https://www.npa.go.jp/publications/statistics/koutsuu/opendata/index_opendata.html) (2019–2024)
- **Weather data**: [Japan Meteorological Agency](https://www.jma.go.jp/) surface observation stations

## Reproduction

```bash
pip install pandas scipy statsmodels pyarrow matplotlib weasyprint markdown
python3 src/01_prepare_data.py
python3 src/02_main_analysis.py
python3 src/03_figures.py
python3 generate_pdf.py
```

## Citation

Shirai M. Friday the 13th Has No Bite in Japan: A Natural Cultural Control Study of 1.9 Million Traffic Accidents. SocArXiv Preprints. 2026.

## License

- Code: MIT License
- Manuscript and figures: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- Data: Public domain (Japanese government open data)

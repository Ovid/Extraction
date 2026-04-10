# Data Sources

This document catalogs every data source used to construct Extraction Index scores.
Each source is assigned a key used in the per-country data files.

## Source Registry

### Political Capture

| Key | Source | URL | Coverage | Update Cycle |
|-----|--------|-----|----------|--------------|
| `vdem_polyarchy` | V-Dem Electoral Democracy Index | https://www.v-dem.net/ | 202 countries, 1789–present | Annual |
| `vdem_clientelism` | V-Dem Clientelism Index | https://www.v-dem.net/ | 202 countries | Annual |
| `vdem_corruption` | V-Dem Political Corruption Index | https://www.v-dem.net/ | 202 countries | Annual |
| `fh_freedom` | Freedom House Freedom in the World | https://freedomhouse.org/ | 210 countries/territories | Annual |

### Economic Concentration

| Key | Source | URL | Coverage | Update Cycle |
|-----|--------|-----|----------|--------------|
| `wid_inequality` | World Inequality Database | https://wid.world/ | 180+ countries | Continuous |
| `wb_gini` | World Bank Gini Index | https://data.worldbank.org/ | 160+ countries | Annual |
| `ilo_labor_share` | ILO Labour Income Share of GDP (SDG 10.4.1) | https://ilostat.ilo.org/ | 189 countries | Annual |
| `ilo_wages` | ILO Global Wage Report data | https://www.ilo.org/ | 130+ countries | Biennial |

### Financial Extraction

| Key | Source | URL | Coverage | Update Cycle |
|-----|--------|-----|----------|--------------|
| `tjn_fsi` | Tax Justice Network Financial Secrecy Index | https://fsi.taxjustice.net/ | 141 jurisdictions | Biennial |
| `bis_finance` | BIS Financial Sector Statistics | https://www.bis.org/ | 60+ countries | Quarterly |
| `wb_domestic_credit` | World Bank Domestic Credit to Private Sector (% GDP) | https://data.worldbank.org/ | 180+ countries | Annual |
| `wb_net_interest_margin` | World Bank Bank Net Interest Margin (%) (GFDD) | https://data.worldbank.org/ | 167 countries | Annual (2-3 year lag) |

### Institutional Gatekeeping

| Key | Source | URL | Coverage | Update Cycle |
|-----|--------|-----|----------|--------------|
| `wjp_rule_of_law` | World Justice Project Rule of Law Index | https://worldjusticeproject.org/ | 142 countries | Annual |
| `wb_reg_quality` | World Bank Regulatory Quality Indicator | https://data.worldbank.org/ | 190+ countries | Annual |
| `oecd_pmr` | OECD Product Market Regulation Indicators | https://www.oecd.org/ | 38 OECD + partners | ~5 years |
| `cpi_corruption` | Transparency International CPI | https://www.transparency.org/ | 180 countries | Annual |

### Information & Media Capture

| Key | Source | URL | Coverage | Update Cycle |
|-----|--------|-----|----------|--------------|
| `rsf_press` | RSF World Press Freedom Index | https://rsf.org/ | 180 countries | Annual |
| `vdem_media` | V-Dem Media Freedom / Censorship indicators | https://www.v-dem.net/ | 202 countries | Annual |
| `vdem_internet` | V-Dem Internet Censorship | https://www.v-dem.net/ | 202 countries | Annual |

### Resource & Labor Extraction

| Key | Source | URL | Coverage | Update Cycle |
|-----|--------|-----|----------|--------------|
| `nrgi_rgi` | Natural Resource Governance Institute RGI | https://resourcegovernance.org/ | 89 assessments, 81 countries | ~3 years |
| `ituc_rights` | ITUC Global Rights Index | https://www.globalrightsindex.org/ | 149 countries | Annual |
| `ilo_child_labor` | ILO Child Labor Estimates | https://www.ilo.org/ | Global | ~4 years |
| `wb_natural_rents` | World Bank Total Natural Resource Rents (% GDP) | https://data.worldbank.org/ | 170+ countries | Annual |

### Transnational Facilitation

| Key | Source | URL | Coverage | Update Cycle |
|-----|--------|-----|----------|--------------|
| `tjn_cthi` | Tax Justice Network Corporate Tax Haven Index | https://cthi.taxjustice.net/ | 70 jurisdictions | Biennial |
| `tjn_fsi` | Tax Justice Network Financial Secrecy Index | https://fsi.taxjustice.net/ | 141 jurisdictions | Biennial |
| `oecd_beps` | OECD BEPS Country-by-Country data | https://www.oecd.org/ | ~50 jurisdictions | Annual |
| `gfi_iff` | Global Financial Integrity Illicit Financial Flows | https://gfintegrity.org/ | 148 countries | Irregular |

---

## Confidence Level Guidelines

- **High**: 3+ independent sources covering this domain, data updated within last 2 years
- **Moderate**: 1–2 reliable sources, or data is 2–4 years old
- **Low**: Single source, indirect indicators, or data >4 years old
- **Very Low**: No direct measurement; score based on extrapolation, journalistic accounts, or expert judgment

## Scoring Methodology

All domain scores are normalized to a 0–100 scale where:
- **0** = No measurable extraction (theoretical minimum; no country scores 0)
- **100** = Maximum extraction observed or plausible

Normalization uses min-max scaling across the full country dataset for each indicator,
then indicators within a domain are averaged. Where multiple indicators exist for a domain,
they receive equal weight within the domain unless otherwise justified.

The **composite score** is a weighted average of all seven domain scores.
Default weights are equal (1/7 each ≈ 0.143). Users can adjust weights interactively.

## Known Limitations

1. **OECD bias**: Many sources have richer coverage for OECD countries, creating systematic confidence gaps for developing nations.
2. **Legibility paradox**: The most extractive regimes often produce the least reliable data, meaning confidence and extraction tend to be inversely correlated.
3. **Institutional gatekeeping**: This domain is the least well-measured. Existing indices measure rule of law, not *who the law serves*. Scores here carry higher uncertainty.
4. **Transnational facilitation**: Data focuses on financial facilitation; other forms (arms transit, labor trafficking routes) are poorly measured.
5. **Lag**: Most sources update annually or less frequently. Rapid political changes may not be reflected.

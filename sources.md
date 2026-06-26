# Data Sources

All figures used in `data/grounding_counts.csv` are sourced from publicly available reporting and corporate disclosures. Raw source URLs are not included because fleet data is typically gated behind subscriptions or paginated earnings transcripts; the citations below are sufficient to verify the figures.

---

## FlightGlobal / Cirium

Industry databases that aggregate airline fleet and grounding data from lessors, regulators, and airlines. Used for:
- Global grounded-count totals (Oct 2024, Feb 2025, Jul 2025, Oct 2025)
- Volaris and VivaAerobus airline-level figures (Oct 2025)
- Wizz Air airline-level figures (Jul 2025, Oct 2025)

## RTX / Pratt & Whitney Earnings Calls

Quarterly investor presentations and earnings call transcripts from RTX Corporation (NYSE: RTX). Used for:
- JetBlue grounded-count figures (Q1 2025, Q1 2026 calls)
- MRO output index (2024 baseline = 100; 2025 = 126; Q4 2025 = 139)

The MRO index is derived from RTX disclosures describing the percentage increase in shop-visit throughput relative to 2024 levels. It is not an official RTX-published index; it is computed from verbal disclosures and should be treated as indicative rather than precise.

---

## Wizz Air Public Communications (`data/wizz_air_comms.csv`)

Statements and disclosures used to populate the Wizz Air narrative tracker. All sources are publicly available.

| Date | Source | URL |
|------|--------|-----|
| May 2024 | ch-aviation — "Wizz Air secures PW compensation but groundings persist" | https://www.ch-aviation.com/news/140655-wizz-air-secures-pw-compensation-but-groundings-persist |
| Aug 2024 | Skift — "Wizz Air Reports Drop in Earnings as Aircraft Groundings Bite" | https://skift.com/2024/08/01/wizz-air-reports-drop-in-earnings-as-aircraft-groundings-bite/ |
| Nov 2024 | Simple Flying — "Wizz Air Sees H1 Earnings Drop To $888 Million As P&W GTF Engine Issues Increase Operating Costs" | https://simpleflying.com/wizz-air-h1-earnings-drop-888-million-pratt-whitney-engine-gtf-engine-costs/ |
| Jan 2025 | Simple Flying — "40 Wizz Air Airbus Planes Will Remain Grounded Until 2026 Due To Pratt & Whitney Engine Issues" | https://simpleflying.com/40-wizz-air-airbus-planes-remain-grounded-until-2026-pratt-whitney/ |
| Jun 2025 | Wizz Air RNS — "Results for the 12 Months to 31 March 2025" | https://s204.q4cdn.com/169340705/files/doc_news/Final-Results-2025.pdf |
| Jul 2025 | Aerospace Global News — "GTF engine issues hit Wizz Air profits: Airbus groundings until 2027" | https://aerospaceglobalnews.com/news/wizz-air-gtf-engine-issues-2027-pratt-whitney-advantage/ |
| Aug 2025 | AJ Bell — "Wizz Air strikes compensation deal for grounded aircraft" | https://www.ajbell.co.uk/articles/latestnews/283945/wizz-air-strikes-compensation-deal-grounded-aircraft |
| Oct 2025 | Simple Flying — "Wizz Air Says P&W Engine Issues Will Continue Until End Of 2027" | https://simpleflying.com/wizz-air-engine-issues-end-of-2027/ |
| Jan 2026 | Investing.com — "Earnings call transcript: Wizz Air Q3 2026 sees 10% revenue growth, net loss narrows" | https://www.investing.com/news/transcripts/earnings-call-transcript-wizz-air-q3-2026-sees-10-revenue-growth-net-loss-narrows-93CH-4472487 |

### Data gaps
- Pre-May 2024 Wizz Air earnings calls (FY2023, H1 FY2024) did not include specific grounded-aircraft counts in publicly available summaries. Figures for those periods are not included in `wizz_air_comms.csv` to avoid speculation.
- Sentiment scores (1–5 scale) are editorial assessments based on language tone in the cited source, not a quantitative model. See `generate_report.py` for scoring rationale.

---

## Fleet Context Panel (added — share of global GTF fleet)

Uses the existing `data/grounding_counts.csv` Global row (835 of 2,450 GTF-powered aircraft grounded, 34.1%) and the four named-airline rows (Wizz Air, Volaris, VivaAerobus, JetBlue) to show how much of the 835 figure is attributable to airlines with individually sourced, disclosed counts versus the remainder. Named airlines account for ~102 of the 835 grounded aircraft in this dataset — the remaining ~733 are not broken out by airline in any currently sourced figure, and the panel labels this explicitly as a data gap rather than implying those aircraft are unaccounted for in reality.

## Chart 7 — Emissions Penalty Methodology

Estimates the extra CO2 from grounded GTF aircraft being effectively replaced in service by older, less fuel-efficient ceo-generation aircraft over an 18-month window.

**Inputs and sources:**
- **Fuel burn rate (2.5 tonnes/hour):** A320-family ceo total-aircraft cruise fuel burn. Pilot/engineer consensus on Airliners.net forums places A320ceo total aircraft burn at roughly 2.0–2.6 tonnes/hour at cruise altitude depending on weight and configuration; 2.5 t/hr sits in the upper-middle of this range and is used as the baseline.
- **Daily block hours (10.8):** MIT Airline Data Project, using US DOT Form 41 data — average daily block-hour utilization across all sectors, 2019 (pre-pandemic baseline).
- **CO2 conversion factor (3.16 kg CO2 / kg fuel):** Standard IATA jet fuel combustion factor.
- **Fuel-burn penalty (16–20%, mid-case 17.5%):** Sourced to widely-reported GTF-vs-ceo fuel efficiency improvement figures (commonly cited as "up to 20%" fuel burn improvement for GTF-powered neo aircraft over the ceo generation they replace). Treated here as the penalty incurred when flying ceo capacity instead of grounded GTF/neo capacity.
- **Fleet range (687–835 aircraft):** The two extreme data points in `data/grounding_counts.csv` (Oct 2024 and Oct 2025 global grounded counts).

**Headline calculation:** 2.5 t/hr × 10.8 hrs/day × 547.9 days (18 months) × 3.16 kg CO2/kg fuel × 17.5% × 835 aircraft ≈ **6.8 million tonnes CO2**.

**Range:** Low bound uses 16% penalty × 687 aircraft (≈5.1M tonnes); high bound uses 20% penalty × 835 aircraft (≈7.8M tonnes). Note this range conflates two different sources of uncertainty (penalty rate and fleet size) rather than varying them independently — a more rigorous sensitivity analysis would present these separately. Flagged here for transparency; worth tightening with a technical reviewer before external use.

## Chart 8 — CO2e Extension Methodology

Applies three named, sourced non-CO2 climate multipliers to the Chart 7 mid-case headline (6.8M tonnes CO2) to illustrate the range of total climate-equivalent impact once non-CO2 aviation effects are included. The three scenarios are **not a confidence interval** — they measure different scopes (contrail-only vs. all non-CO2 effects) and different metrics, and are presented as separate, labeled cases rather than blended into a single range.

- **Contrail-only, ~1.23x (Johansson et al. 2025):** Based on a 2025 climate-economic damage estimate finding the relative impact of contrails compared with CO2 is approximately 16–30% (central ~23%), using Teoh et al. central estimates. Narrowest scope — excludes NOx, soot, and water vapour effects.
- **GWP100 contrail, 1.63x (Lee et al., *Atmospheric Environment* 244, 2020/2021):** Lee et al. estimate the GWP100 ratio of contrail cirrus to CO2 impacts at 0.63 (i.e., total = CO2 × 1.63). This is the most-cited single peer-reviewed figure in the field, though it is contrail-specific rather than a full non-CO2 multiplier.
- **Industry RFI rule-of-thumb, 1.7x (cited via EASA):** EASA's report on aviation's non-CO2 climate impacts cites an overall multiplier of approximately 1.7x to account for the combined future impact of all aviation non-CO2 emissions (contrails, NOx, water vapour, soot). This is the broadest-scope figure but is explicitly contested within the scientific community — other proposed metrics (e.g., GTP) produce multipliers closer to 1.1x.

**Resulting CO2e range: ~8.4M–11.6M tonnes**, applied to the Chart 7 mid-case (6.8M tonnes CO2) only. Applying the same multipliers to the Chart 7 low/high bounds would produce a wider total range; this was not done here to avoid compounding two layers of uncertainty into a single number.

---

## Chart 3 — Fix Applied (June 2026)

The original Chart 3 used two independently-scaled y-axes (aircraft count, 600–920 range; MRO index, 80–160 range) to plot groundings against MRO recovery. Because the two scales were chosen independently to make both lines visible, the lines' visual proximity or convergence carried no real meaning — but could be misread as "the problem is resolving" simply because the lines appeared to move toward each other.

**Fix:** both series are now normalized to % change from their own baseline (groundings from Oct 2024; MRO index from 2024) and plotted on a single shared axis. This makes visual distance between the lines actually meaningful: as of Oct 2025, MRO output is up 39% while groundings are up 22% — MRO is recovering faster than the backlog is growing, but the lines are not converging toward a shared resolution point, and the chart no longer implies one.

## Financial Lens — Sourcing

The tracker's Financial Lens (tab F1–F4) pulls real, sourced dollar/euro figures rather than reframing existing operational charts.

- **F1 (Wizz Air P&W compensation):** €198.6M (FY2024) and €146M (H1 FY2025), both directly disclosed by Wizz Air in earnings calls. See `data/wizz_air_comms.csv`. Later compensation deals (Jan 2025, Aug 2025) were publicly announced but did not disclose specific amounts, so are not charted.
- **F2 (Operating profit miss):** Wizz Air Q1 FY2026 earnings call (24 Jul 2025) — actual operating profit of €27M against a forecast of €87M, a 69% miss. Company attributed this substantially to GTF-grounding-related costs.
- **F3 (Spare engine lease economics):** GTF engine lease rates of approximately $200,000/month/engine, sourced to Cirium data as reported across Reuters, Simple Flying, and AirInsight (2025–2026). A leased pair (two engines) can generate ~$4.8M/year — comparable to or exceeding the value of flying the aircraft itself, which is the underlying reason young aircraft are being dismantled for parts rather than repaired and returned to service.
- **F4 (Industry-wide cost):** IATA Director General Willie Walsh's estimate of $11B in total industry-wide supply chain disruption costs for the relevant year, of which $2.6B is engine-related. Cited via AviTrader and AeroMorning (Nov 2025). This figure covers the broader supply chain crisis, not GTF exclusively, though GTF groundings are cited as a major contributor — flagged here so the scope isn't overstated.

---

## Notes on accuracy

- Fleet sizes (denominator in `pct_grounded`) are approximate and vary by source.
- Grounding counts represent aircraft awaiting inspection or awaiting return of inspected/repaired engines, and may include aircraft newly delivered with uninspected engines.
- "Global" totals combine GTF variants: PW1100G (A320neo), PW1500G (A220), PW1900G (E2), and PW1400G (MC-21).
- All figures are point-in-time snapshots; the actual grounded count fluctuates daily.

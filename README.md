# GTF Grounding Tracker v2

An updated version of [jbechar/gtf-grounding-tracker](https://github.com/jbechar/gtf-grounding-tracker), incorporating several significant changes:

- **Fleet context panel** — new section providing broader fleet and grounding context
- **Charts 7–8 rebuilt** — emissions methodology overhauled for accuracy
- **Chart 3 fixed** — replaced misleading dual-axis layout with a single shared % axis
- **Financial / climate lens tab split** — separate tabs for financial and climate perspectives

## Files

| File | Purpose |
|------|---------|
| `index.html` | Complete, standalone dashboard — works in any browser with no build step |
| `generate_report.py` | Python script that regenerates `index.html` from local data files |
| `sources.md` | Source citations and methodology notes |

## Running the generator

`generate_report.py` requires two data files that are **not included in this repo** and do not currently exist on the original development machine:

```
data/ground_day_comparison.csv
data/variant_split.csv
```

Until those files are sourced and placed in a `data/` folder at the repo root, `generate_report.py` will not run successfully. **`index.html` is a complete, standalone file and works fine without them** — only re-running the generator needs them.

The script also uses two files that do exist in the original repo:

```
data/grounding_counts.csv
data/wizz_air_comms.csv
```

Copy those from [jbechar/gtf-grounding-tracker](https://github.com/jbechar/gtf-grounding-tracker) (they are gitignored there and must be obtained separately).

## Requirements

```
pip install plotly pandas
```

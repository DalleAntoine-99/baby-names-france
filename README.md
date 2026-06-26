# Baby Names France

Interactive dashboard exploring French first name data (1900–2020) across three angles: temporal trends, regional distribution, and gender effects.

## Data

Download `dpt2020.csv` from the [INSEE website](https://www.insee.fr/fr/statistiques/7633685) and place it in the `Names hints/` folder alongside the GeoJSON file.

## Setup

```bash
pip install dash plotly pandas numpy
```

## Run

**v1 (original):**
```bash
python app.py
```

**v2 (improved):**
```bash
python app_v2.py
```

Then open [http://localhost:8050](http://localhost:8050) in your browser.

## Visualizations

**1. Temporal heatmap** — names × years, color-encoded by normalized birth frequency (log scale). Highlights consistent classics vs. short-lived trends.

**2. Regional map (LQ choropleth)** — each department colored by Location Quotient (name share locally vs. nationally). Values above 1 mean the name is overrepresented there. Click a department to see its most distinctive names.

**3. Gender effects** — scatter of all names by total popularity vs. % female. Click any name to see its male/female breakdown year by year.

## v1 → v2 improvements

Based on peer review feedback.

### Data
- `_PRENOMS_RARES` (aggregated rare names) filtered out at load time
- Division-by-zero edge case fixed in gender score computation

### Visualization 1 — Temporal heatmap
- Switched from `px.density_heatmap` to `px.imshow` on a pivot table for accurate color encoding
- Added **Top N dropdown** (20 / 50 / 100 / 200 names) to control readability
- Names sorted by **peak popularity year** instead of alphabetically
- Tooltip now shows **actual birth counts** instead of the log-normalized value
- Y-axis labels explicitly forced; chart height scales with number of names (22 px/row)

### Visualization 2 — Regional map + bar chart
- Added an **explanatory note** for the Location Quotient directly in the interface
- Bar chart uses a **single neutral color** instead of a redundant color gradient (length already encodes LQ)

### Visualization 3 — Gender scatter + line chart
- Added **opacity (0.55)** to reduce overplotting in dense clusters
- Color scale changed from Viridis to a **blue → purple → red gradient**, consistent with the M/F colors in the line chart
- **Name labels** added on the 12 most popular names for immediate readability
- Axis labels clarified (`log₁₀ total births`, `share of female births`)

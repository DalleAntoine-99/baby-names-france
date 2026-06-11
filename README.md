# Baby Names France

Interactive dashboard exploring French first name data (1900–2020) across three angles: temporal trends, regional distribution, and gender effects.

## Data

Download `dpt2020.csv` from the [INSEE website](https://www.insee.fr/fr/statistiques/7633685) and place it in the project root alongside `app.py`.

## Setup

```bash
pip install dash plotly pandas numpy
```

## Run

```bash
python app.py
```

Then open [http://localhost:8050](http://localhost:8050) in your browser.

## Visualizations

**1. Temporal heatmap** — names × years, color-encoded by normalized birth frequency (log scale). Highlights consistent classics vs. short-lived trends.

**2. Regional map (LQ choropleth)** — each department colored by Location Quotient (name share locally vs. nationally). Values above 1 mean the name is overrepresented there. Click a department to see its most distinctive names.

**3. Gender effects** — scatter of all names by total popularity vs. % female. Click any name to see its male/female breakdown year by year.

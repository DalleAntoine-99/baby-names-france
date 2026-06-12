import json
from pathlib import Path

import dash
import numpy as np
import pandas as pd
import plotly.express as px
from dash import Input, Output, dcc, html

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Names hints"
MIN_NATIONAL_BIRTHS = 1000
MIN_DEPARTMENT_BIRTHS = 20


def find_data_file(filename):
    """Cherche un fichier dans le dossier de données puis à la racine."""
    for folder in (DATA_DIR, BASE_DIR):
        path = folder / filename
        if path.exists():
            return path

    raise FileNotFoundError(
        f"{filename} est introuvable dans '{DATA_DIR}' ou '{BASE_DIR}'."
    )


print("Chargement des données...")

df = pd.read_csv(find_data_file("dpt2020.csv"), sep=";")
df = df.rename(
    columns={
        "preusuel": "prenom",
        "annais": "annee",
        "dpt": "departement",
    }
)
df = df[(df["annee"] != "XXXX") & (df["departement"] != "XX")].copy()
df["annee"] = df["annee"].astype(int)
df["sexe"] = df["sexe"].map({1: "M", 2: "F"})

with find_data_file("departements-version-simplifiee.geojson").open(
    encoding="utf-8"
) as geojson_file:
    geojson_france = json.load(geojson_file)

# Données de la heatmap
df_v1 = df.groupby(["prenom", "annee"])["nombre"].sum().reset_index()
total_par_an = df_v1.groupby("annee")["nombre"].sum().rename("total_an")
df_v1 = df_v1.merge(total_par_an, on="annee")
df_v1["part_normalisee"] = df_v1["nombre"] / df_v1["total_an"]
df_v1["log_part"] = np.log1p(df_v1["part_normalisee"] * 100000)

noms_gardes = df_v1.groupby("prenom")["nombre"].sum()
noms_gardes = noms_gardes[noms_gardes > 100].index
df_v1 = df_v1[df_v1["prenom"].isin(noms_gardes)]

# Données de la carte régionale
df_v2 = df.groupby(["prenom", "departement"])["nombre"].sum().reset_index()
total_dept = df_v2.groupby("departement")["nombre"].sum().rename("total_dept")
nb_nat = df.groupby("prenom")["nombre"].sum().rename("nb_nat")

df_v2 = (
    df_v2.merge(total_dept.reset_index(), on="departement")
    .merge(nb_nat.reset_index(), on="prenom")
)
df_v2["share_dept"] = df_v2["nombre"] / df_v2["total_dept"]
df_v2["share_nat"] = df_v2["nb_nat"] / df["nombre"].sum()
df_v2["LQ"] = df_v2["share_dept"] / df_v2["share_nat"]

regional_names = sorted(
    nb_nat[nb_nat >= MIN_NATIONAL_BIRTHS].index.tolist()
)
default_regional_name = "MARIE" if "MARIE" in regional_names else regional_names[0]

# Données de la visualisation par sexe
df_v3 = (
    df.groupby(["prenom", "sexe"])["nombre"]
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)
for sexe in ("M", "F"):
    if sexe not in df_v3:
        df_v3[sexe] = 0

df_v3["total"] = df_v3["M"] + df_v3["F"]
df_v3["pct_female"] = df_v3["F"] / df_v3["total"]
df_v3["log_total"] = np.log10(df_v3["total"] + 1)
df_v3["gender_score"] = (
    df_v3[["M", "F"]].min(axis=1) / df_v3[["M", "F"]].max(axis=1)
)

app = dash.Dash(__name__)

# --- LAYOUT (Interface Visuelle) ---
section_style = {
    "padding": "20px",
    "backgroundColor": "#f9f9f9",
    "marginBottom": "20px",
    "borderRadius": "8px",
}
half_width = {"display": "inline-block", "width": "50%"}

app.layout = html.Div(
    [
        html.H1(
            "Visualisation — Prénoms en France",
            style={"color": "#A6192E", "textAlign": "center"},
        ),
        html.Div(
            [
                html.H2("1. Évolution temporelle"),
                html.P(
                    "Couleur = intensité des naissances normalisée "
                    "(échelle logarithmique)."
                ),
                dcc.Graph(id="heatmap-temporelle"),
            ],
            style=section_style,
        ),
        html.Div(
            [
                html.H2("2. Effet régional"),
                html.P(
                    "Choisissez un prénom, puis cliquez sur un département "
                    "pour afficher les prénoms qui y sont surreprésentés."
                ),
                html.Label("Prénom affiché sur la carte :", htmlFor="regional-name"),
                dcc.Dropdown(
                    id="regional-name",
                    options=[
                        {"label": name.title(), "value": name}
                        for name in regional_names
                    ],
                    value=default_regional_name,
                    clearable=False,
                    searchable=True,
                    style={"marginBottom": "12px"},
                ),
                html.Div(
                    [
                        dcc.Graph(id="carte-lq", style=half_width),
                        dcc.Graph(id="bar-lq-detail", style=half_width),
                    ]
                ),
            ],
            style=section_style,
        ),
        html.Div(
            [
                html.H2("3. Effets liés au sexe"),
                html.P(
                    "Cliquez sur un prénom pour afficher son évolution "
                    "chez les filles et les garçons."
                ),
                html.Div(
                    [
                        dcc.Graph(id="scatter-genre", style=half_width),
                        dcc.Graph(id="line-genre-detail", style=half_width),
                    ]
                ),
            ],
            style={**section_style, "marginBottom": "0"},
        ),
    ],
    style={"fontFamily": "sans-serif", "maxWidth": "1200px", "margin": "auto"},
)


@app.callback(Output("heatmap-temporelle", "figure"), Input("heatmap-temporelle", "id"))
def update_heatmap(_):
    fig = px.density_heatmap(
        df_v1,
        x="annee",
        y="prenom",
        z="log_part",
        color_continuous_scale="Reds",
        title="Popularité des prénoms au fil du temps",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
    return fig


@app.callback(Output("carte-lq", "figure"), Input("regional-name", "value"))
def update_map(prenom):
    data = df_v2[df_v2["prenom"] == prenom]
    
    fig = px.choropleth_mapbox(
        data,
        geojson=geojson_france,
        locations="departement",
        featureidkey="properties.code",
        color="LQ",
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=1,
        custom_data=["nombre"],
        mapbox_style="carto-positron",
        zoom=4.5,
        center={"lat": 46.5, "lon": 2.5},
        title=f"Quotient de localisation pour {prenom.title()}",
    )
    fig.update_traces(
        hovertemplate=(
            "Département : %{location}<br>"
            "Naissances : %{customdata[0]:,.0f}<br>"
            "LQ : %{z:.2f}<extra></extra>"
        )
    )
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
    return fig


@app.callback(Output("bar-lq-detail", "figure"), Input("carte-lq", "clickData"))
def update_bar_chart(clickData):
    department = clickData["points"][0]["location"] if clickData else "75"
    data = df_v2[
        (df_v2["departement"] == department)
        & (df_v2["nombre"] >= MIN_DEPARTMENT_BIRTHS)
        & (df_v2["nb_nat"] >= MIN_NATIONAL_BIRTHS)
    ].nlargest(15, "LQ")
    
    fig = px.bar(
        data,
        x="LQ",
        y="prenom",
        orientation="h",
        title=f"Prénoms surreprésentés dans le département {department}",
        color="LQ",
        color_continuous_scale="Reds",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


@app.callback(Output("scatter-genre", "figure"), Input("scatter-genre", "id"))
def update_scatter(_):
    fig = px.scatter(
        df_v3,
        x="log_total",
        y="pct_female",
        size="total",
        color="gender_score",
        hover_name="prenom",
        color_continuous_scale="Viridis",
        title="Répartition par sexe et popularité",
    )
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray")
    fig.update_layout(height=500)
    return fig


@app.callback(Output("line-genre-detail", "figure"), Input("scatter-genre", "clickData"))
def update_line_chart(clickData):
    prenom = clickData["points"][0]["hovertext"] if clickData else "CAMILLE"
    data = (
        df[df["prenom"] == prenom]
        .groupby(["annee", "sexe"])["nombre"]
        .sum()
        .reset_index()
    )
    
    fig = px.line(
        data,
        x="annee",
        y="nombre",
        color="sexe",
        title=f"Évolution historique détaillée : {prenom}",
        color_discrete_map={"M": "#1f77b4", "F": "#d62728"},
    )
    fig.update_layout(height=500)
    return fig


if __name__ == "__main__":
    app.run(debug=True)

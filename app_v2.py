import json

import dash
import numpy as np
import pandas as pd
import plotly.express as px
from dash import Input, Output, dcc, html

MIN_NATIONAL_BIRTHS = 1000
MIN_DEPARTMENT_BIRTHS = 20

print("Chargement des données...")

df = pd.read_csv("Names hints/dpt2020.csv", sep=";")
df = df.rename(columns={"preusuel": "prenom", "annais": "annee", "dpt": "departement"})
df = df[
    (df["annee"] != "XXXX")
    & (df["departement"] != "XX")
    & (df["prenom"] != "_PRENOMS_RARES")
].copy()
df["annee"] = df["annee"].astype(int)
df["sexe"] = df["sexe"].map({1: "M", 2: "F"})

with open("Names hints/departements-version-simplifiee.geojson", encoding="utf-8") as f:
    geojson_france = json.load(f)

# --- Données Viz 1 : heatmap ---
df_v1 = df.groupby(["prenom", "annee"])["nombre"].sum().reset_index()
total_par_an = df_v1.groupby("annee")["nombre"].sum().rename("total_an")
df_v1 = df_v1.merge(total_par_an, on="annee")
df_v1["part_normalisee"] = df_v1["nombre"] / df_v1["total_an"]
df_v1["log_part"] = np.log1p(df_v1["part_normalisee"] * 100000)

noms_gardes = df_v1.groupby("prenom")["nombre"].sum()
noms_gardes = noms_gardes[noms_gardes > 100].index
df_v1 = df_v1[df_v1["prenom"].isin(noms_gardes)]

peak_year = (
    df_v1.loc[df_v1.groupby("prenom")["nombre"].idxmax(), ["prenom", "annee"]]
    .set_index("prenom")["annee"]
)
df_v1["peak_year"] = df_v1["prenom"].map(peak_year)

# --- Données Viz 2 : carte LQ ---
df_v2 = df.groupby(["prenom", "departement"])["nombre"].sum().reset_index()
total_dept = df_v2.groupby("departement")["nombre"].sum().rename("total_dept")
nb_nat = df.groupby("prenom")["nombre"].sum().rename("nb_nat")
df_v2 = (
    df_v2
    .merge(total_dept.reset_index(), on="departement")
    .merge(nb_nat.reset_index(), on="prenom")
)
df_v2["share_dept"] = df_v2["nombre"] / df_v2["total_dept"]
df_v2["share_nat"] = df_v2["nb_nat"] / df["nombre"].sum()
df_v2["LQ"] = df_v2["share_dept"] / df_v2["share_nat"]

regional_names = sorted(nb_nat[nb_nat >= MIN_NATIONAL_BIRTHS].index.tolist())
default_regional_name = "MARIE" if "MARIE" in regional_names else regional_names[0]

# --- Données Viz 3 : genre ---
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
    df_v3[["M", "F"]].min(axis=1)
    / df_v3[["M", "F"]].max(axis=1).replace(0, np.nan)
)

app = dash.Dash(__name__)

section_style = {
    "padding": "20px",
    "backgroundColor": "#f9f9f9",
    "marginBottom": "20px",
    "borderRadius": "8px",
}
half_width = {"display": "inline-block", "width": "50%"}

LQ_EXPLANATION = (
    "Le Quotient de Localisation (LQ) compare la part d'un prénom dans un département "
    "à sa part nationale. LQ > 1 : le prénom est surreprésenté localement. "
    "LQ < 1 : il est sous-représenté."
)

app.layout = html.Div(
    [
        html.H1(
            "Visualisation — Prénoms en France",
            style={"color": "#A6192E", "textAlign": "center"},
        ),

        # --- Viz 1 ---
        html.Div(
            [
                html.H2("1. Évolution temporelle"),
                html.P(
                    "Couleur = intensité des naissances normalisée (échelle logarithmique). "
                    "Triés par année de pic de popularité."
                ),
                html.Div(
                    [
                        html.Label("Prénoms affichés :", htmlFor="top-n-select"),
                        dcc.Dropdown(
                            id="top-n-select",
                            options=[
                                {"label": "Top 20", "value": 20},
                                {"label": "Top 50", "value": 50},
                                {"label": "Top 100", "value": 100},
                                {"label": "Top 200", "value": 200},
                            ],
                            value=50,
                            clearable=False,
                            style={"width": "180px", "display": "inline-block"},
                        ),
                    ],
                    style={"marginBottom": "12px"},
                ),
                dcc.Graph(id="heatmap-temporelle"),
            ],
            style=section_style,
        ),

        # --- Viz 2 ---
        html.Div(
            [
                html.H2("2. Effet régional"),
                html.P(
                    "Choisissez un prénom, puis cliquez sur un département "
                    "pour afficher les prénoms qui y sont surreprésentés."
                ),
                html.P(
                    LQ_EXPLANATION,
                    style={"fontStyle": "italic", "color": "#555", "fontSize": "0.9em"},
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

        # --- Viz 3 ---
        html.Div(
            [
                html.H2("3. Effets liés au sexe"),
                html.P(
                    "Cliquez sur un prénom pour afficher son évolution "
                    "chez les filles et les garçons. "
                    "Taille = nombre total de naissances. "
                    "Couleur = score de mixité (0 = monogenre, 1 = parfaitement mixte)."
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


@app.callback(Output("heatmap-temporelle", "figure"), Input("top-n-select", "value"))
def update_heatmap(top_n):
    top_names = df_v1.groupby("prenom")["nombre"].sum().nlargest(top_n).index
    data = df_v1[df_v1["prenom"].isin(top_names)].copy()

    # Ordre des lignes : par année de pic
    name_order = (
        data.drop_duplicates("prenom")
        .sort_values("peak_year")["prenom"]
        .tolist()
    )

    pivot_color = data.pivot_table(
        index="prenom", columns="annee", values="log_part", fill_value=0
    ).reindex(name_order)

    pivot_hover = data.pivot_table(
        index="prenom", columns="annee", values="nombre", fill_value=0
    ).reindex(name_order)

    fig = px.imshow(
        pivot_color,
        color_continuous_scale="Reds",
        aspect="auto",
        title=f"Popularité des prénoms au fil du temps (Top {top_n})",
        labels={"color": "Intensité (log)", "x": "Année", "y": "Prénom"},
    )
    fig.update_traces(
        customdata=pivot_hover.values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Année : %{x}<br>"
            "Naissances : %{customdata:,.0f}<extra></extra>"
        ),
    )
    fig.update_yaxes(tickmode="array", tickvals=name_order, ticktext=name_order)
    fig.update_layout(height=max(400, top_n * 22))
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
        title=f"Prénoms surreprésentés — département {department}",
        labels={"LQ": "Quotient de localisation", "prenom": "Prénom"},
    )
    fig.update_traces(marker_color="#A6192E")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
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
        color_continuous_scale=["#1f77b4", "#9467bd", "#d62728"],
        opacity=0.55,
        title="Répartition par sexe et popularité",
        labels={
            "log_total": "Popularité (log₁₀ naissances totales)",
            "pct_female": "Part des naissances féminines",
            "gender_score": "Score mixité",
        },
    )
    # Labels sur les 12 prénoms les plus populaires
    for _, row in df_v3.nlargest(12, "total").iterrows():
        fig.add_annotation(
            x=row["log_total"],
            y=row["pct_female"],
            text=row["prenom"].title(),
            showarrow=False,
            font={"size": 8, "color": "#333"},
            yshift=10,
        )
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray")
    fig.update_layout(height=500)
    return fig


@app.callback(
    Output("line-genre-detail", "figure"), Input("scatter-genre", "clickData")
)
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
        title=f"Évolution historique : {prenom.title()}",
        color_discrete_map={"M": "#1f77b4", "F": "#d62728"},
        labels={"annee": "Année", "nombre": "Naissances", "sexe": "Sexe"},
    )
    fig.update_layout(height=500)
    return fig


if __name__ == "__main__":
    app.run(debug=True)

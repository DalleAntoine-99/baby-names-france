import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
import json

# ==========================================
# 1. CHARGEMENT ET NETTOYAGE DES DONNÉES
# ==========================================
print("Chargement des données en cours...")

# Chargement du csv (séparateur point-virgule)
df = pd.read_csv('dpt2020.csv', sep=';')

# Renommer les colonnes pour correspondre au code de visualisation
df = df.rename(columns={
    'preusuel': 'prenom',
    'annais': 'annee',
    'dpt': 'departement'
})

# Nettoyage des données INSEE
df = df[df['annee'] != 'XXXX']
df['annee'] = df['annee'].astype(int)

df = df[df['departement'] != 'XX']

# Convertir le sexe (1 = M, 2 = F)
df['sexe'] = df['sexe'].map({1: 'M', 2: 'F'})

# Chargement du GeoJSON pour la carte
# Assure-toi que la clé géographique (ex: properties.code) correspond aux numéros de département
try:
    with open('departements-version-simplifiee.geojson', 'r') as f:
        geojson_france = json.load(f)
except FileNotFoundError:
    geojson_france = None
    print("Attention : Fichier geojson introuvable. La carte ne s'affichera pas correctement.")

# ==========================================
# 2. PRÉPARATION DATA VIZ 1 : Heatmap
# ==========================================
df_v1 = df.groupby(['prenom', 'annee'])['nombre'].sum().reset_index()

total_par_an = df_v1.groupby('annee')['nombre'].sum().reset_index(name='total_an')
df_v1 = df_v1.merge(total_par_an, on='annee')
df_v1['part_normalisee'] = df_v1['nombre'] / df_v1['total_an']
df_v1['log_part'] = np.log1p(df_v1['part_normalisee'] * 100000)

# Filtre pour ne garder que les prénoms ayant plus de 100 naissances au total
noms_gardes = df_v1.groupby('prenom')['nombre'].sum()
noms_gardes = noms_gardes[noms_gardes > 100].index
df_v1 = df_v1[df_v1['prenom'].isin(noms_gardes)]

# ==========================================
# 3. PRÉPARATION DATA VIZ 2 : LQ Choropleth
# ==========================================
df_v2 = df.groupby(['prenom', 'departement'])['nombre'].sum().reset_index()

total_dept = df_v2.groupby('departement')['nombre'].sum().reset_index(name='total_dept')
df_v2 = df_v2.merge(total_dept, on='departement')
df_v2['share_dept'] = df_v2['nombre'] / df_v2['total_dept']

total_nat = df['nombre'].sum()
nb_nat = df.groupby('prenom')['nombre'].sum().reset_index(name='nb_nat')
df_v2 = df_v2.merge(nb_nat, on='prenom')
df_v2['share_nat'] = df_v2['nb_nat'] / total_nat

# Calcul du Quotient de Localisation
df_v2['LQ'] = df_v2['share_dept'] / df_v2['share_nat']

# ==========================================
# 4. PRÉPARATION DATA VIZ 3 : Scatter Genre
# ==========================================
df_v3 = df.groupby(['prenom', 'sexe'])['nombre'].sum().unstack(fill_value=0).reset_index()

if 'M' not in df_v3.columns: df_v3['M'] = 0
if 'F' not in df_v3.columns: df_v3['F'] = 0

df_v3['total'] = df_v3['M'] + df_v3['F']
df_v3['pct_female'] = df_v3['F'] / df_v3['total']
df_v3['log_total'] = np.log10(df_v3['total'] + 1)

df_v3['gender_score'] = df_v3[['M', 'F']].min(axis=1) / df_v3[['M', 'F']].max(axis=1)

print("Préparation des données terminée. Lancement de Dash...")

# ==========================================
# 5. INITIALISATION DE L'APPLICATION DASH
# ==========================================
app = dash.Dash(__name__)

# --- LAYOUT (Interface Visuelle) ---
app.layout = html.Div([
    html.H1("Visualisation — Prénoms en France", style={'color': '#A6192E', 'font-family': 'sans-serif', 'textAlign': 'center'}),
    
    # === VIZ 1 : HEATMAP ===
    html.Div([
        html.H2("1. Évolution Temporelle (Heatmap)"),
        html.P("Couleur = intensité des naissances normalisée (échelle log)."),
        dcc.Graph(id='heatmap-temporelle')
    ], style={'padding': '20px', 'backgroundColor': '#f9f9f9', 'marginBottom': '20px', 'borderRadius': '8px'}),
    
    # === VIZ 2 : CARTE LQ + BAR CHART ===
    html.Div([
        html.H2("2. Effet Régional (LQ Choropleth)"),
        html.P("Cliquez sur un département sur la carte pour voir ses prénoms les plus distinctifs (surreprésentés) à droite."),
        html.Div([
            dcc.Graph(id='carte-lq', style={'display': 'inline-block', 'width': '50%'}),
            dcc.Graph(id='bar-lq-detail', style={'display': 'inline-block', 'width': '50%'})
        ])
    ], style={'padding': '20px', 'backgroundColor': '#f9f9f9', 'marginBottom': '20px', 'borderRadius': '8px'}),
    
    # === VIZ 3 : SCATTER GENRE + COURBE DÉTAIL ===
    html.Div([
        html.H2("3. Effets de Genre (Scatter + Dual-line)"),
        html.P("Cliquez sur un point (un prénom) du nuage de points à gauche pour afficher son évolution historique à droite."),
        html.Div([
            dcc.Graph(id='scatter-genre', style={'display': 'inline-block', 'width': '50%'}),
            dcc.Graph(id='line-genre-detail', style={'display': 'inline-block', 'width': '50%'})
        ])
    ], style={'padding': '20px', 'backgroundColor': '#f9f9f9', 'borderRadius': '8px'})
], style={'font-family': 'sans-serif', 'maxWidth': '1200px', 'margin': 'auto'})

# ==========================================
# 6. CALLBACKS (Interactivité)
# ==========================================

# Génération Viz 1
@app.callback(Output('heatmap-temporelle', 'figure'), Input('heatmap-temporelle', 'id'))
def update_heatmap(_):
    # Pour ne pas surcharger le navigateur, on peut afficher un sample ou le top N 
    # (ici on affiche tout ce qui a été filtré, attention si > 3000 prénoms ça peut être lourd)
    fig = px.density_heatmap(
        df_v1, x='annee', y='prenom', z='log_part',
        color_continuous_scale='Reds',
        title="Heatmap Prénoms x Années"
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
    return fig

# Génération Viz 2 (Carte)
@app.callback(Output('carte-lq', 'figure'), Input('carte-lq', 'id'))
def update_map(_):
    if geojson_france is None:
        return px.scatter(title="Erreur: GeoJSON manquant")
        
    # Filtrer sur un prénom par défaut pour afficher la carte (ex: 'MARIE')
    # Dans la version finale de ton dashboard, ce prénom devrait provenir d'un dcc.Dropdown
    dff_map = df_v2[df_v2['prenom'] == 'MARIE']
    
    fig = px.choropleth_mapbox(
        dff_map, geojson=geojson_france, locations='departement', 
        featureidkey="properties.code", # A adapter selon la structure de ton geojson !
        color='LQ', color_continuous_scale='RdBu_r', color_continuous_midpoint=1,
        mapbox_style="carto-positron", zoom=4.5, center={"lat": 46.5, "lon": 2.5},
        title="Quotient de Localisation (LQ) - Prénom: MARIE"
    )
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    return fig

# Génération Viz 2 (Bar chart lié à la carte)
@app.callback(Output('bar-lq-detail', 'figure'), Input('carte-lq', 'clickData'))
def update_bar_chart(clickData):
    dept = clickData['points'][0]['location'] if clickData else '75'
    dff_bar = df_v2[df_v2['departement'] == dept].nlargest(15, 'LQ')
    
    fig = px.bar(
        dff_bar, x='LQ', y='prenom', orientation='h',
        title=f"Top 15 Prénoms surreprésentés - Dépt {dept}",
        color='LQ', color_continuous_scale='Reds'
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

# Génération Viz 3 (Scatter)
@app.callback(Output('scatter-genre', 'figure'), Input('scatter-genre', 'id'))
def update_scatter(_):
    fig = px.scatter(
        df_v3, x='log_total', y='pct_female', 
        size='total', color='gender_score', 
        hover_name='prenom',
        color_continuous_scale='Viridis',
        title="Neutralité vs Popularité (Clic pour détailler)"
    )
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray")
    fig.update_layout(height=500)
    return fig

# Génération Viz 3 (Courbe de détail liée au scatter)
@app.callback(Output('line-genre-detail', 'figure'), Input('scatter-genre', 'clickData'))
def update_line_chart(clickData):
    prenom = clickData['points'][0]['hovertext'] if clickData else 'CAMILLE'
    
    # On filtre sur le prénom cliqué, puis on groupe par année et sexe pour additionner tous les départements
    dff_line = df[df['prenom'] == prenom].groupby(['annee', 'sexe'])['nombre'].sum().reset_index()
    
    fig = px.line(
        dff_line, x='annee', y='nombre', color='sexe',
        title=f"Évolution historique détaillée : {prenom}",
        color_discrete_map={'M': '#1f77b4', 'F': '#d62728'} # Bleu pour M, Rouge pour F
    )
    fig.update_layout(height=500)
    return fig

if __name__ == '__main__':
    # Lance le serveur (Mise à jour Dash 2.0+)
    app.run(debug=True)
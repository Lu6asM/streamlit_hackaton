import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import charger_donnees, get_stations, INDICATEURS
from utils.footer import afficher_footer

# ============================================================
# PAGE : CARTE INTERACTIVE
# ============================================================
st.title("🗺️ Carte Interactive")
st.markdown("Explorez les données météorologiques de Loire-Atlantique par ville.")

df = charger_donnees()

# Zones de focus prédéfinies
ZONES = {
    "Loire-Atlantique (tout)": {"lat": 47.25, "lon": -1.6, "zoom": 8.5},
    "Nantes Métropole": {"lat": 47.22, "lon": -1.55, "zoom": 11},
    "Saint-Nazaire / Estuaire": {"lat": 47.28, "lon": -2.2, "zoom": 11},
    "Nord du département": {"lat": 47.5, "lon": -1.4, "zoom": 10},
    "Littoral / Côte": {"lat": 47.15, "lon": -2.1, "zoom": 10},
    "Sud-Est / Vignoble": {"lat": 47.1, "lon": -1.3, "zoom": 10},
}

# --- Sidebar : filtres ---
st.sidebar.header("Filtres")

indicateur_choisi = st.sidebar.selectbox(
    "Indicateur à afficher",
    options=list(INDICATEURS.keys()),
    format_func=lambda x: INDICATEURS[x]["nom"],
)

annee_min = int(df["annee"].min())
annee_max = int(df["annee"].max())
plage_annees = st.sidebar.slider(
    "Période",
    min_value=annee_min,
    max_value=annee_max,
    value=(2000, annee_max),
)

zone_choisie = st.sidebar.selectbox("Zoom sur une zone", options=list(ZONES.keys()))

style_carte = st.sidebar.selectbox(
    "Style de carte",
    options=["open-street-map", "carto-positron", "carto-darkmatter"],
    index=2,
)

# --- Calcul des données par ville pour la période ---
df_filtre = df[(df["annee"] >= plage_annees[0]) & (df["annee"] <= plage_annees[1])]

villes_data = df_filtre.groupby("ville").agg(
    latitude=("latitude", "first"),
    longitude=("longitude", "first"),
    valeur=(indicateur_choisi, "mean"),
    nb_mesures=("date", "count"),
).reset_index().dropna(subset=["valeur", "latitude", "longitude"])

# --- Carte Plotly ---
zone = ZONES[zone_choisie]
info = INDICATEURS[indicateur_choisi]

fig = px.scatter_mapbox(
    villes_data,
    lat="latitude",
    lon="longitude",
    size_max=18,
    color="valeur",
    size="nb_mesures",
    hover_name="ville",
    hover_data={"valeur": ":.2f", "nb_mesures": True, "latitude": False, "longitude": False},
    color_continuous_scale="RdYlBu_r" if "temp" in indicateur_choisi else "Blues",
    mapbox_style=style_carte,
    zoom=zone["zoom"],
    center={"lat": zone["lat"], "lon": zone["lon"]},
    labels={"valeur": info["unite"], "nb_mesures": "Nb mesures"},
)
fig.update_layout(
    height=650,
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    coloraxis_colorbar=dict(title=info["unite"]),
)

st.plotly_chart(fig, use_container_width=True)

st.caption(f"**{info['nom']}** — Moyenne sur la période {plage_annees[0]}-{plage_annees[1]}")

# --- Tableau récapitulatif ---
with st.expander("📋 Détail par ville"):
    villes_display = villes_data[["ville", "valeur", "nb_mesures"]].copy()
    villes_display.columns = ["Ville", info["nom"], "Nb mesures"]
    villes_display = villes_display.sort_values(by=villes_display.columns[1], ascending=False)
    st.dataframe(villes_display, use_container_width=True, hide_index=True)

# ============================================================
# FOOTER ÉQUIPE
# ============================================================
afficher_footer()

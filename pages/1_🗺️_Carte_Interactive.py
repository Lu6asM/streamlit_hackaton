import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import charger_donnees, get_stations, INDICATEURS

# ============================================================
# PAGE : CARTE INTERACTIVE
# ============================================================
st.title("🗺️ Carte Interactive des Stations Météo")
st.markdown("Visualisez les stations météorologiques de Loire-Atlantique et leurs données.")

df = charger_donnees()
stations = get_stations(df)

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

# --- Calcul des données par station pour la période ---
df_filtre = df[(df["annee"] >= plage_annees[0]) & (df["annee"] <= plage_annees[1])]

stations_data = df_filtre.groupby("station").agg(
    LAT=("latitude", "first"),
    LON=("longitude", "first"),
    valeur=(indicateur_choisi, "mean"),
    nb_mesures=("date", "count"),
).reset_index().dropna(subset=["valeur", "latitude", "longitude"])

# --- Carte Plotly ---
fig = px.scatter_mapbox(
    stations_data,
    lat="latitude",
    lon="longitude",
    size_max=15,
    color="valeur",
    size="nb_mesures",
    hover_name="station",
    hover_data={"valeur": ":.2f", "nb_mesures": True, "latitude": ":.4f", "longitude": ":.4f"},
    color_continuous_scale="RdYlBu_r" if "temp" in indicateur_choisi else "Blues",
    mapbox_style="open-street-map",
    zoom=8,
    center={"lat": 47.2, "lon": -1.6},
    title=f"{INDICATEURS[indicateur_choisi]['nom']} — Moyenne {plage_annees[0]}-{plage_annees[1]}",
    labels={"valeur": INDICATEURS[indicateur_choisi]["unite"]},
)
fig.update_layout(height=600, margin={"r": 0, "t": 40, "l": 0, "b": 0})

st.plotly_chart(fig, use_container_width=True)

# --- Tableau récapitulatif ---
st.markdown("### Détail par station")
stations_display = stations_data[["station", "valeur", "nb_mesures", "latitude", "longitude"]].copy()
stations_display.columns = ["Station", f"{INDICATEURS[indicateur_choisi]['nom']}", "Nb mesures", "Latitude", "Longitude"]
stations_display = stations_display.sort_values(by=stations_display.columns[1], ascending=False)
st.dataframe(stations_display, use_container_width=True, hide_index=True)

import pandas as pd
import streamlit as st
import os

# ============================================================
# CONFIGURATION DES INDICATEURS (noms du CSV nettoyé)
# ============================================================
INDICATEURS = {
    "temp_moyenne": {"nom": "Température moyenne (°C)", "unite": "°C", "categorie": "Évolution climatique", "color": "#FF6B35"},
    "temp_max": {"nom": "Température maximale (°C)", "unite": "°C", "categorie": "Évolution climatique", "color": "#D7263D"},
    "temp_min": {"nom": "Température minimale (°C)", "unite": "°C", "categorie": "Évolution climatique", "color": "#3B82F6"},
    "precipitations": {"nom": "Précipitations (mm)", "unite": "mm", "categorie": "Évolution climatique", "color": "#1B998B"},
    "jours_gel": {"nom": "Nb jours de gel", "unite": "jours", "categorie": "Évolution climatique", "color": "#7EC8E3"},
    "jours_chaleur_30": {"nom": "Nb jours > 30°C", "unite": "jours", "categorie": "Évolution climatique", "color": "#E63946"},
    "jours_orage": {"nom": "Nb jours d'orage", "unite": "jours", "categorie": "Événements extrêmes", "color": "#FFD166"},
    "evapotranspiration": {"nom": "Évapotranspiration (mm)", "unite": "mm", "categorie": "Événements extrêmes", "color": "#F4A261"},
}


@st.cache_data
def charger_donnees():
    """Charge et nettoie le CSV météo Loire-Atlantique (version clean)."""
    # Essai local d'abord, sinon GitHub raw
    csv_local = os.path.join(os.path.dirname(__file__), "..", "data", "meteo_44_1900_2026_clean.csv")
    csv_local = os.path.normpath(csv_local)

    if os.path.exists(csv_local):
        csv_path = csv_local
    else:
        csv_path = "https://raw.githubusercontent.com/Lu6asM/streamlit_hackaton/refs/heads/main/data/meteo_44_1900_2026_clean.csv"

    df = pd.read_csv(csv_path, sep=";", low_memory=False)

    # Conversion de la colonne date
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["annee"] = df["annee_mois"].astype(str).str[:4].astype(int)
    df["mois"] = df["annee_mois"].astype(str).str[4:6].astype(int)

    # Conversion des colonnes indicateurs en numérique
    for col in INDICATEURS.keys():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Conversion coordonnées
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Renommer station → ville pour plus de clarté
    df.rename(columns={"station": "ville"}, inplace=True)

    return df


def get_stations(df):
    """Retourne la liste des stations uniques avec leurs coordonnées."""
    stations = df.groupby("ville").agg(
        latitude=("latitude", "first"),
        longitude=("longitude", "first"),
        nb_mesures=("date", "count")
    ).reset_index()
    return stations


def get_moyennes_annuelles(df, indicateur, station=None):
    """Calcule les moyennes annuelles d'un indicateur, optionnellement pour une station."""
    data = df.copy()
    if station and station != "Toutes les villes":
        data = data[data["ville"] == station]

    moyennes = data.groupby("annee")[indicateur].mean().reset_index()
    moyennes.columns = ["annee", indicateur]
    moyennes = moyennes.dropna()
    return moyennes

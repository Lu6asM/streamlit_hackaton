import pandas as pd
import streamlit as st
import os

# ============================================================
# CONFIGURATION DES INDICATEURS
# ============================================================
INDICATEURS = {
    "TM": {"nom": "Température moyenne (°C)", "unite": "°C", "categorie": "Évolution climatique", "color": "#FF6B35"},
    "TX": {"nom": "Température maximale (°C)", "unite": "°C", "categorie": "Évolution climatique", "color": "#D7263D"},
    "TN": {"nom": "Température minimale (°C)", "unite": "°C", "categorie": "Évolution climatique", "color": "#3B82F6"},
    "RR": {"nom": "Précipitations (mm)", "unite": "mm", "categorie": "Évolution climatique", "color": "#1B998B"},
    "NBJGELEE": {"nom": "Nb jours de gel", "unite": "jours", "categorie": "Évolution climatique", "color": "#7EC8E3"},
    "NBJTX30": {"nom": "Nb jours > 30°C", "unite": "jours", "categorie": "Évolution climatique", "color": "#E63946"},
    "NBJORAG": {"nom": "Nb jours d'orage", "unite": "jours", "categorie": "Événements extrêmes", "color": "#FFD166"},
    "ETP": {"nom": "Évapotranspiration (mm)", "unite": "mm", "categorie": "Événements extrêmes", "color": "#F4A261"},
}


@st.cache_data
def charger_donnees():
    """Charge et nettoie le CSV météo Loire-Atlantique."""
    # Essai local d'abord, sinon GitHub raw
    csv_local = os.path.join(os.path.dirname(__file__), "..", "data", "meteo_44_1900_2026.csv")
    csv_local = os.path.normpath(csv_local)

    if os.path.exists(csv_local):
        csv_path = csv_local
    else:
        csv_path = "https://raw.githubusercontent.com/Lu6asM/streamlit_hackaton/refs/heads/main/data/meteo_44_1900_2026.csv"

    df = pd.read_csv(csv_path, sep=";", low_memory=False)

    # Conversion de la colonne date
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    df["annee"] = df["AAAAMM"].astype(str).str[:4].astype(int)
    df["mois"] = df["AAAAMM"].astype(str).str[4:6].astype(int)

    # Conversion des colonnes indicateurs en numérique
    for col in INDICATEURS.keys():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Conversion coordonnées
    df["LAT"] = pd.to_numeric(df["LAT"], errors="coerce")
    df["LON"] = pd.to_numeric(df["LON"], errors="coerce")

    return df


def get_stations(df):
    """Retourne la liste des stations uniques avec leurs coordonnées."""
    stations = df.groupby("NOM_USUEL").agg(
        LAT=("LAT", "first"),
        LON=("LON", "first"),
        nb_mesures=("date", "count")
    ).reset_index()
    return stations


def get_moyennes_annuelles(df, indicateur, station=None):
    """Calcule les moyennes annuelles d'un indicateur, optionnellement pour une station."""
    data = df.copy()
    if station and station != "Toutes les stations":
        data = data[data["NOM_USUEL"] == station]

    moyennes = data.groupby("annee")[indicateur].mean().reset_index()
    moyennes.columns = ["annee", indicateur]
    moyennes = moyennes.dropna()
    return moyennes

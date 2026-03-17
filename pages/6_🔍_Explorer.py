import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import charger_donnees, INDICATEURS
from utils.footer import afficher_footer

# ============================================================
# PAGE : EXPLORER LES DONNÉES
# ============================================================
st.title("🔍 Explorer les données")
st.markdown("Créez vos propres graphiques à partir du dataset météo complet.")

df = charger_donnees()

# --- Colonnes disponibles pour l'exploration ---
# On propose toutes les colonnes numériques
colonnes_numeriques = df.select_dtypes(include=[np.number]).columns.tolist()
# Exclure les colonnes techniques
colonnes_exclues = ["annee_mois", "code_station", "annee", "mois"]
colonnes_dispo = [c for c in colonnes_numeriques if c not in colonnes_exclues]

# Labels lisibles pour les colonnes connues
def label_colonne(col):
    if col in INDICATEURS:
        return INDICATEURS[col]["nom"]
    labels = {
        "annee": "Année", "mois": "Mois", "latitude": "Latitude", "longitude": "Longitude",
        "altitude": "Altitude", "jours_pluie_1mm": "Jours pluie > 1mm",
        "jours_pluie_5mm": "Jours pluie > 5mm", "jours_pluie_10mm": "Jours pluie > 10mm",
        "jours_chaleur_25": "Jours > 25°C", "jours_chaleur_35": "Jours > 35°C",
        "jours_temp_min_5": "Jours Tmin < 5°C", "jours_temp_min_10": "Jours Tmin < -10°C",
        "amplitude_thermique_moyenne": "Amplitude thermique moy.",
        "temp_moyenne_mensuelle": "Temp. moy. mensuelle",
        "humidite_moyenne": "Humidité moyenne (%)",
        "vent_moyen": "Vent moyen (m/s)", "ensoleillement": "Ensoleillement (h)",
        "pression_mer_moyenne": "Pression mer moy. (hPa)",
        "nb_mesures": "Nb mesures",
    }
    return labels.get(col, col)

# --- Sidebar ---
st.sidebar.header("Configuration du graphique")

type_graphique = st.sidebar.selectbox(
    "Type de graphique",
    options=["Ligne", "Barres", "Scatter", "Heatmap", "Boxplot", "Histogramme"],
)

# Filtres communs
villes_list = ["Toutes les villes"] + sorted(df["ville"].unique().tolist())
ville_choisie = st.sidebar.selectbox("Ville", villes_list)

annee_min = int(df["annee"].min())
annee_max = int(df["annee"].max())
plage = st.sidebar.slider("Période", annee_min, annee_max, (1950, annee_max))

# Agrégation
aggregation = st.sidebar.selectbox("Agrégation temporelle", ["Année", "Mois", "Données brutes"])

# --- Filtrage des données ---
data = df.copy()
if ville_choisie != "Toutes les villes":
    data = data[data["ville"] == ville_choisie]
data = data[(data["annee"] >= plage[0]) & (data["annee"] <= plage[1])]

# --- Agrégation ---
if aggregation == "Année":
    data_agg = data.groupby("annee")[colonnes_dispo].mean().reset_index()
    x_default = "annee"
elif aggregation == "Mois":
    data_agg = data.groupby("mois")[colonnes_dispo].mean().reset_index()
    x_default = "mois"
else:
    data_agg = data
    x_default = "annee"

# ============================================================
# CONFIGURATION AXES
# ============================================================
st.markdown("### Choisissez vos données")

col1, col2 = st.columns(2)

with col1:
    axe_x = st.selectbox(
        "Axe X",
        options=colonnes_dispo,
        index=colonnes_dispo.index(x_default) if x_default in colonnes_dispo else 0,
        format_func=label_colonne,
    )

with col2:
    default_y = "temp_moyenne" if "temp_moyenne" in colonnes_dispo else colonnes_dispo[1]
    axe_y = st.selectbox(
        "Axe Y",
        options=colonnes_dispo,
        index=colonnes_dispo.index(default_y) if default_y in colonnes_dispo else 1,
        format_func=label_colonne,
    )

# Option couleur pour scatter
couleur = None
if type_graphique == "Scatter":
    utiliser_couleur = st.checkbox("Colorer par une 3e variable")
    if utiliser_couleur:
        couleur = st.selectbox(
            "Variable de couleur",
            options=colonnes_dispo,
            format_func=label_colonne,
            key="couleur",
        )

# ============================================================
# GÉNÉRATION DU GRAPHIQUE
# ============================================================
st.markdown("---")

if data_agg.empty:
    st.warning("Aucune donnée disponible pour ces filtres.")
    st.stop()

try:
    if type_graphique == "Ligne":
        fig = px.line(
            data_agg.sort_values(axe_x), x=axe_x, y=axe_y,
            labels={axe_x: label_colonne(axe_x), axe_y: label_colonne(axe_y)},
        )
        fig.update_traces(line=dict(width=2))

    elif type_graphique == "Barres":
        fig = px.bar(
            data_agg.sort_values(axe_x), x=axe_x, y=axe_y,
            labels={axe_x: label_colonne(axe_x), axe_y: label_colonne(axe_y)},
            color=axe_y, color_continuous_scale="Viridis",
        )

    elif type_graphique == "Scatter":
        fig = px.scatter(
            data_agg, x=axe_x, y=axe_y,
            color=couleur if couleur else None,
            color_continuous_scale="Viridis" if couleur else None,
            labels={
                axe_x: label_colonne(axe_x),
                axe_y: label_colonne(axe_y),
                couleur: label_colonne(couleur) if couleur else "",
            },
            trendline="ols",
            opacity=0.6,
        )

    elif type_graphique == "Heatmap":
        # Heatmap mois × année
        if "mois" in data.columns and "annee" in data.columns:
            pivot = data.groupby(["annee", "mois"])[axe_y].mean().reset_index()
            pivot_table = pivot.pivot(index="mois", columns="annee", values=axe_y)
            mois_labels = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]

            fig = go.Figure(data=go.Heatmap(
                z=pivot_table.values,
                x=pivot_table.columns,
                y=mois_labels[:len(pivot_table.index)],
                colorscale="RdYlBu_r" if "temp" in axe_y else "Viridis",
                colorbar_title=label_colonne(axe_y),
            ))
            fig.update_layout(xaxis_title="Année", yaxis_title="Mois")
        else:
            st.warning("La heatmap nécessite des données avec année et mois.")
            st.stop()

    elif type_graphique == "Boxplot":
        # Boxplot par décennie
        data_agg["decennie"] = (data_agg["annee"] // 10 * 10).astype(str) + "s"
        fig = px.box(
            data_agg, x="decennie", y=axe_y,
            labels={"decennie": "Décennie", axe_y: label_colonne(axe_y)},
            color="decennie",
        )

    elif type_graphique == "Histogramme":
        fig = px.histogram(
            data_agg, x=axe_y, nbins=40,
            labels={axe_y: label_colonne(axe_y)},
            color_discrete_sequence=["#1B998B"],
        )
        fig.update_layout(yaxis_title="Fréquence")

    # Layout commun
    fig.update_layout(
        title=f"{label_colonne(axe_y)} — {ville_choisie} ({plage[0]}-{plage[1]})",
        height=550,
        template="plotly_dark",
        hovermode="closest",
    )

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Erreur lors de la génération du graphique : {e}")

# ============================================================
# STATISTIQUES DESCRIPTIVES
# ============================================================
with st.expander("📊 Statistiques descriptives"):
    if axe_y in data_agg.columns:
        col_stats = data_agg[axe_y].dropna()
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1:
            st.metric("Moyenne", f"{col_stats.mean():.2f}")
        with s2:
            st.metric("Médiane", f"{col_stats.median():.2f}")
        with s3:
            st.metric("Écart-type", f"{col_stats.std():.2f}")
        with s4:
            st.metric("Min", f"{col_stats.min():.2f}")
        with s5:
            st.metric("Max", f"{col_stats.max():.2f}")

# ============================================================
# EXPORT DES DONNÉES
# ============================================================
with st.expander("💾 Exporter les données filtrées"):
    st.dataframe(data_agg.head(100), use_container_width=True, hide_index=True)
    csv = data_agg.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Télécharger en CSV", csv, "export_donnees.csv", "text/csv")

# ============================================================
# FOOTER ÉQUIPE
# ============================================================
afficher_footer()
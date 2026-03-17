import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import charger_donnees, INDICATEURS

# ============================================================
# PAGE : CORRÉLATIONS ENTRE INDICATEURS
# ============================================================
st.title("🔗 Corrélations entre indicateurs")
st.markdown("Explorez les relations entre les différents indicateurs climatiques.")

df = charger_donnees()

# --- Sidebar ---
st.sidebar.header("Filtres")

stations_list = ["Toutes les stations"] + sorted(df["station"].unique().tolist())
station_choisie = st.sidebar.selectbox("Station", stations_list, key="corr_station")

annee_min = int(df["annee"].min())
annee_max = int(df["annee"].max())
plage = st.sidebar.slider("Période", annee_min, annee_max, (1950, annee_max), key="corr_plage")

# Filtrage
data = df.copy()
if station_choisie != "Toutes les stations":
    data = data[data["station"] == station_choisie]
data = data[(data["annee"] >= plage[0]) & (data["annee"] <= plage[1])]

cols_indicateurs = [c for c in INDICATEURS.keys() if c in data.columns]

tab_matrice, tab_scatter, tab_stations = st.tabs([
    "📊 Matrice de corrélation",
    "🔍 Scatter plot",
    "🏘️ Comparaison de stations",
])

# ============================================================
# ONGLET 1 : MATRICE DE CORRÉLATION
# ============================================================
with tab_matrice:
    # Moyennes annuelles pour la corrélation
    moy_ann = data.groupby("annee")[cols_indicateurs].mean().dropna()

    if len(moy_ann) < 5:
        st.warning("Pas assez de données pour calculer les corrélations.")
    else:
        corr = moy_ann.corr()

        # Renommer pour lisibilité
        labels = [INDICATEURS[c]["nom"].split("(")[0].strip() for c in corr.columns]

        fig_corr = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=labels, y=labels,
            colorscale="RdBu_r", zmin=-1, zmax=1,
            text=np.round(corr.values, 2),
            texttemplate="%{text}",
            textfont=dict(size=11),
            colorbar_title="Corrélation",
        ))
        fig_corr.update_layout(
            title="Matrice de corrélation des indicateurs (moyennes annuelles)",
            height=550, template="plotly_dark",
        )
        st.plotly_chart(fig_corr, use_container_width=True)

        st.markdown("""
        **Lecture** : une valeur proche de **+1** (rouge) = forte corrélation positive,
        **-1** (bleu) = forte corrélation négative, **0** = pas de lien linéaire.
        """)

# ============================================================
# ONGLET 2 : SCATTER PLOT
# ============================================================
with tab_scatter:
    col1, col2 = st.columns(2)
    with col1:
        ind_x = st.selectbox("Axe X", options=cols_indicateurs,
                             format_func=lambda x: INDICATEURS[x]["nom"], key="sc_x")
    with col2:
        ind_y = st.selectbox("Axe Y", options=cols_indicateurs, index=min(1, len(cols_indicateurs)-1),
                             format_func=lambda x: INDICATEURS[x]["nom"], key="sc_y")

    moy_scatter = data.groupby("annee")[cols_indicateurs].mean().reset_index().dropna(subset=[ind_x, ind_y])

    fig_sc = px.scatter(
        moy_scatter, x=ind_x, y=ind_y,
        color="annee", color_continuous_scale="Viridis",
        hover_data=["annee"],
        trendline="ols",
        labels={
            ind_x: INDICATEURS[ind_x]["nom"],
            ind_y: INDICATEURS[ind_y]["nom"],
            "annee": "Année",
        },
    )
    fig_sc.update_layout(
        title=f"{INDICATEURS[ind_x]['nom']} vs {INDICATEURS[ind_y]['nom']}",
        height=500, template="plotly_dark",
    )
    st.plotly_chart(fig_sc, use_container_width=True)

    # Calcul de la corrélation
    r = moy_scatter[ind_x].corr(moy_scatter[ind_y])
    st.info(f"**Coefficient de corrélation (Pearson)** : r = {r:.3f}")

# ============================================================
# ONGLET 3 : COMPARAISON DE STATIONS
# ============================================================
with tab_stations:
    st.markdown("Comparez jusqu'à 4 stations sur un même indicateur.")

    ind_comp = st.selectbox("Indicateur", options=cols_indicateurs,
                            format_func=lambda x: INDICATEURS[x]["nom"], key="comp_ind")

    all_stations = sorted(df["station"].unique().tolist())
    stations_choisies = st.multiselect(
        "Stations à comparer (max 4)",
        options=all_stations,
        default=all_stations[:min(3, len(all_stations))],
        max_selections=4,
    )

    if stations_choisies:
        fig_comp = go.Figure()

        colors = ["#FF6B35", "#3B82F6", "#10B981", "#F59E0B"]
        for i, station in enumerate(stations_choisies):
            data_st = df[(df["station"] == station) &
                         (df["annee"] >= plage[0]) & (df["annee"] <= plage[1])]
            moy_st = data_st.groupby("annee")[ind_comp].mean().reset_index().dropna()

            # Moyenne glissante
            moy_st["rolling"] = moy_st[ind_comp].rolling(window=10, center=True).mean()

            fig_comp.add_trace(go.Scatter(
                x=moy_st["annee"], y=moy_st["rolling"],
                mode="lines", name=station,
                line=dict(color=colors[i % len(colors)], width=2),
            ))

        fig_comp.update_layout(
            title=f"Comparaison — {INDICATEURS[ind_comp]['nom']} (moyenne glissante 10 ans)",
            xaxis_title="Année",
            yaxis_title=f"{INDICATEURS[ind_comp]['nom']} ({INDICATEURS[ind_comp]['unite']})",
            height=500, hovermode="x unified", template="plotly_dark",
        )
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Sélectionnez au moins une station.")

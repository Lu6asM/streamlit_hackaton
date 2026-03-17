import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import charger_donnees, get_stations, get_moyennes_annuelles, INDICATEURS

# ============================================================
# PAGE : VISUALISATIONS HISTORIQUES (améliorée)
# ============================================================
st.title("📊 Visualisations Historiques")
st.markdown("Analysez l'évolution des indicateurs climatiques en Loire-Atlantique depuis 1900.")

df = charger_donnees()

# Événements climatiques marquants pour annotations
EVENEMENTS = {
    2003: "Canicule 2003",
    2022: "Canicule record 2022",
    2010: "Tempête Xynthia",
    1956: "Gel historique 1956",
    1976: "Sécheresse 1976",
    2018: "Été caniculaire",
}

# --- Sidebar : filtres ---
st.sidebar.header("Filtres")

stations_list = ["Toutes les stations"] + sorted(df["NOM_USUEL"].unique().tolist())
station_choisie = st.sidebar.selectbox("Station", stations_list)

indicateurs_choisis = st.sidebar.multiselect(
    "Indicateurs à afficher",
    options=list(INDICATEURS.keys()),
    default=["TM", "RR", "NBJGELEE", "NBJTX30"],
    format_func=lambda x: INDICATEURS[x]["nom"],
)

annee_min = int(df["annee"].min())
annee_max = int(df["annee"].max())
plage = st.sidebar.slider("Période", annee_min, annee_max, (1950, annee_max))

afficher_tendance = st.sidebar.checkbox("Tendance linéaire", value=True)
afficher_moyenne_glissante = st.sidebar.checkbox("Moyenne glissante (10 ans)", value=True)
afficher_annotations = st.sidebar.checkbox("Événements marquants", value=True)

# --- Onglets ---
tab_courbes, tab_heatmap, tab_stripes, tab_comparaison = st.tabs([
    "📈 Courbes d'évolution",
    "🟥 Heatmap mensuelle",
    "🌡️ Warming Stripes",
    "⚖️ Comparaison de périodes",
])

# ============================================================
# ONGLET 1 : COURBES D'ÉVOLUTION
# ============================================================
with tab_courbes:
    if not indicateurs_choisis:
        st.warning("Sélectionnez au moins un indicateur dans la barre latérale.")
    else:
        for indicateur in indicateurs_choisis:
            moyennes = get_moyennes_annuelles(df, indicateur, station_choisie)
            moyennes = moyennes[(moyennes["annee"] >= plage[0]) & (moyennes["annee"] <= plage[1])]

            if moyennes.empty:
                st.warning(f"Pas de données pour {INDICATEURS[indicateur]['nom']}.")
                continue

            info = INDICATEURS[indicateur]
            fig = go.Figure()

            # Courbe principale
            fig.add_trace(go.Scatter(
                x=moyennes["annee"], y=moyennes[indicateur],
                mode="lines+markers", name=info["nom"],
                line=dict(color=info["color"], width=2),
                marker=dict(size=3),
            ))

            # Moyenne glissante 10 ans
            if afficher_moyenne_glissante and len(moyennes) > 10:
                moyennes["rolling"] = moyennes[indicateur].rolling(window=10, center=True).mean()
                fig.add_trace(go.Scatter(
                    x=moyennes["annee"], y=moyennes["rolling"],
                    mode="lines", name="Moyenne glissante 10 ans",
                    line=dict(color="#FBBF24", width=3),
                ))

            # Tendance linéaire
            if afficher_tendance and len(moyennes) > 2:
                x = moyennes["annee"].values
                y = moyennes[indicateur].values
                mask = ~np.isnan(y)
                if mask.sum() > 2:
                    coeffs = np.polyfit(x[mask], y[mask], 1)
                    tendance = np.polyval(coeffs, x)
                    pente = coeffs[0] * 10
                    fig.add_trace(go.Scatter(
                        x=moyennes["annee"], y=tendance,
                        mode="lines",
                        name=f"Tendance ({pente:+.2f} {info['unite']}/décennie)",
                        line=dict(color="rgba(255,80,80,0.6)", width=2, dash="dash"),
                    ))

            # Annotations événements
            if afficher_annotations:
                for annee_evt, label in EVENEMENTS.items():
                    if plage[0] <= annee_evt <= plage[1]:
                        val = moyennes[moyennes["annee"] == annee_evt][indicateur]
                        if not val.empty:
                            fig.add_annotation(
                                x=annee_evt, y=val.values[0],
                                text=label, showarrow=True,
                                arrowhead=2, arrowsize=1, arrowcolor="#EF4444",
                                font=dict(size=10, color="#EF4444"),
                                bgcolor="rgba(0,0,0,0.7)", bordercolor="#EF4444",
                            )

            fig.update_layout(
                title=f"{info['nom']} — {station_choisie} ({plage[0]}-{plage[1]})",
                xaxis_title="Année",
                yaxis_title=f"{info['nom']} ({info['unite']})",
                height=420, hovermode="x unified", template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)

# ============================================================
# ONGLET 2 : HEATMAP MENSUELLE
# ============================================================
with tab_heatmap:
    st.markdown("Visualisez un indicateur par mois et par année sous forme de heatmap.")

    ind_heatmap = st.selectbox(
        "Indicateur pour la heatmap",
        options=list(INDICATEURS.keys()),
        format_func=lambda x: INDICATEURS[x]["nom"],
        key="heatmap_ind",
    )

    data_hm = df.copy()
    if station_choisie != "Toutes les stations":
        data_hm = data_hm[data_hm["NOM_USUEL"] == station_choisie]

    data_hm = data_hm[(data_hm["annee"] >= plage[0]) & (data_hm["annee"] <= plage[1])]

    pivot = data_hm.groupby(["annee", "mois"])[ind_heatmap].mean().reset_index()
    pivot_table = pivot.pivot(index="mois", columns="annee", values=ind_heatmap)

    mois_labels = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]

    fig_hm = go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=mois_labels[:len(pivot_table.index)],
        colorscale="RdYlBu_r" if "T" in ind_heatmap else "Blues",
        colorbar_title=INDICATEURS[ind_heatmap]["unite"],
        hoverongaps=False,
    ))
    fig_hm.update_layout(
        title=f"Heatmap — {INDICATEURS[ind_heatmap]['nom']} ({plage[0]}-{plage[1]})",
        xaxis_title="Année", yaxis_title="Mois",
        height=500, template="plotly_dark",
    )
    st.plotly_chart(fig_hm, use_container_width=True)

# ============================================================
# ONGLET 3 : WARMING STRIPES
# ============================================================
with tab_stripes:
    st.markdown("""
    Les **Warming Stripes** (bandes de réchauffement) montrent l'anomalie de température
    de chaque année par rapport à la moyenne de référence 1961-1990.
    """)

    ind_stripes = st.selectbox(
        "Indicateur", options=["TM", "TX", "TN"],
        format_func=lambda x: INDICATEURS[x]["nom"], key="stripes_ind",
    )

    data_s = df.copy()
    if station_choisie != "Toutes les stations":
        data_s = data_s[data_s["NOM_USUEL"] == station_choisie]

    moy_annuelle = data_s.groupby("annee")[ind_stripes].mean().reset_index()
    moy_annuelle = moy_annuelle.dropna()

    # Référence 1961-1990
    ref = moy_annuelle[(moy_annuelle["annee"] >= 1961) & (moy_annuelle["annee"] <= 1990)][ind_stripes].mean()
    moy_annuelle["anomalie"] = moy_annuelle[ind_stripes] - ref

    # Stripes avec barres colorées
    colors = moy_annuelle["anomalie"].values
    fig_stripes = go.Figure(data=go.Bar(
        x=moy_annuelle["annee"],
        y=[1] * len(moy_annuelle),
        marker=dict(
            color=colors,
            colorscale="RdBu_r",
            cmin=-max(abs(colors)),
            cmax=max(abs(colors)),
            colorbar=dict(title="Anomalie (°C)"),
        ),
        hovertemplate="Année: %{x}<br>Anomalie: %{marker.color:.2f}°C<extra></extra>",
    ))
    fig_stripes.update_layout(
        title=f"Warming Stripes — {INDICATEURS[ind_stripes]['nom']} (réf. 1961-1990)",
        xaxis_title="Année", yaxis_visible=False,
        height=300, template="plotly_dark",
        bargap=0,
    )
    st.plotly_chart(fig_stripes, use_container_width=True)

    # Graphique anomalies détaillées
    fig_anom = go.Figure()
    fig_anom.add_trace(go.Bar(
        x=moy_annuelle["annee"], y=moy_annuelle["anomalie"],
        marker_color=["#D7263D" if v > 0 else "#3B82F6" for v in moy_annuelle["anomalie"]],
        name="Anomalie",
    ))
    fig_anom.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
    fig_anom.update_layout(
        title="Anomalies annuelles détaillées",
        xaxis_title="Année", yaxis_title="Anomalie (°C)",
        height=400, template="plotly_dark",
    )
    st.plotly_chart(fig_anom, use_container_width=True)

# ============================================================
# ONGLET 4 : COMPARAISON DE PÉRIODES
# ============================================================
with tab_comparaison:
    st.markdown("Comparez les indicateurs entre deux périodes de votre choix.")

    col1, col2 = st.columns(2)
    with col1:
        periode1 = st.slider("Période de référence", annee_min, annee_max, (1950, 1980), key="cp1")
    with col2:
        periode2 = st.slider("Période récente", annee_min, annee_max, (2000, annee_max), key="cp2")

    if indicateurs_choisis:
        comparaison = []
        for ind in indicateurs_choisis:
            data = df.copy()
            if station_choisie != "Toutes les stations":
                data = data[data["NOM_USUEL"] == station_choisie]

            moy1 = data[(data["annee"] >= periode1[0]) & (data["annee"] <= periode1[1])][ind].mean()
            moy2 = data[(data["annee"] >= periode2[0]) & (data["annee"] <= periode2[1])][ind].mean()
            delta = moy2 - moy1
            pct = (delta / abs(moy1) * 100) if moy1 != 0 else 0

            comparaison.append({
                "Indicateur": INDICATEURS[ind]["nom"],
                f"Moy. {periode1[0]}-{periode1[1]}": round(moy1, 2),
                f"Moy. {periode2[0]}-{periode2[1]}": round(moy2, 2),
                "Variation absolue": round(delta, 2),
                "Variation (%)": round(pct, 1),
            })

        df_comp = pd.DataFrame(comparaison)
        st.dataframe(df_comp, use_container_width=True, hide_index=True)

        # Export CSV
        csv = df_comp.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Exporter en CSV", csv, "comparaison_climatique.csv", "text/csv")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import charger_donnees, get_moyennes_annuelles, INDICATEURS
from utils.footer import afficher_footer

# ============================================================
# PAGE : PRÉDICTIONS IA (Prophet + ARIMA + fallback linéaire)
# ============================================================
st.title("🔮 Prédictions IA")
st.markdown("Projections climatiques basées sur les données historiques — Prophet, ARIMA et régression.")

df = charger_donnees()

# --- Sidebar : paramètres ---
st.sidebar.header("Paramètres")

indicateur_choisi = st.sidebar.selectbox(
    "Indicateur à prédire",
    options=list(INDICATEURS.keys()),
    format_func=lambda x: INDICATEURS[x]["nom"],
)

horizon = st.sidebar.selectbox("Horizon", options=[2030, 2050, 2100], index=1)

villes_list = ["Toutes les villes"] + sorted(df["ville"].unique().tolist())
ville_choisie = st.sidebar.selectbox("Ville", villes_list)

modeles_actifs = st.sidebar.multiselect(
    "Modèles à comparer",
    options=["Prophet", "ARIMA", "Régression polynomiale"],
    default=["Prophet", "Régression polynomiale"],
)

# --- Données ---
moyennes = get_moyennes_annuelles(df, indicateur_choisi, ville_choisie)
moyennes = moyennes[moyennes["annee"] >= 1950]

if moyennes.empty or len(moyennes) < 10:
    st.error("Pas assez de données pour cette station/indicateur.")
    st.stop()

info = INDICATEURS[indicateur_choisi]
annee_max_data = int(moyennes["annee"].max())
annees_futures = np.arange(annee_max_data + 1, horizon + 1)

# ============================================================
# GRAPHIQUE PRINCIPAL : COMPARAISON DES MODÈLES
# ============================================================
fig = go.Figure()

# Données historiques
fig.add_trace(go.Scatter(
    x=moyennes["annee"], y=moyennes[indicateur_choisi],
    mode="lines+markers", name="Données historiques",
    line=dict(color=info["color"], width=2), marker=dict(size=3),
))

resultats = {}  # Pour stocker les prédictions de chaque modèle

# --- PROPHET ---
if "Prophet" in modeles_actifs:
    try:
        from prophet import Prophet

        df_prophet = pd.DataFrame({
            "ds": pd.to_datetime(moyennes["annee"], format="%Y"),
            "y": moyennes[indicateur_choisi].values,
        })

        with st.spinner("Entraînement de Prophet..."):
            model_prophet = Prophet(
                yearly_seasonality=False, weekly_seasonality=False,
                daily_seasonality=False, changepoint_prior_scale=0.05,
            )
            model_prophet.fit(df_prophet)
            nb_futures = max(horizon - annee_max_data, 1)
            future = model_prophet.make_future_dataframe(periods=nb_futures, freq="YS")
            forecast = model_prophet.predict(future)
            forecast["annee"] = forecast["ds"].dt.year
            fc_futur = forecast[forecast["annee"] > annee_max_data]

        fig.add_trace(go.Scatter(
            x=fc_futur["annee"], y=fc_futur["yhat"],
            mode="lines", name="Prophet",
            line=dict(color="#9333EA", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=pd.concat([fc_futur["annee"], fc_futur["annee"][::-1]]),
            y=pd.concat([fc_futur["yhat_upper"], fc_futur["yhat_lower"][::-1]]),
            fill="toself", fillcolor="rgba(147,51,234,0.12)",
            line=dict(color="rgba(255,255,255,0)"), name="IC 95% Prophet", showlegend=False,
        ))
        resultats["Prophet"] = {int(a): round(v, 2) for a, v in zip(fc_futur["annee"], fc_futur["yhat"])}

    except ImportError:
        st.warning("Prophet non installé → `pip install prophet`")

# --- ARIMA ---
if "ARIMA" in modeles_actifs:
    try:
        from statsmodels.tsa.arima.model import ARIMA

        y_vals = moyennes[indicateur_choisi].values
        y_clean = pd.Series(y_vals).interpolate().values

        with st.spinner("Entraînement d'ARIMA..."):
            model_arima = ARIMA(y_clean, order=(2, 1, 2))
            fit_arima = model_arima.fit()
            nb_pred = max(horizon - annee_max_data, 1)
            pred_arima = fit_arima.forecast(steps=nb_pred)

        fig.add_trace(go.Scatter(
            x=annees_futures[:len(pred_arima)], y=pred_arima,
            mode="lines", name="ARIMA(2,1,2)",
            line=dict(color="#F59E0B", width=2, dash="dot"),
        ))
        resultats["ARIMA"] = {int(a): round(v, 2) for a, v in zip(annees_futures[:len(pred_arima)], pred_arima)}

    except ImportError:
        st.warning("statsmodels non installé → `pip install statsmodels`")
    except Exception as e:
        st.warning(f"Erreur ARIMA : {e}")

# --- RÉGRESSION POLYNOMIALE ---
if "Régression polynomiale" in modeles_actifs:
    x = moyennes["annee"].values
    y = moyennes[indicateur_choisi].values
    mask = ~np.isnan(y)

    if mask.sum() > 2:
        coeffs = np.polyfit(x[mask], y[mask], 2)  # degré 2
        pred_poly = np.polyval(coeffs, annees_futures)

        fig.add_trace(go.Scatter(
            x=annees_futures, y=pred_poly,
            mode="lines", name="Régression polynomiale (deg. 2)",
            line=dict(color="#10B981", width=2, dash="dashdot"),
        ))
        resultats["Régression poly."] = {int(a): round(v, 2) for a, v in zip(annees_futures, pred_poly)}

# Lignes repères
for a_repere in [2030, 2050, 2100]:
    if a_repere <= horizon:
        fig.add_vline(x=a_repere, line_dash="dot", line_color="gray", opacity=0.4,
                      annotation_text=str(a_repere))

fig.update_layout(
    title=f"Comparaison des modèles — {info['nom']} ({ville_choisie})",
    xaxis_title="Année", yaxis_title=f"{info['nom']} ({info['unite']})",
    height=550, hovermode="x unified", template="plotly_dark",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# KPI DE PROJECTION
# ============================================================
st.markdown("### Projections clés")

annees_cibles = [a for a in [2030, 2050, 2100] if a <= horizon]
cols = st.columns(len(annees_cibles))

val_actuelle = moyennes[indicateur_choisi].iloc[-5:].mean()

for i, annee_cible in enumerate(annees_cibles):
    with cols[i]:
        st.markdown(f"**📅 {annee_cible}**")
        for nom_modele, preds in resultats.items():
            if annee_cible in preds:
                delta = preds[annee_cible] - val_actuelle
                st.metric(nom_modele, f"{preds[annee_cible]:.2f} {info['unite']}", f"{delta:+.2f}")

# ============================================================
# TABLEAU COMPARATIF DÉTAILLÉ
# ============================================================
st.markdown("### Tableau comparatif")

if resultats:
    annees_affichees = sorted(set().union(*[set(p.keys()) for p in resultats.values()]))
    # Afficher tous les 5 ans pour lisibilité
    annees_affichees = [a for a in annees_affichees if a % 5 == 0 or a in annees_cibles]

    tableau = {"Année": annees_affichees}
    for nom_modele, preds in resultats.items():
        tableau[nom_modele] = [preds.get(a, None) for a in annees_affichees]

    df_tableau = pd.DataFrame(tableau)
    st.dataframe(df_tableau, use_container_width=True, hide_index=True)

    csv = df_tableau.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Exporter les prédictions", csv, "predictions_climatiques.csv", "text/csv")

# ============================================================
# FOOTER ÉQUIPE
# ============================================================
afficher_footer()

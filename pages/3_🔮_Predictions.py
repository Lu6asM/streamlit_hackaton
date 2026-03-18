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
# Avec scénarios optimiste/médian/pessimiste + métriques RMSE/MAE
# ============================================================
st.title("🔮 Prédictions IA")
st.markdown(
    "Projections climatiques basées sur les données historiques — "
    "**Prophet**, **ARIMA** et **Régression polynomiale** avec scénarios et validation croisée."
)

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

ANNEE_SPLIT = st.sidebar.slider("Année de coupure train/test", 2005, 2020, 2015)

# --- Données ---
moyennes = get_moyennes_annuelles(df, indicateur_choisi, ville_choisie)
moyennes = moyennes[moyennes["annee"] >= 1950]

if moyennes.empty or len(moyennes) < 10:
    st.error("Pas assez de données pour cette station/indicateur.")
    st.stop()

info = INDICATEURS[indicateur_choisi]
annee_max_data = int(moyennes["annee"].max())
annees_futures = np.arange(annee_max_data + 1, horizon + 1)

# --- Split train / test ---
train = moyennes[moyennes["annee"] <= ANNEE_SPLIT]
test = moyennes[moyennes["annee"] > ANNEE_SPLIT]
annees_test = test["annee"].values
y_test = test[indicateur_choisi].values


def calc_rmse(y_true, y_pred):
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    if mask.sum() == 0:
        return np.nan
    return np.sqrt(np.mean((y_true[mask] - y_pred[mask]) ** 2))


def calc_mae(y_true, y_pred):
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    if mask.sum() == 0:
        return np.nan
    return np.mean(np.abs(y_true[mask] - y_pred[mask]))


# ============================================================
# GRAPHIQUE PRINCIPAL : COMPARAISON DES MODÈLES + SCÉNARIOS
# ============================================================
fig = go.Figure()

# Données historiques
fig.add_trace(go.Scatter(
    x=moyennes["annee"], y=moyennes[indicateur_choisi],
    mode="lines+markers", name="Données historiques",
    line=dict(color=info["color"], width=2), marker=dict(size=3),
))

# Ligne de séparation train/test
fig.add_vline(
    x=ANNEE_SPLIT, line_dash="dash", line_color="white", opacity=0.5,
    annotation_text=f"Split {ANNEE_SPLIT}", annotation_position="top left",
)

resultats = {}       # {modèle: {année: valeur_médiane}}
resultats_upper = {} # {modèle: {année: valeur_optimiste}}
resultats_lower = {} # {modèle: {année: valeur_pessimiste}}
metriques = {}       # {modèle: {"RMSE": ..., "MAE": ...}}

# --- PROPHET ---
if "Prophet" in modeles_actifs:
    try:
        from prophet import Prophet
        import logging
        logging.getLogger("prophet").setLevel(logging.WARNING)
        logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

        # --- Entraînement sur TRAIN pour métriques ---
        df_train = pd.DataFrame({
            "ds": pd.to_datetime(train["annee"], format="%Y"),
            "y": train[indicateur_choisi].values,
        })

        with st.spinner("Entraînement de Prophet..."):
            # Modèle sur train → test pour métriques
            m_train = Prophet(
                yearly_seasonality=False, weekly_seasonality=False,
                daily_seasonality=False, changepoint_prior_scale=0.05,
                interval_width=0.80,
            )
            m_train.fit(df_train)
            future_test = m_train.make_future_dataframe(
                periods=max(annee_max_data - ANNEE_SPLIT, 1), freq="YS"
            )
            fc_test = m_train.predict(future_test)
            fc_test["annee"] = fc_test["ds"].dt.year
            fc_test_only = fc_test[fc_test["annee"].isin(annees_test)]

            if len(fc_test_only) > 0 and len(y_test) > 0:
                y_pred_test = fc_test_only["yhat"].values[:len(y_test)]
                metriques["Prophet"] = {
                    "RMSE": calc_rmse(y_test[:len(y_pred_test)], y_pred_test),
                    "MAE": calc_mae(y_test[:len(y_pred_test)], y_pred_test),
                }

            # Modèle complet → projections futures
            df_full = pd.DataFrame({
                "ds": pd.to_datetime(moyennes["annee"], format="%Y"),
                "y": moyennes[indicateur_choisi].values,
            })
            m_full = Prophet(
                yearly_seasonality=False, weekly_seasonality=False,
                daily_seasonality=False, changepoint_prior_scale=0.05,
                interval_width=0.80,
            )
            m_full.fit(df_full)
            nb_futures = max(horizon - annee_max_data, 1)
            future = m_full.make_future_dataframe(periods=nb_futures, freq="YS")
            forecast = m_full.predict(future)
            forecast["annee"] = forecast["ds"].dt.year
            fc_futur = forecast[forecast["annee"] > annee_max_data]

        # Médian (yhat)
        fig.add_trace(go.Scatter(
            x=fc_futur["annee"], y=fc_futur["yhat"],
            mode="lines", name="Prophet — Médian",
            line=dict(color="#9333EA", width=2),
        ))
        # Scénario optimiste / pessimiste (IC 80%)
        fig.add_trace(go.Scatter(
            x=fc_futur["annee"], y=fc_futur["yhat_upper"],
            mode="lines", name="Prophet — Pessimiste (IC 80%)",
            line=dict(color="#9333EA", width=1, dash="dash"),
            showlegend=True,
        ))
        fig.add_trace(go.Scatter(
            x=fc_futur["annee"], y=fc_futur["yhat_lower"],
            mode="lines", name="Prophet — Optimiste (IC 80%)",
            line=dict(color="#9333EA", width=1, dash="dash"),
            showlegend=True,
            fill="tonexty", fillcolor="rgba(147,51,234,0.10)",
        ))

        resultats["Prophet"] = {int(a): round(v, 2) for a, v in zip(fc_futur["annee"], fc_futur["yhat"])}
        resultats_upper["Prophet"] = {int(a): round(v, 2) for a, v in zip(fc_futur["annee"], fc_futur["yhat_upper"])}
        resultats_lower["Prophet"] = {int(a): round(v, 2) for a, v in zip(fc_futur["annee"], fc_futur["yhat_lower"])}

    except ImportError:
        st.warning("Prophet non installé → `pip install prophet`")

# --- ARIMA ---
if "ARIMA" in modeles_actifs:
    try:
        from statsmodels.tsa.arima.model import ARIMA

        y_train_vals = pd.Series(train[indicateur_choisi].values).interpolate().values
        y_full_vals = pd.Series(moyennes[indicateur_choisi].values).interpolate().values

        with st.spinner("Entraînement d'ARIMA..."):
            # Train → test pour métriques
            m_arima_train = ARIMA(y_train_vals, order=(2, 1, 2))
            fit_train = m_arima_train.fit()
            nb_test = len(y_test)
            fc_arima_test = fit_train.get_forecast(steps=nb_test)
            pred_test_arima = fc_arima_test.predicted_mean

            if len(pred_test_arima) > 0:
                metriques["ARIMA"] = {
                    "RMSE": calc_rmse(y_test[:len(pred_test_arima)], pred_test_arima[:len(y_test)]),
                    "MAE": calc_mae(y_test[:len(pred_test_arima)], pred_test_arima[:len(y_test)]),
                }

            # Modèle complet → projections futures avec IC
            m_arima_full = ARIMA(y_full_vals, order=(2, 1, 2))
            fit_full = m_arima_full.fit()
            nb_pred = max(horizon - annee_max_data, 1)
            fc_arima = fit_full.get_forecast(steps=nb_pred)
            pred_arima = fc_arima.predicted_mean
            ci_arima = fc_arima.conf_int(alpha=0.20)  # IC 80%

        ann_fut = annees_futures[:len(pred_arima)]

        # Médian
        fig.add_trace(go.Scatter(
            x=ann_fut, y=pred_arima,
            mode="lines", name="ARIMA(2,1,2) — Médian",
            line=dict(color="#F59E0B", width=2, dash="dot"),
        ))
        # IC 80% — conf_int retourne un ndarray (n, 2)
        ci_arr = np.asarray(ci_arima)
        ci_lower = ci_arr[:, 0]
        ci_upper = ci_arr[:, 1]
        fig.add_trace(go.Scatter(
            x=ann_fut, y=ci_upper[:len(ann_fut)],
            mode="lines", name="ARIMA — Pessimiste (IC 80%)",
            line=dict(color="#F59E0B", width=1, dash="dash"),
        ))
        fig.add_trace(go.Scatter(
            x=ann_fut, y=ci_lower[:len(ann_fut)],
            mode="lines", name="ARIMA — Optimiste (IC 80%)",
            line=dict(color="#F59E0B", width=1, dash="dash"),
            fill="tonexty", fillcolor="rgba(245,158,11,0.10)",
        ))

        resultats["ARIMA"] = {int(a): round(v, 2) for a, v in zip(ann_fut, pred_arima)}
        resultats_upper["ARIMA"] = {int(a): round(v, 2) for a, v in zip(ann_fut, ci_upper[:len(ann_fut)])}
        resultats_lower["ARIMA"] = {int(a): round(v, 2) for a, v in zip(ann_fut, ci_lower[:len(ann_fut)])}

    except ImportError:
        st.warning("statsmodels non installé → `pip install statsmodels`")
    except Exception as e:
        st.warning(f"Erreur ARIMA : {e}")

# --- RÉGRESSION POLYNOMIALE ---
if "Régression polynomiale" in modeles_actifs:
    x_train = train["annee"].values
    y_train_poly = train[indicateur_choisi].values
    mask_train = ~np.isnan(y_train_poly)

    x_full = moyennes["annee"].values
    y_full_poly = moyennes[indicateur_choisi].values
    mask_full = ~np.isnan(y_full_poly)

    if mask_train.sum() > 2 and mask_full.sum() > 2:
        # Train → test pour métriques
        coeffs_train = np.polyfit(x_train[mask_train], y_train_poly[mask_train], 2)
        pred_poly_test = np.polyval(coeffs_train, annees_test)
        metriques["Régression poly."] = {
            "RMSE": calc_rmse(y_test, pred_poly_test[:len(y_test)]),
            "MAE": calc_mae(y_test, pred_poly_test[:len(y_test)]),
        }

        # Modèle complet → projections futures
        coeffs_full = np.polyfit(x_full[mask_full], y_full_poly[mask_full], 2)
        pred_poly = np.polyval(coeffs_full, annees_futures)

        # Estimation d'IC basée sur résidus historiques
        residus = y_full_poly[mask_full] - np.polyval(coeffs_full, x_full[mask_full])
        std_res = np.std(residus)
        # IC s'élargit avec le temps (incertitude croissante)
        years_ahead = annees_futures - annee_max_data
        ic_width = 1.28 * std_res * np.sqrt(1 + years_ahead / len(x_full))  # ~IC 80%

        fig.add_trace(go.Scatter(
            x=annees_futures, y=pred_poly,
            mode="lines", name="Régression poly. — Médian",
            line=dict(color="#10B981", width=2, dash="dashdot"),
        ))
        fig.add_trace(go.Scatter(
            x=annees_futures, y=pred_poly + ic_width,
            mode="lines", name="Régr. poly. — Pessimiste",
            line=dict(color="#10B981", width=1, dash="dash"),
        ))
        fig.add_trace(go.Scatter(
            x=annees_futures, y=pred_poly - ic_width,
            mode="lines", name="Régr. poly. — Optimiste",
            line=dict(color="#10B981", width=1, dash="dash"),
            fill="tonexty", fillcolor="rgba(16,185,129,0.10)",
        ))

        resultats["Régression poly."] = {int(a): round(v, 2) for a, v in zip(annees_futures, pred_poly)}
        resultats_upper["Régression poly."] = {int(a): round(v, 2) for a, v in zip(annees_futures, pred_poly + ic_width)}
        resultats_lower["Régression poly."] = {int(a): round(v, 2) for a, v in zip(annees_futures, pred_poly - ic_width)}

# Lignes repères
for a_repere in [2030, 2050, 2100]:
    if a_repere <= horizon:
        fig.add_vline(x=a_repere, line_dash="dot", line_color="gray", opacity=0.4,
                      annotation_text=str(a_repere))

fig.update_layout(
    title=f"Comparaison des modèles — {info['nom']} ({ville_choisie})",
    xaxis_title="Année", yaxis_title=f"{info['nom']} ({info['unite']})",
    height=600, hovermode="x unified", template="plotly_dark",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=10)),
)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# SCÉNARIOS : PROJECTIONS OPTIMISTE / MÉDIAN / PESSIMISTE
# ============================================================
st.markdown("### 🎯 Scénarios de projection")
st.caption("Basés sur les intervalles de confiance à 80% de chaque modèle.")

annees_cibles = [horizon]
val_actuelle = moyennes[indicateur_choisi].iloc[-5:].mean()

for annee_cible in annees_cibles:
    st.markdown(f"#### 📅 Horizon {annee_cible}")
    cols = st.columns(len(resultats) if resultats else 1)

    for i, (nom_modele, preds) in enumerate(resultats.items()):
        with cols[i]:
            if annee_cible in preds:
                val_med = preds[annee_cible]
                val_up = resultats_upper.get(nom_modele, {}).get(annee_cible)
                val_low = resultats_lower.get(nom_modele, {}).get(annee_cible)
                delta = val_med - val_actuelle

                st.markdown(f"**{nom_modele}**")
                st.metric("Médian", f"{val_med:.2f} {info['unite']}", f"{delta:+.2f}")
                if val_up is not None:
                    st.metric("Pessimiste", f"{val_up:.2f} {info['unite']}", help="Borne haute IC 80%")
                if val_low is not None:
                    st.metric("Optimiste", f"{val_low:.2f} {info['unite']}", help="Borne basse IC 80%")

# ============================================================
# MÉTRIQUES DE VALIDATION : RMSE & MAE (train/test split)
# ============================================================
st.markdown("---")
st.markdown("### 📐 Évaluation des modèles (RMSE & MAE)")
st.caption(
    f"Validation sur la période **{ANNEE_SPLIT + 1}–{annee_max_data}** "
    f"(entraînement sur 1950–{ANNEE_SPLIT})."
)

if metriques:
    # Tableau comparatif
    df_metriques = pd.DataFrame(metriques).T
    df_metriques.index.name = "Modèle"
    df_metriques = df_metriques.round(4)

    col_tab, col_viz = st.columns([1, 2])

    with col_tab:
        st.dataframe(df_metriques, use_container_width=True)
        # Meilleur modèle
        best_rmse = df_metriques["RMSE"].idxmin()
        best_mae = df_metriques["MAE"].idxmin()
        if best_rmse == best_mae:
            st.success(f"✅ **{best_rmse}** est le meilleur modèle sur les deux métriques.")
        else:
            st.info(f"🏆 Meilleur RMSE : **{best_rmse}** — Meilleur MAE : **{best_mae}**")

    with col_viz:
        # Graphique barres groupées RMSE / MAE
        fig_metrics = make_subplots(rows=1, cols=2, subplot_titles=["RMSE", "MAE"])

        colors_models = {"Prophet": "#9333EA", "ARIMA": "#F59E0B", "Régression poly.": "#10B981"}
        modeles_list = list(metriques.keys())

        fig_metrics.add_trace(go.Bar(
            x=modeles_list,
            y=[metriques[m]["RMSE"] for m in modeles_list],
            marker_color=[colors_models.get(m, "#6B7280") for m in modeles_list],
            text=[f"{metriques[m]['RMSE']:.3f}" for m in modeles_list],
            textposition="outside", name="RMSE", showlegend=False,
        ), row=1, col=1)

        fig_metrics.add_trace(go.Bar(
            x=modeles_list,
            y=[metriques[m]["MAE"] for m in modeles_list],
            marker_color=[colors_models.get(m, "#6B7280") for m in modeles_list],
            text=[f"{metriques[m]['MAE']:.3f}" for m in modeles_list],
            textposition="outside", name="MAE", showlegend=False,
        ), row=1, col=2)

        fig_metrics.update_layout(
            height=350, template="plotly_dark",
            title_text="Comparaison des erreurs de prédiction",
            margin=dict(t=80),
        )
        st.plotly_chart(fig_metrics, use_container_width=True)

    # Explication pédagogique
    with st.expander("ℹ️ Comment lire ces métriques ?"):
        st.markdown("""
**RMSE** (Root Mean Squared Error) : Erreur quadratique moyenne. Pénalise davantage les grosses erreurs.
Plus la valeur est basse, meilleur est le modèle.

**MAE** (Mean Absolute Error) : Erreur absolue moyenne. Donne le même poids à toutes les erreurs.
Plus intuitive : correspond à l'écart moyen entre prédiction et réalité.

**Intervalle de confiance à 80%** : Il y a 80% de chances que la valeur future se situe dans
l'enveloppe affichée. La borne haute représente le scénario pessimiste (réchauffement plus fort),
la borne basse le scénario optimiste.

**Train/test split** : Les modèles sont entraînés sur les données historiques jusqu'en """ + str(ANNEE_SPLIT) + """,
puis évalués sur les données réelles de """ + str(ANNEE_SPLIT + 1) + """ à """ + str(annee_max_data) + """.
Cela donne une estimation réaliste de la fiabilité des projections.
        """)
else:
    st.info("Sélectionnez au moins un modèle pour voir les métriques de validation.")

# ============================================================
# TABLEAU COMPARATIF DÉTAILLÉ
# ============================================================
st.markdown("---")
st.markdown("### 📋 Tableau comparatif détaillé")

if resultats:
    annees_affichees = sorted(set().union(*[set(p.keys()) for p in resultats.values()]))
    annees_affichees = [a for a in annees_affichees if a % 5 == 0 or a in annees_cibles]

    tableau = {"Année": annees_affichees}
    for nom_modele, preds in resultats.items():
        tableau[f"{nom_modele} (médian)"] = [preds.get(a, None) for a in annees_affichees]
        if nom_modele in resultats_upper:
            tableau[f"{nom_modele} (pessim.)"] = [resultats_upper[nom_modele].get(a, None) for a in annees_affichees]
        if nom_modele in resultats_lower:
            tableau[f"{nom_modele} (optim.)"] = [resultats_lower[nom_modele].get(a, None) for a in annees_affichees]

    df_tableau = pd.DataFrame(tableau)
    st.dataframe(df_tableau, use_container_width=True, hide_index=True)

    csv = df_tableau.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Exporter les prédictions", csv, "predictions_climatiques.csv", "text/csv")

# ============================================================
# FOOTER ÉQUIPE
# ============================================================
afficher_footer()

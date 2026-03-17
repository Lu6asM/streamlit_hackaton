import streamlit as st

# ============================================================
# CONFIGURATION GÉNÉRALE
# ============================================================
st.set_page_config(
    page_title="🌍 Changement Climatique - Loire-Atlantique (44)",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.footer import afficher_footer

# ============================================================
# PAGE D'ACCUEIL
# ============================================================
st.markdown("# 🌍 Observatoire du Changement Climatique")

# KPI rapides
from utils.data_loader import charger_donnees, INDICATEURS
df = charger_donnees()

st.markdown("### 📊 Aperçu rapide — Évolution entre 1950-1980 et 2010-2026")

annees_recentes = df[df["annee"] >= 2010]
annees_anciennes = df[(df["annee"] >= 1950) & (df["annee"] < 1980)]

c1, c2, c3, c4 = st.columns(4)

tm_recent = annees_recentes["temp_moyenne"].mean()
tm_ancien = annees_anciennes["temp_moyenne"].mean()
delta_tm = tm_recent - tm_ancien if tm_ancien and tm_recent else 0

gel_recent = annees_recentes["jours_gel"].mean()
gel_ancien = annees_anciennes["jours_gel"].mean()
delta_gel = gel_recent - gel_ancien if gel_ancien and gel_recent else 0

canicule_recent = annees_recentes["jours_chaleur_30"].mean()
canicule_ancien = annees_anciennes["jours_chaleur_30"].mean()
delta_canicule = canicule_recent - canicule_ancien if canicule_ancien and canicule_recent else 0

rr_recent = annees_recentes["precipitations"].mean()
rr_ancien = annees_anciennes["precipitations"].mean()
delta_rr = rr_recent - rr_ancien if rr_ancien and rr_recent else 0

with c1:
    st.metric("🌡️ Temp. moyenne", f"{tm_recent:.1f}°C", f"{delta_tm:+.1f}°C")
with c2:
    st.metric("❄️ Jours de gel/mois", f"{gel_recent:.1f}", f"{delta_gel:+.1f}")
with c3:
    st.metric("🔥 Jours >30°C/mois", f"{canicule_recent:.1f}", f"{delta_canicule:+.1f}")
with c4:
    st.metric("🌧️ Précipitations", f"{rr_recent:.0f} mm", f"{delta_rr:+.0f} mm")

st.markdown("---")

# Navigation rapide
st.markdown("### 🧭 Navigation")

nav1, nav2, nav3 = st.columns(3)
with nav1:
    st.page_link("pages/1_🗺️_Carte_Interactive.py", label="Carte Interactive", icon="🗺️")
    st.page_link("pages/2_📊_Historique.py", label="Visualisations Historiques", icon="📊")
with nav2:
    st.page_link("pages/3_🔮_Predictions.py", label="Prédictions IA", icon="🔮")
    st.page_link("pages/4_💡_Preconisations.py", label="Préconisations", icon="💡")
with nav3:
    st.page_link("pages/5_🔗_Correlations.py", label="Corrélations", icon="🔗")
    st.page_link("pages/6_🔍_Explorer.py", label="Explorer les données", icon="🔍")

st.markdown("---")

col_intro1, col_intro2 = st.columns([2, 1])

with col_intro1:
    st.markdown("""
    Ce tableau de bord analyse **126 ans de données météorologiques** sur le département
    de la Loire-Atlantique pour comprendre et anticiper les effets du changement climatique.

    Il s'appuie sur les données ouvertes de **Météo-France**, couvrant des dizaines de
    stations réparties sur tout le département, et utilise des modèles d'IA (Prophet, ARIMA)
    pour projeter l'évolution climatique jusqu'en 2100.
    """)

with col_intro2:
    st.markdown("""
    **8 indicateurs suivis :**
    - Température moyenne, min, max
    - Précipitations
    - Jours de gel
    - Jours de canicule (>30°C)
    - Jours d'orage
    - Évapotranspiration
    """)

st.markdown("---")

st.caption("Loire-Atlantique (44) — Données Météo-France de 1900 à 2026")

afficher_footer()

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

# ============================================================
# PAGE D'ACCUEIL
# ============================================================
st.title("🌍 Observatoire du Changement Climatique")
st.subheader("Loire-Atlantique (44) — 1900 à 2026")

st.markdown("---")

st.markdown("""
### Bienvenue sur le dashboard interactif

Ce tableau de bord analyse **126 ans de données météorologiques** sur le département
de la Loire-Atlantique pour comprendre et anticiper les effets du changement climatique.

**Naviguez via le menu latéral** pour accéder aux différentes sections :
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    🗺️ **Carte Interactive**
    Explorez les stations météo et leurs données géolocalisées.

    📊 **Visualisations Historiques**
    Analysez l'évolution des 8 indicateurs climatiques depuis 1900.
    """)

with col2:
    st.markdown("""
    🤖 **Prédictions IA (Prophet)**
    Projections climatiques pour 2030, 2050 et 2100.

    💡 **Préconisations Citoyennes**
    Recommandations adaptées au territoire basées sur les projections.
    """)

st.markdown("---")

# KPI rapides
from utils.data_loader import charger_donnees, INDICATEURS
df = charger_donnees()

st.markdown("### Aperçu rapide")

c1, c2, c3, c4 = st.columns(4)

# Calcul des KPI
annees_recentes = df[df["annee"] >= 2010]
annees_anciennes = df[(df["annee"] >= 1950) & (df["annee"] < 1980)]

tm_recent = annees_recentes["TM"].mean()
tm_ancien = annees_anciennes["TM"].mean()
delta_tm = tm_recent - tm_ancien if tm_ancien and tm_recent else 0

gel_recent = annees_recentes["NBJGELEE"].mean()
gel_ancien = annees_anciennes["NBJGELEE"].mean()
delta_gel = gel_recent - gel_ancien if gel_ancien and gel_recent else 0

canicule_recent = annees_recentes["NBJTX30"].mean()
canicule_ancien = annees_anciennes["NBJTX30"].mean()
delta_canicule = canicule_recent - canicule_ancien if canicule_ancien and canicule_recent else 0

rr_recent = annees_recentes["RR"].mean()
rr_ancien = annees_anciennes["RR"].mean()
delta_rr = rr_recent - rr_ancien if rr_ancien and rr_recent else 0

with c1:
    st.metric("🌡️ Temp. moyenne", f"{tm_recent:.1f}°C", f"{delta_tm:+.1f}°C vs 1950-80")
with c2:
    st.metric("❄️ Jours de gel/mois", f"{gel_recent:.1f}", f"{delta_gel:+.1f} vs 1950-80")
with c3:
    st.metric("🔥 Jours >30°C/mois", f"{canicule_recent:.1f}", f"{delta_canicule:+.1f} vs 1950-80")
with c4:
    st.metric("🌧️ Précipitations", f"{rr_recent:.0f} mm", f"{delta_rr:+.0f} mm vs 1950-80")

st.markdown("---")
st.caption("Hackathon 2026 — Sup de Vinci — Données Météo-France")

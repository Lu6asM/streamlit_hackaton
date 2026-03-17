import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import charger_donnees, INDICATEURS
from utils.footer import afficher_footer

# ============================================================
# PAGE : PRÉCONISATIONS CITOYENNES
# ============================================================
st.title("💡 Préconisations Citoyennes")
st.markdown("""
Recommandations adaptées à la **Loire-Atlantique** basées sur l'analyse des données climatiques
et les projections du modèle Prophet. Sources : GIEC AR6, PNACC-3, Earth Action Report.
""")

df = charger_donnees()

# --- Calcul des tendances pour alimenter les préconisations ---
annees_ref = df[(df["annee"] >= 1950) & (df["annee"] < 1980)]
annees_recentes = df[df["annee"] >= 2010]

def calcul_tendance(col):
    moy_ref = annees_ref[col].mean()
    moy_rec = annees_recentes[col].mean()
    return moy_ref, moy_rec, moy_rec - moy_ref

# ============================================================
# SECTION 1 : ÉTAT DES LIEUX
# ============================================================
st.markdown("---")
st.markdown("## 📋 État des lieux climatique")

col1, col2, col3, col4 = st.columns(4)

ref_tm, rec_tm, delta_tm = calcul_tendance("temp_moyenne")
ref_gel, rec_gel, delta_gel = calcul_tendance("jours_gel")
ref_can, rec_can, delta_can = calcul_tendance("jours_chaleur_30")
ref_rr, rec_rr, delta_rr = calcul_tendance("precipitations")

with col1:
    st.metric("🌡️ Température moy.", f"{rec_tm:.1f}°C", f"{delta_tm:+.1f}°C")
with col2:
    st.metric("❄️ Jours de gel", f"{rec_gel:.1f}/mois", f"{delta_gel:+.1f}")
with col3:
    st.metric("🔥 Jours >30°C", f"{rec_can:.1f}/mois", f"{delta_can:+.1f}")
with col4:
    st.metric("🌧️ Précipitations", f"{rec_rr:.0f} mm", f"{delta_rr:+.0f} mm")

# ============================================================
# SECTION 2 : PRÉCONISATIONS PAR THÉMATIQUE
# ============================================================
st.markdown("---")
st.markdown("## 🎯 Préconisations par thématique")

# --- Chaleur & Canicule ---
with st.expander("🔥 **Chaleur & Canicules** — Adaptation aux vagues de chaleur", expanded=True):
    st.markdown(f"""
    **Constat** : Les jours dépassant 30°C ont augmenté de **{delta_can:+.1f} jours/mois** en moyenne
    par rapport à la période 1950-1980.

    **Préconisations :**

    **Pour les citoyens :**
    - Adapter son logement : isolation thermique, stores extérieurs, ventilation naturelle
    - Identifier les îlots de fraîcheur dans sa commune (parcs, plans d'eau, bâtiments climatisés)
    - Adopter des pratiques de jardinage résilientes (paillage, arrosage matinal, espèces adaptées)
    - Protéger les personnes vulnérables (personnes âgées, jeunes enfants)

    **Pour les collectivités :**
    - Développer la végétalisation urbaine et les trames vertes
    - Installer des fontaines et brumisateurs dans les espaces publics
    - Mettre en place des Plans Communaux de Sauvegarde canicule
    - Favoriser les matériaux à forte albédo dans la construction

    *Sources : PNACC-3, GIEC AR6 WG2 Chapitre 13*
    """)

# --- Gel & Froid ---
with st.expander("❄️ **Gel & Froid** — Disparition progressive du gel"):
    st.markdown(f"""
    **Constat** : Le nombre de jours de gel a diminué de **{abs(delta_gel):.1f} jours/mois** en moyenne.

    **Préconisations :**

    **Pour l'agriculture :**
    - Anticiper la modification des cycles de culture (floraison plus précoce, risque de gel tardif)
    - Diversifier les cultures en intégrant des espèces méditerranéennes
    - Surveiller l'apparition de nouveaux parasites liés au recul du gel

    **Pour la biodiversité :**
    - Protéger les espèces locales sensibles au réchauffement
    - Surveiller les espèces invasives favorisées par des hivers plus doux
    - Préserver les zones humides essentielles à la régulation thermique

    *Sources : GIEC AR6, Observatoire National des Effets du Réchauffement Climatique*
    """)

# --- Précipitations ---
with st.expander("🌧️ **Précipitations** — Évolution du régime pluviométrique"):
    st.markdown(f"""
    **Constat** : Les précipitations moyennes ont évolué de **{delta_rr:+.0f} mm/mois**.
    La tendance est à l'intensification des épisodes pluvieux et à l'allongement des périodes sèches.

    **Préconisations :**

    **Gestion de l'eau :**
    - Installer des systèmes de récupération d'eau de pluie (cuves, jardins de pluie)
    - Réduire l'imperméabilisation des sols (débitumer, favoriser les revêtements perméables)
    - Adopter une consommation d'eau sobre : récupération, réutilisation

    **Prévention des risques :**
    - Vérifier les zones inondables de sa commune (via Géorisques)
    - Ne pas construire en zone d'expansion de crues
    - Entretenir les cours d'eau et les systèmes de drainage

    *Sources : PNACC-3, Agence de l'Eau Loire-Bretagne*
    """)

# --- Sécheresse & Évapotranspiration ---
with st.expander("☀️ **Sécheresse & Évapotranspiration** — Stress hydrique croissant"):
    ref_etp, rec_etp, delta_etp = calcul_tendance("evapotranspiration")
    st.markdown(f"""
    **Constat** : L'évapotranspiration (indicateur de sécheresse) a évolué de **{delta_etp:+.1f} mm/mois**.
    La demande en eau des sols et de la végétation augmente.

    **Préconisations :**

    **Agriculture :**
    - Transition vers l'agroécologie et les techniques de conservation des sols
    - Développer l'irrigation raisonnée (goutte-à-goutte, capteurs d'humidité)
    - Planter des haies brise-vent pour limiter l'évaporation

    **Quotidien :**
    - Réduire sa consommation d'eau potable
    - Favoriser les espèces végétales méditerranéennes résistantes à la sécheresse
    - Participer aux actions communales de préservation des nappes phréatiques

    *Sources : GIEC AR6, Earth Action Report*
    """)

# --- Événements extrêmes ---
with st.expander("⛈️ **Événements extrêmes** — Orages et phénomènes violents"):
    ref_orag, rec_orag, delta_orag = calcul_tendance("jours_orage")
    st.markdown(f"""
    **Constat** : L'évolution des jours d'orage est de **{delta_orag:+.1f} jours/mois** en moyenne.
    Les événements extrêmes (tempêtes, orages violents) tendent à s'intensifier.

    **Préconisations :**

    - Renforcer la résilience des habitations (toitures, ouvertures, drainage)
    - S'inscrire aux alertes Vigilance Météo-France
    - Connaître les gestes de mise en sécurité (PCS communal)
    - Vérifier son contrat d'assurance habitation (couverture catastrophe naturelle)

    *Sources : PNACC-3, Météo-France*
    """)

# ============================================================
# SECTION 3 : SYNTHÈSE & ACTIONS PRIORITAIRES
# ============================================================
st.markdown("---")
st.markdown("## ✅ Actions prioritaires pour la Loire-Atlantique")

st.markdown("""
| Priorité | Action | Échéance | Portée |
|----------|--------|----------|--------|
| 🔴 Haute | Plans canicule communaux renforcés | Court terme | Collectivités |
| 🔴 Haute | Végétalisation urbaine massive | Moyen terme | Collectivités |
| 🟠 Moyenne | Transition vers l'agroécologie | Moyen terme | Agriculture |
| 🟠 Moyenne | Récupération d'eau de pluie | Court terme | Citoyens |
| 🟡 Continue | Sensibilisation au changement climatique | Permanent | Tous |
| 🟡 Continue | Suivi des indicateurs via ce dashboard | Permanent | Tous |
""")

st.markdown("---")
st.caption("Sources : GIEC AR6, PNACC-3, Earth Action Report, Météo-France — Hackathon 2026 Sup de Vinci")

# ============================================================
# FOOTER ÉQUIPE
# ============================================================
afficher_footer()

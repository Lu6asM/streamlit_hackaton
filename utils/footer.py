import streamlit as st


def afficher_footer():
    """Affiche le footer fixe avec le CSS nécessaire sur chaque page."""
    st.markdown("""
    <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #0E1117;
            border-top: 1px solid #1A1F2E;
            padding: 10px 0;
            text-align: center;
            font-size: 13px;
            color: #888;
            z-index: 999;
        }
        .footer a { color: #1B998B; text-decoration: none; }
        .main .block-container { padding-bottom: 80px; }
    </style>
    <div class="footer">
        🎓 Hackathon 2026 — Sup de Vinci |
        Fait avec ❤️ par Mbotiravo MANANTSOA · Julien BURGER · Jules BOIZIAU · Lucas MEIRELES · Siméon BEURET · Ahmed Mounir PEKASSA NGOUPAYOU · Thomas MABED |
        <a href="https://github.com/Lu6asM/streamlit_hackaton" target="_blank">GitHub</a>
    </div>
    """, unsafe_allow_html=True)

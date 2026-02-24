import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db
from auth import login_page, logout, require_auth

st.set_page_config(
    page_title="Petrobras / Senai EaD",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&display=swap');

*, html, body { font-family: 'Sora', sans-serif !important; }

/* ── Page background ── */
.stApp { background: #0f1117 !important; }
.block-container { padding-top: 1.2rem !important; padding-bottom: 2rem !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #161b27 !important;
    border-right: 1px solid #1e2740;
}
[data-testid="stSidebar"] * { color: #c8d6f0 !important; }
[data-testid="stSidebarContent"] { padding: 0 !important; }

/* Sidebar logo */
.sb-logo {
    padding: 1.4rem 1.2rem 1rem;
    border-bottom: 1px solid #1e2740;
    margin-bottom: 0.5rem;
}
.sb-logo-top { font-size: 0.68rem; color: #4a7fa5 !important; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 0.3rem; }
.sb-logo-title { font-size: 1.15rem; font-weight: 700; color: #e2f0ff !important; letter-spacing: -0.3px; }
.sb-logo-sub { font-size: 0.7rem; color: #4a6a8a !important; margin-top: 0.15rem; }

/* User chip */
.sb-user {
    margin: 0.6rem 1rem 0.8rem;
    background: #1a2236;
    border: 1px solid #243050;
    border-radius: 10px;
    padding: 0.65rem 0.9rem;
    display: flex; align-items: center; gap: 0.6rem;
}
.sb-avatar {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 700; flex-shrink: 0;
    color: #fff !important;
}
.sb-uname { font-size: 0.82rem; font-weight: 600; color: #ddeeff !important; }
.sb-urole { font-size: 0.68rem; color: #5a7a9a !important; text-transform: uppercase; letter-spacing: 0.06em; }

/* Nav label */
.sb-nav-label {
    font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.15em;
    color: #2e4a6a !important; padding: 0.8rem 1.2rem 0.3rem; font-weight: 600;
}

/* Radio nav */
[data-testid="stSidebar"] .stRadio > label { display: none !important; }
[data-testid="stSidebar"] .stRadio > div { flex-direction: column !important; gap: 0.1rem !important; padding: 0 0.7rem; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    display: flex !important; align-items: center !important;
    padding: 0.6rem 0.9rem !important; border-radius: 8px !important;
    font-size: 0.88rem !important; font-weight: 500 !important;
    cursor: pointer !important; transition: background 0.12s !important;
    color: #8aabcc !important;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background: #1a2a3d !important; color: #c8e0f8 !important;
}
[data-testid="stSidebar"] [data-baseweb="radio"] input:checked ~ * { color: #60a5fa !important; }

/* ── Metrics ── */
[data-testid="metric-container"] {
    border-radius: 12px !important; padding: 1.1rem 1.3rem !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3) !important;
    border: 1px solid !important;
}
[data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { font-size: 0.8rem !important; font-weight: 500 !important; opacity: 0.85; }
[data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px !important; font-weight: 600 !important;
    transition: all 0.15s !important; border: none !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: white !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(37,99,235,0.45) !important;
}
.stButton > button[kind="secondary"] {
    background: #1a2236 !important; color: #8aabcc !important;
    border: 1px solid #2a3a54 !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #161b27 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 12px !important;
    margin-bottom: 0.5rem !important;
}
[data-testid="stExpander"] summary { color: #c8d6f0 !important; font-weight: 600 !important; }

/* ── Selectbox / text input ── */
[data-testid="stSelectbox"], [data-testid="stTextInput"], .stTextArea textarea {
    background: #1a2236 !important; color: #c8d6f0 !important;
    border: 1px solid #2a3a54 !important; border-radius: 8px !important;
}

/* ── Form ── */
[data-testid="stForm"] {
    background: #161b27 !important; border: 1px solid #1e2d45 !important;
    border-radius: 14px !important; padding: 1.5rem !important;
}

/* ── Dividers ── */
hr { border-color: #1e2740 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 2px solid #1e2d45 !important; }
.stTabs [data-baseweb="tab"] { color: #5a7a9a !important; font-weight: 600 !important; }
.stTabs [aria-selected="true"] { color: #60a5fa !important; border-bottom: 2px solid #60a5fa !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f1117; }
::-webkit-scrollbar-thumb { background: #2a3a54; border-radius: 3px; }

/* ── Hide branding ── */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden !important; }

/* ── General text ── */
h1,h2,h3,h4,h5,p,span,div,label { color: #c8d6f0; }
.stMarkdown p { color: #a0b8d0; }
</style>
""", unsafe_allow_html=True)

init_db()

if not require_auth():
    login_page()
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-logo">
        <div class="sb-logo-top">🛢️ Petrobras</div>
        <div class="sb-logo-title">Senai EaD</div>
        <div class="sb-logo-sub">Plataforma de Gestão de Projetos</div>
    </div>
    """, unsafe_allow_html=True)

    role = st.session_state.get("user_role", "colaborador")
    nome = st.session_state.get("user_nome", "Usuário")
    color = st.session_state.get("user_color", "#2563eb")
    initials = "".join(p[0].upper() for p in nome.split()[:2])
    role_label = {"admin": "Administrador", "gestor": "Gestor", "colaborador": "Colaborador"}.get(role, role)

    st.markdown(f"""
    <div class="sb-user">
        <div class="sb-avatar" style="background:{color}">{initials}</div>
        <div>
            <div class="sb-uname">{nome}</div>
            <div class="sb-urole">{role_label}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-nav-label">Menu</div>', unsafe_allow_html=True)

    page = st.radio("nav", [
        "📊  Dashboard",
        "📋  Projetos",
        "🗂️  Kanban",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div class="sb-nav-label">Conta</div>', unsafe_allow_html=True)
    if st.button("⬡  Sair", use_container_width=True):
        logout()

    st.markdown("""
    <div style="text-align:center;padding:1.5rem 0 0.5rem;font-size:0.65rem;color:#2e4a6a;">
        Petrobras / Senai EaD v2.0<br>
        <span style="opacity:0.5">Powered by Streamlit</span>
    </div>
    """, unsafe_allow_html=True)

# ── Routing ───────────────────────────────────────────────────────────────────
if "📊" in page:
    from pages import dashboard; dashboard.show()
elif "📋" in page:
    from pages import projetos; projetos.show()
elif "🗂️" in page:
    from pages import kanban; kanban.show()

import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db
from auth import login_page, logout, require_auth

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ProjectFlow",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ---------- Base ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Remove default streamlit header margin */
.block-container { padding-top: 1.5rem; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
}
[data-testid="stSidebar"] * { color: #e0e7ff !important; }

.sidebar-logo {
    text-align: center;
    padding: 1.5rem 0 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 1rem;
}
.sidebar-logo .logo-icon { font-size: 2.5rem; }
.sidebar-logo .logo-text {
    font-size: 1.4rem;
    font-weight: 700;
    color: white !important;
    margin-top: 0.25rem;
    letter-spacing: -0.5px;
}
.sidebar-logo .logo-sub {
    font-size: 0.75rem;
    color: #a5b4fc !important;
    margin-top: 0.1rem;
}

.user-badge {
    background: rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0 1rem;
    border: 1px solid rgba(255,255,255,0.15);
}
.user-badge .ub-name { font-weight: 600; font-size: 0.9rem; color: white !important; }
.user-badge .ub-role {
    font-size: 0.72rem;
    color: #a5b4fc !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.2rem;
}

.nav-section {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #818cf8 !important;
    padding: 0.75rem 0 0.3rem;
    font-weight: 600;
}

/* ---------- Radio nav buttons ---------- */
[data-testid="stSidebar"] .stRadio > div {
    flex-direction: column;
    gap: 0.2rem;
}
[data-testid="stSidebar"] .stRadio label {
    display: block;
    padding: 0.6rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.15s;
    font-size: 0.9rem;
    font-weight: 500;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div ~ div {
    background: rgba(255,255,255,0.15);
}

/* ---------- Metrics ---------- */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.85rem;
    color: #64748b;
    font-weight: 500;
}

/* ---------- Dataframe ---------- */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
}

/* ---------- Expander ---------- */
[data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    background: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 0.5rem;
}

/* ---------- Buttons ---------- */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border: none;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(99,102,241,0.4);
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 2px solid #e2e8f0;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-weight: 500;
    color: #64748b;
    border-radius: 8px 8px 0 0;
}
.stTabs [aria-selected="true"] {
    color: #6366f1 !important;
    border-bottom: 2px solid #6366f1 !important;
}

/* ---------- Forms ---------- */
[data-testid="stForm"] {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
}

/* ---------- Divider ---------- */
hr { border-color: #f1f5f9; }

/* Hide streamlit branding */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Initialize DB ─────────────────────────────────────────────────────────────
init_db()

# ── Auth check ────────────────────────────────────────────────────────────────
if not require_auth():
    login_page()
    st.stop()

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="logo-icon">🚀</div>
        <div class="logo-text">ProjectFlow</div>
        <div class="logo-sub">Gerenciamento de Projetos</div>
    </div>
    """, unsafe_allow_html=True)

    role_icons = {"admin": "👑", "gestor": "🎯", "colaborador": "👤"}
    role_icon = role_icons.get(st.session_state.get("user_role", "colaborador"), "👤")

    st.markdown(f"""
    <div class="user-badge">
        <div class="ub-name">{role_icon} {st.session_state.get("user_nome", "Usuário")}</div>
        <div class="ub-role">{st.session_state.get("user_role", "colaborador")}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="nav-section">Navegação</div>', unsafe_allow_html=True)

    page = st.radio(
        "nav",
        ["📊 Dashboard", "📁 Projetos", "✅ Tarefas", "🗂️ Kanban"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown('<div class="nav-section">Conta</div>', unsafe_allow_html=True)

    if st.button("🚪 Sair", use_container_width=True):
        logout()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; font-size:0.7rem; color:#818cf8; padding-top:1rem;">
        ProjectFlow v1.0<br>
        <span style="opacity:0.6">Powered by Streamlit</span>
    </div>
    """, unsafe_allow_html=True)

# ── Page routing ──────────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    from pages import dashboard
    dashboard.show()
elif page == "📁 Projetos":
    from pages import projetos
    projetos.show()
elif page == "✅ Tarefas":
    from pages import tarefas
    tarefas.show()
elif page == "🗂️ Kanban":
    from pages import kanban
    kanban.show()

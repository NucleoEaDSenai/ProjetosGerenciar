import streamlit as st
from database import get_db, verify_password
from models import User


def login_page():
    """Render the login page."""
    st.markdown("""
    <style>
    .login-container {
        max-width: 420px;
        margin: 0 auto;
        padding: 2rem;
    }
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .login-logo {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .login-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0;
    }
    .login-subtitle {
        color: #64748b;
        margin-top: 0.25rem;
    }
    .demo-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-top: 1.5rem;
    }
    .demo-title {
        font-weight: 600;
        color: #475569;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .demo-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        color: #64748b;
        padding: 0.2rem 0;
    }
    .demo-badge {
        background: #e0e7ff;
        color: #4338ca;
        padding: 0.1rem 0.5rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="login-header">
            <div class="login-logo">🚀</div>
            <h1 class="login-title">ProjectFlow</h1>
            <p class="login-subtitle">Gerenciamento de Projetos Institucional</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("📧 E-mail", placeholder="seu@email.com")
            senha = st.text_input("🔒 Senha", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Entrar →", use_container_width=True, type="primary")

            if submitted:
                if not email or not senha:
                    st.error("Preencha e-mail e senha.")
                else:
                    user = authenticate(email, senha)
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_id"] = user.id
                        st.session_state["user_nome"] = user.nome
                        st.session_state["user_email"] = user.email
                        st.session_state["user_role"] = user.role
                        st.session_state["user_color"] = user.avatar_color
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")

        st.markdown("""
        <div class="demo-card">
            <div class="demo-title">🔑 Contas de Demonstração</div>
            <div class="demo-row"><span>admin@demo.com / admin123</span><span class="demo-badge">Admin</span></div>
            <div class="demo-row"><span>gestor@demo.com / gestor123</span><span class="demo-badge">Gestor</span></div>
            <div class="demo-row"><span>colab@demo.com / colab123</span><span class="demo-badge">Colaborador</span></div>
        </div>
        """, unsafe_allow_html=True)


def authenticate(email: str, password: str):
    """Authenticate user and return User object or None."""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user and verify_password(password, user.senha_hash):
            return user
        return None
    finally:
        db.close()


def logout():
    """Clear session state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def require_auth():
    """Check if user is authenticated."""
    return st.session_state.get("authenticated", False)


def require_role(*roles):
    """Check if current user has required role."""
    return st.session_state.get("user_role") in roles


def get_current_user_id():
    return st.session_state.get("user_id")

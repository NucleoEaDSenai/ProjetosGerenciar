import streamlit as st
from database import get_db, verify_password
from models import User


def login_page():
    st.markdown("""
    <style>
    .stApp { background: #0a0e1a !important; }
    .login-wrap { max-width: 400px; margin: 0 auto; padding-top: 3rem; }

    .login-brand {
        text-align: center; margin-bottom: 2.5rem;
    }
    .login-brand .lb-icon { font-size: 3rem; }
    .login-brand .lb-company { font-size: 0.75rem; color: #4a7fa5; text-transform: uppercase; letter-spacing: 0.15em; margin-top: 0.5rem; }
    .login-brand .lb-title { font-size: 1.7rem; font-weight: 700; color: #e2f0ff; margin-top: 0.2rem; letter-spacing: -0.5px; }
    .login-brand .lb-sub { font-size: 0.82rem; color: #4a6a8a; margin-top: 0.3rem; }

    .demo-box {
        background: #161b27; border: 1px solid #1e2d45;
        border-radius: 12px; padding: 1rem 1.2rem; margin-top: 1.5rem;
    }
    .demo-title { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.1em; color: #4a7fa5; font-weight: 600; margin-bottom: 0.5rem; }
    .demo-row { display: flex; justify-content: space-between; align-items: center; padding: 0.25rem 0; font-size: 0.8rem; color: #7a9ab8; border-bottom: 1px solid #1e2d45; }
    .demo-row:last-child { border-bottom: none; }
    .demo-badge { background: #1a3050; color: #60a5fa; padding: 0.1rem 0.55rem; border-radius: 20px; font-size: 0.68rem; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="login-brand">
            <div class="lb-icon">🛢️</div>
            <div class="lb-company">Petrobras</div>
            <div class="lb-title">Senai EaD</div>
            <div class="lb-sub">Plataforma de Gestão de Projetos EaD</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("E-mail", placeholder="seu@email.com")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

            if submitted:
                if not email or not senha:
                    st.error("Preencha e-mail e senha.")
                else:
                    user = authenticate(email, senha)
                    if user:
                        st.session_state.update({
                            "authenticated": True,
                            "user_id": user.id,
                            "user_nome": user.nome,
                            "user_email": user.email,
                            "user_role": user.role,
                            "user_color": user.avatar_color,
                        })
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")

        st.markdown("""
        <div class="demo-box">
            <div class="demo-title">🔑 Contas de demonstração</div>
            <div class="demo-row"><span>admin@demo.com / admin123</span><span class="demo-badge">Admin</span></div>
            <div class="demo-row"><span>gestor@demo.com / gestor123</span><span class="demo-badge">Gestor</span></div>
            <div class="demo-row"><span>colab@demo.com / colab123</span><span class="demo-badge">Colab</span></div>
        </div>
        """, unsafe_allow_html=True)


def authenticate(email, password):
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user and verify_password(password, user.senha_hash):
            return user
        return None
    finally:
        db.close()


def logout():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


def require_auth():
    return st.session_state.get("authenticated", False)


def require_role(*roles):
    return st.session_state.get("user_role") in roles


def get_current_user_id():
    return st.session_state.get("user_id")

import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_db
from models import Project, User, Task
from auth import require_role


def show():
    st.markdown("## 📁 Projetos")
    st.markdown("---")

    db = get_db()
    try:
        tab1, tab2 = st.tabs(["📋 Lista de Projetos", "➕ Novo Projeto"])

        with tab1:
            _list_projects(db)

        with tab2:
            if require_role("admin", "gestor"):
                _create_project_form(db)
            else:
                st.warning("Você não tem permissão para criar projetos.")
    finally:
        db.close()


def _list_projects(db):
    # Filters
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("🔍 Buscar projeto", placeholder="Nome do projeto...")
    with col2:
        status_filter = st.selectbox("Status", ["Todos", "Ativo", "Planejamento", "Pausado", "Concluído", "Cancelado"])
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)

    query = db.query(Project)
    if search:
        query = query.filter(Project.nome.ilike(f"%{search}%"))
    if status_filter != "Todos":
        query = query.filter(Project.status == status_filter)

    projects = query.order_by(Project.criado_em.desc()).all()

    if not projects:
        st.info("Nenhum projeto encontrado.")
        return

    for p in projects:
        _project_card(p, db)


def _project_card(p, db):
    status_colors = {
        "Ativo": "#10b981", "Concluído": "#6366f1",
        "Planejamento": "#f59e0b", "Pausado": "#64748b", "Cancelado": "#ef4444"
    }
    status_icons = {
        "Ativo": "🟢", "Concluído": "✅", "Planejamento": "🟡",
        "Pausado": "⏸️", "Cancelado": "❌"
    }
    color = status_colors.get(p.status, "#64748b")
    icon = status_icons.get(p.status, "⚪")

    total_tasks = len(p.tarefas)
    done_tasks = sum(1 for t in p.tarefas if t.status == "Concluído")
    now = datetime.now()
    is_late = p.data_fim and p.data_fim < now and p.status not in ["Concluído", "Cancelado"]

    with st.expander(f"{icon} **{p.nome}** — {p.status} | {p.progresso:.0f}% concluído {'⚠️ ATRASADO' if is_late else ''}"):
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown(f"**Descrição:** {p.descricao or 'Sem descrição'}")
            st.markdown(f"**Responsável:** {p.responsavel_user.nome if p.responsavel_user else '-'}")
            if p.data_inicio and p.data_fim:
                st.markdown(f"**Período:** {p.data_inicio.strftime('%d/%m/%Y')} → {p.data_fim.strftime('%d/%m/%Y')}")

        with col2:
            st.metric("📋 Tarefas", f"{done_tasks}/{total_tasks}")

        with col3:
            st.metric("📈 Progresso", f"{p.progresso:.0f}%")

        st.progress(p.progresso / 100)

        # Actions
        if require_role("admin", "gestor"):
            col_e, col_d, _ = st.columns([1, 1, 3])
            with col_e:
                if st.button("✏️ Editar", key=f"edit_{p.id}"):
                    st.session_state[f"editing_project"] = p.id
                    st.rerun()
            with col_d:
                if st.button("🗑️ Excluir", key=f"del_{p.id}", type="secondary"):
                    st.session_state[f"confirm_del_proj_{p.id}"] = True

            if st.session_state.get(f"confirm_del_proj_{p.id}"):
                st.warning(f"⚠️ Tem certeza que deseja excluir **{p.nome}** e todas as suas tarefas?")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("✅ Confirmar exclusão", key=f"confirm_{p.id}", type="primary"):
                        db.delete(p)
                        db.commit()
                        del st.session_state[f"confirm_del_proj_{p.id}"]
                        st.success("Projeto excluído!")
                        st.rerun()
                with cc2:
                    if st.button("❌ Cancelar", key=f"cancel_{p.id}"):
                        del st.session_state[f"confirm_del_proj_{p.id}"]
                        st.rerun()

    # Edit modal (shown below the card if editing)
    if st.session_state.get("editing_project") == p.id:
        _edit_project_form(p, db)


def _edit_project_form(p, db):
    st.markdown("---")
    st.markdown(f"### ✏️ Editando: {p.nome}")

    users = db.query(User).all()
    user_map = {u.nome: u.id for u in users}
    user_names = [u.nome for u in users]

    current_resp = next((u.nome for u in users if u.id == p.responsavel_id), user_names[0] if user_names else None)

    with st.form(f"edit_form_{p.id}"):
        nome = st.text_input("Nome do Projeto", value=p.nome)
        descricao = st.text_area("Descrição", value=p.descricao or "")
        responsavel = st.selectbox("Responsável", user_names,
                                   index=user_names.index(current_resp) if current_resp in user_names else 0)
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data de Início", value=p.data_inicio.date() if p.data_inicio else None)
            status = st.selectbox("Status", ["Planejamento", "Ativo", "Pausado", "Concluído", "Cancelado"],
                                  index=["Planejamento", "Ativo", "Pausado", "Concluído", "Cancelado"].index(p.status) if p.status in ["Planejamento", "Ativo", "Pausado", "Concluído", "Cancelado"] else 0)
        with col2:
            data_fim = st.date_input("Data de Fim", value=p.data_fim.date() if p.data_fim else None)
            progresso = st.slider("Progresso (%)", 0, 100, int(p.progresso))

        col_s, col_c = st.columns(2)
        with col_s:
            submitted = st.form_submit_button("💾 Salvar", type="primary", use_container_width=True)
        with col_c:
            cancelled = st.form_submit_button("Cancelar", use_container_width=True)

        if submitted:
            p.nome = nome
            p.descricao = descricao
            p.responsavel_id = user_map.get(responsavel)
            p.data_inicio = datetime.combine(data_inicio, datetime.min.time()) if data_inicio else None
            p.data_fim = datetime.combine(data_fim, datetime.min.time()) if data_fim else None
            p.status = status
            p.progresso = float(progresso)
            p.atualizado_em = datetime.now()
            db.commit()
            del st.session_state["editing_project"]
            st.success("✅ Projeto atualizado!")
            st.rerun()

        if cancelled:
            del st.session_state["editing_project"]
            st.rerun()


def _create_project_form(db):
    st.markdown("### ➕ Criar Novo Projeto")

    users = db.query(User).all()
    user_map = {u.nome: u.id for u in users}
    user_names = [u.nome for u in users]

    with st.form("create_project_form"):
        nome = st.text_input("Nome do Projeto *", placeholder="Ex: Portal do Aluno v3")
        descricao = st.text_area("Descrição", placeholder="Descreva os objetivos do projeto...")

        col1, col2 = st.columns(2)
        with col1:
            responsavel = st.selectbox("Responsável *", user_names)
            data_inicio = st.date_input("Data de Início")
            status = st.selectbox("Status inicial", ["Planejamento", "Ativo"])
        with col2:
            data_fim = st.date_input("Data de Conclusão")
            progresso = st.slider("Progresso inicial (%)", 0, 100, 0)

        submitted = st.form_submit_button("🚀 Criar Projeto", type="primary", use_container_width=True)

        if submitted:
            if not nome:
                st.error("O nome do projeto é obrigatório.")
            else:
                proj = Project(
                    nome=nome,
                    descricao=descricao,
                    responsavel_id=user_map.get(responsavel),
                    data_inicio=datetime.combine(data_inicio, datetime.min.time()),
                    data_fim=datetime.combine(data_fim, datetime.min.time()),
                    status=status,
                    progresso=float(progresso)
                )
                db.add(proj)
                db.commit()
                st.success(f"✅ Projeto **{nome}** criado com sucesso!")
                st.balloons()

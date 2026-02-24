import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_db
from models import Task, Project, User
from auth import require_role, get_current_user_id


def show():
    st.markdown("## ✅ Tarefas")
    st.markdown("---")

    db = get_db()
    try:
        tab1, tab2 = st.tabs(["📋 Lista de Tarefas", "➕ Nova Tarefa"])

        with tab1:
            _list_tasks(db)
        with tab2:
            _create_task_form(db)
    finally:
        db.close()


def _list_tasks(db):
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        search = st.text_input("🔍 Buscar", placeholder="Título da tarefa...")
    with col2:
        projects = db.query(Project).all()
        proj_opts = ["Todos"] + [p.nome for p in projects]
        proj_filter = st.selectbox("Projeto", proj_opts)
    with col3:
        status_filter = st.selectbox("Status", ["Todos", "A Fazer", "Em Andamento", "Concluído"])
    with col4:
        prior_filter = st.selectbox("Prioridade", ["Todas", "Crítica", "Alta", "Média", "Baixa"])

    query = db.query(Task)
    if search:
        query = query.filter(Task.titulo.ilike(f"%{search}%"))
    if proj_filter != "Todos":
        proj = db.query(Project).filter(Project.nome == proj_filter).first()
        if proj:
            query = query.filter(Task.projeto_id == proj.id)
    if status_filter != "Todos":
        query = query.filter(Task.status == status_filter)
    if prior_filter != "Todas":
        query = query.filter(Task.prioridade == prior_filter)

    tasks = query.order_by(Task.data_criacao.desc()).all()

    if not tasks:
        st.info("Nenhuma tarefa encontrada.")
        return

    st.markdown(f"**{len(tasks)} tarefa(s) encontrada(s)**")
    st.markdown("")

    for t in tasks:
        _task_card(t, db)


def _task_card(t, db):
    now = datetime.now()
    is_late = t.prazo and t.prazo < now and t.status != "Concluído"
    is_done = t.status == "Concluído"

    prior_colors = {"Crítica": "🔴", "Alta": "🟠", "Média": "🟡", "Baixa": "🟢"}
    status_icons = {"A Fazer": "📝", "Em Andamento": "⚙️", "Concluído": "✅"}

    p_icon = prior_colors.get(t.prioridade, "⚪")
    s_icon = status_icons.get(t.status, "📌")
    late_label = " ⚠️ ATRASADA" if is_late else ""
    done_style = "~~" if is_done else ""

    label = f"{s_icon} {done_style}{t.titulo}{done_style} | {p_icon} {t.prioridade} | {t.status}{late_label}"

    with st.expander(label):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**Descrição:** {t.descricao or 'Sem descrição'}")
            st.markdown(f"**Projeto:** {t.projeto.nome if t.projeto else '-'}")
            st.markdown(f"**Responsável:** {t.responsavel_user.nome if t.responsavel_user else '-'}")
            if t.prazo:
                prazo_str = t.prazo.strftime("%d/%m/%Y")
                if is_late:
                    dias = (now - t.prazo).days
                    st.markdown(f"**Prazo:** :red[{prazo_str} (atraso de {dias} dia(s))]")
                else:
                    st.markdown(f"**Prazo:** {prazo_str}")
            st.markdown(f"**Criada em:** {t.data_criacao.strftime('%d/%m/%Y %H:%M')}")

        with col2:
            # Quick status change
            status_opts = ["A Fazer", "Em Andamento", "Concluído"]
            curr_idx = status_opts.index(t.status) if t.status in status_opts else 0
            new_status = st.selectbox("Alterar status", status_opts,
                                      index=curr_idx, key=f"status_{t.id}")
            if new_status != t.status:
                t.status = new_status
                t.atualizado_em = datetime.now()
                db.commit()
                st.success("Status atualizado!")
                st.rerun()

        if require_role("admin", "gestor") or t.responsavel_id == get_current_user_id():
            col_e, col_d, _ = st.columns([1, 1, 3])
            with col_e:
                if st.button("✏️ Editar", key=f"tedit_{t.id}"):
                    st.session_state["editing_task"] = t.id
                    st.rerun()
            with col_d:
                if st.button("🗑️ Excluir", key=f"tdel_{t.id}"):
                    st.session_state[f"confirm_del_task_{t.id}"] = True

            if st.session_state.get(f"confirm_del_task_{t.id}"):
                st.warning("Tem certeza que deseja excluir esta tarefa?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Confirmar", key=f"tconfirm_{t.id}", type="primary"):
                        db.delete(t)
                        db.commit()
                        del st.session_state[f"confirm_del_task_{t.id}"]
                        st.success("Tarefa excluída!")
                        st.rerun()
                with c2:
                    if st.button("❌ Cancelar", key=f"tcancel_{t.id}"):
                        del st.session_state[f"confirm_del_task_{t.id}"]
                        st.rerun()

    if st.session_state.get("editing_task") == t.id:
        _edit_task_form(t, db)


def _edit_task_form(t, db):
    st.markdown("---")
    st.markdown(f"### ✏️ Editando: {t.titulo}")

    projects = db.query(Project).all()
    users = db.query(User).all()
    proj_map = {p.nome: p.id for p in projects}
    user_map = {u.nome: u.id for u in users}
    proj_names = [p.nome for p in projects]
    user_names = [u.nome for u in users]

    curr_proj = next((p.nome for p in projects if p.id == t.projeto_id), proj_names[0] if proj_names else None)
    curr_resp = next((u.nome for u in users if u.id == t.responsavel_id), user_names[0] if user_names else None)

    with st.form(f"edit_task_{t.id}"):
        titulo = st.text_input("Título", value=t.titulo)
        descricao = st.text_area("Descrição", value=t.descricao or "")
        col1, col2 = st.columns(2)
        with col1:
            projeto = st.selectbox("Projeto", proj_names,
                                   index=proj_names.index(curr_proj) if curr_proj in proj_names else 0)
            status = st.selectbox("Status", ["A Fazer", "Em Andamento", "Concluído"],
                                  index=["A Fazer", "Em Andamento", "Concluído"].index(t.status))
            prazo = st.date_input("Prazo", value=t.prazo.date() if t.prazo else None)
        with col2:
            responsavel = st.selectbox("Responsável", user_names,
                                       index=user_names.index(curr_resp) if curr_resp in user_names else 0)
            prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Crítica"],
                                      index=["Baixa", "Média", "Alta", "Crítica"].index(t.prioridade) if t.prioridade in ["Baixa", "Média", "Alta", "Crítica"] else 1)

        c1, c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button("💾 Salvar", type="primary", use_container_width=True)
        with c2:
            cancelled = st.form_submit_button("Cancelar", use_container_width=True)

        if submitted:
            t.titulo = titulo
            t.descricao = descricao
            t.projeto_id = proj_map.get(projeto)
            t.responsavel_id = user_map.get(responsavel)
            t.status = status
            t.prioridade = prioridade
            t.prazo = datetime.combine(prazo, datetime.min.time()) if prazo else None
            t.atualizado_em = datetime.now()
            db.commit()
            del st.session_state["editing_task"]
            st.success("✅ Tarefa atualizada!")
            st.rerun()

        if cancelled:
            del st.session_state["editing_task"]
            st.rerun()


def _create_task_form(db):
    st.markdown("### ➕ Criar Nova Tarefa")

    projects = db.query(Project).filter(Project.status.in_(["Ativo", "Planejamento"])).all()
    users = db.query(User).all()

    if not projects:
        st.warning("Nenhum projeto ativo disponível. Crie um projeto primeiro.")
        return

    proj_map = {p.nome: p.id for p in projects}
    user_map = {u.nome: u.id for u in users}

    with st.form("create_task_form"):
        titulo = st.text_input("Título da Tarefa *", placeholder="Ex: Criar protótipo da tela inicial")
        descricao = st.text_area("Descrição", placeholder="Detalhe o que precisa ser feito...")

        col1, col2 = st.columns(2)
        with col1:
            projeto = st.selectbox("Projeto *", list(proj_map.keys()))
            responsavel = st.selectbox("Responsável", list(user_map.keys()))
            prazo = st.date_input("Prazo")
        with col2:
            status = st.selectbox("Status", ["A Fazer", "Em Andamento"])
            prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Crítica"], index=1)

        submitted = st.form_submit_button("✅ Criar Tarefa", type="primary", use_container_width=True)

        if submitted:
            if not titulo:
                st.error("O título é obrigatório.")
            else:
                task = Task(
                    titulo=titulo,
                    descricao=descricao,
                    projeto_id=proj_map.get(projeto),
                    responsavel_id=user_map.get(responsavel),
                    status=status,
                    prioridade=prioridade,
                    prazo=datetime.combine(prazo, datetime.min.time()) if prazo else None
                )
                db.add(task)
                db.commit()
                st.success(f"✅ Tarefa **{titulo}** criada com sucesso!")

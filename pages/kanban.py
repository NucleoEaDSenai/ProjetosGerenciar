import streamlit as st
from datetime import datetime
from database import get_db
from models import Task, Project


def show():
    st.markdown("## 🗂️ Kanban Board")
    st.markdown("---")

    db = get_db()
    try:
        # Project filter
        projects = db.query(Project).all()
        proj_opts = ["Todos os Projetos"] + [p.nome for p in projects]

        col1, col2 = st.columns([2, 3])
        with col1:
            selected_proj = st.selectbox("📁 Filtrar por Projeto", proj_opts)

        query = db.query(Task)
        if selected_proj != "Todos os Projetos":
            proj = db.query(Project).filter(Project.nome == selected_proj).first()
            if proj:
                query = query.filter(Task.projeto_id == proj.id)

        all_tasks = query.all()

        a_fazer = [t for t in all_tasks if t.status == "A Fazer"]
        em_andamento = [t for t in all_tasks if t.status == "Em Andamento"]
        concluido = [t for t in all_tasks if t.status == "Concluído"]

        # Summary
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("📝 A Fazer", len(a_fazer))
        with c2:
            st.metric("⚙️ Em Andamento", len(em_andamento))
        with c3:
            st.metric("✅ Concluído", len(concluido))

        st.markdown("---")

        # Kanban CSS
        st.markdown("""
        <style>
        .kanban-col-header {
            font-weight: 700;
            font-size: 1rem;
            padding: 0.6rem 1rem;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 1rem;
        }
        .kanban-afazer { background: #fef3c7; color: #92400e; }
        .kanban-andamento { background: #e0e7ff; color: #3730a3; }
        .kanban-concluido { background: #d1fae5; color: #065f46; }

        .kanban-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            border-left: 4px solid #6366f1;
            transition: box-shadow 0.2s;
        }
        .kanban-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.12); }
        .kanban-card-critica { border-left-color: #ef4444; }
        .kanban-card-alta { border-left-color: #f97316; }
        .kanban-card-media { border-left-color: #6366f1; }
        .kanban-card-baixa { border-left-color: #10b981; }
        .kanban-card-done { border-left-color: #10b981; opacity: 0.75; }

        .card-title { font-weight: 600; font-size: 0.9rem; color: #1e293b; margin-bottom: 0.3rem; }
        .card-project { font-size: 0.75rem; color: #6366f1; font-weight: 500; }
        .card-meta { font-size: 0.75rem; color: #64748b; margin-top: 0.4rem; }
        .card-badge {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 600;
            margin-right: 0.3rem;
        }
        .badge-critica { background: #fee2e2; color: #dc2626; }
        .badge-alta { background: #ffedd5; color: #c2410c; }
        .badge-media { background: #e0e7ff; color: #4338ca; }
        .badge-baixa { background: #d1fae5; color: #065f46; }
        .badge-atrasada { background: #fef2f2; color: #dc2626; }

        .kanban-empty {
            text-align: center;
            color: #94a3b8;
            padding: 2rem 1rem;
            font-size: 0.9rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Three columns
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.markdown('<div class="kanban-col-header kanban-afazer">📝 A Fazer</div>', unsafe_allow_html=True)
            if not a_fazer:
                st.markdown('<div class="kanban-empty">Nenhuma tarefa pendente 🎉</div>', unsafe_allow_html=True)
            for t in a_fazer:
                _render_card(t, db, col="afazer")

        with col_b:
            st.markdown('<div class="kanban-col-header kanban-andamento">⚙️ Em Andamento</div>', unsafe_allow_html=True)
            if not em_andamento:
                st.markdown('<div class="kanban-empty">Nenhuma tarefa em progresso</div>', unsafe_allow_html=True)
            for t in em_andamento:
                _render_card(t, db, col="andamento")

        with col_c:
            st.markdown('<div class="kanban-col-header kanban-concluido">✅ Concluído</div>', unsafe_allow_html=True)
            if not concluido:
                st.markdown('<div class="kanban-empty">Nenhuma tarefa concluída ainda</div>', unsafe_allow_html=True)
            for t in concluido:
                _render_card(t, db, col="concluido")

    finally:
        db.close()


def _render_card(t: Task, db, col: str):
    now = datetime.now()
    is_late = t.prazo and t.prazo < now and t.status != "Concluído"
    is_done = t.status == "Concluído"

    prior_class = {
        "Crítica": "critica", "Alta": "alta", "Média": "media", "Baixa": "baixa"
    }.get(t.prioridade, "media")

    card_class = "kanban-card-done" if is_done else f"kanban-card-{prior_class}"
    prior_badge = f'<span class="card-badge badge-{prior_class}">{t.prioridade}</span>'
    late_badge = '<span class="card-badge badge-atrasada">⚠️ Atrasada</span>' if is_late else ""

    prazo_str = ""
    if t.prazo:
        prazo_str = f"📅 {t.prazo.strftime('%d/%m/%Y')}"

    resp_str = f"👤 {t.responsavel_user.nome}" if t.responsavel_user else ""
    proj_str = f'<div class="card-project">📁 {t.projeto.nome}</div>' if t.projeto else ""

    card_html = f"""
    <div class="kanban-card {card_class}">
        {proj_str}
        <div class="card-title">{'~~' if is_done else ''}{t.titulo}{'~~' if is_done else ''}</div>
        <div class="card-meta">
            {prior_badge}{late_badge}
        </div>
        <div class="card-meta">{resp_str} &nbsp; {prazo_str}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # Quick move buttons
    with st.container():
        status_opts = ["A Fazer", "Em Andamento", "Concluído"]
        current_idx = status_opts.index(t.status) if t.status in status_opts else 0

        cols = []
        if current_idx > 0:
            cols.append(("⬅️", status_opts[current_idx - 1]))
        if current_idx < len(status_opts) - 1:
            cols.append(("➡️", status_opts[current_idx + 1]))

        if cols:
            btn_cols = st.columns(len(cols) + 1)
            for idx, (arrow, new_status) in enumerate(cols):
                with btn_cols[idx]:
                    label = f"{arrow} {new_status.split()[0]}"
                    if st.button(label, key=f"kanban_{t.id}_{new_status}", use_container_width=True):
                        t.status = new_status
                        t.atualizado_em = datetime.now()
                        db.commit()
                        st.rerun()

    st.markdown('<div style="margin-bottom:0.25rem"></div>', unsafe_allow_html=True)

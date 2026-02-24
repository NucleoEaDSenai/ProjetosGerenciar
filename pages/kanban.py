import streamlit as st
from datetime import datetime
from database import get_db
from models import Task, Project


def show():
    st.markdown("""
    <div style="margin-bottom:1.2rem;">
        <h1 style="font-size:1.8rem;font-weight:700;color:#e2f0ff;margin:0;letter-spacing:-0.5px;">🗂️ Kanban</h1>
        <div style="font-size:0.82rem;color:#4a6a8a;margin-top:0.2rem;">Arraste tarefas entre colunas usando os botões de movimento</div>
    </div>
    """, unsafe_allow_html=True)

    db = get_db()
    try:
        projects = db.query(Project).order_by(Project.nome).all()
        proj_opts = ["Todos os Projetos"] + [p.nome[:60] + ("..." if len(p.nome) > 60 else "") for p in projects]
        proj_map = {(p.nome[:60] + ("..." if len(p.nome) > 60 else "")): p.id for p in projects}

        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            sel_proj = st.selectbox("📁 Projeto", proj_opts, label_visibility="collapsed")
        with col_f2:
            sel_resp = st.text_input("🔍 Filtrar por responsável", placeholder="Nome do responsável...", label_visibility="collapsed")

        query = db.query(Task)
        if sel_proj != "Todos os Projetos":
            pid = proj_map.get(sel_proj)
            if pid:
                query = query.filter(Task.projeto_id == pid)
        if sel_resp:
            from models import User
            users = db.query(User).filter(User.nome.ilike(f"%{sel_resp}%")).all()
            uids = [u.id for u in users]
            if uids:
                query = query.filter(Task.responsavel_id.in_(uids))

        all_tasks = query.all()

        a_fazer     = [t for t in all_tasks if t.status == "A Fazer"]
        em_andamento = [t for t in all_tasks if t.status == "Em Andamento"]
        concluido   = [t for t in all_tasks if t.status == "Concluído"]

        # Stats
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div style="background:#1f1a08;border:1.5px solid #6a4a0888;border-radius:12px;
                padding:0.8rem 1.1rem;text-align:center;margin-bottom:1rem;">
                <div style="font-size:1.6rem;font-weight:700;color:#f59e0b;">{len(a_fazer)}</div>
                <div style="font-size:0.72rem;color:#6a4a08;font-weight:600;text-transform:uppercase;">A Fazer</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="background:#0d2137;border:1.5px solid #1d5a8a88;border-radius:12px;
                padding:0.8rem 1.1rem;text-align:center;margin-bottom:1rem;">
                <div style="font-size:1.6rem;font-weight:700;color:#3b9eff;">{len(em_andamento)}</div>
                <div style="font-size:0.72rem;color:#1d4a8a;font-weight:600;text-transform:uppercase;">Em Andamento</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div style="background:#0d2118;border:1.5px solid #1a604088;border-radius:12px;
                padding:0.8rem 1.1rem;text-align:center;margin-bottom:1rem;">
                <div style="font-size:1.6rem;font-weight:700;color:#10b981;">{len(concluido)}</div>
                <div style="font-size:0.72rem;color:#1a4a30;font-weight:600;text-transform:uppercase;">Concluído</div>
            </div>
            """, unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)

        _col_header(col_a, "📝 A Fazer", "#f59e0b", "#1f1a08", len(a_fazer))
        _col_header(col_b, "⚙️ Em Andamento", "#3b9eff", "#0d2137", len(em_andamento))
        _col_header(col_c, "✅ Concluído", "#10b981", "#0d2118", len(concluido))

        now = datetime.now()

        with col_a:
            if not a_fazer:
                st.markdown('<div style="text-align:center;color:#2e4a20;padding:1.5rem;font-size:0.85rem;">Nenhuma tarefa pendente 🎉</div>', unsafe_allow_html=True)
            for t in a_fazer:
                _kanban_card(t, db, now)

        with col_b:
            if not em_andamento:
                st.markdown('<div style="text-align:center;color:#1e3a5a;padding:1.5rem;font-size:0.85rem;">Nenhuma tarefa em andamento</div>', unsafe_allow_html=True)
            for t in em_andamento:
                _kanban_card(t, db, now)

        with col_c:
            if not concluido:
                st.markdown('<div style="text-align:center;color:#1a3a25;padding:1.5rem;font-size:0.85rem;">Nenhuma tarefa concluída</div>', unsafe_allow_html=True)
            for t in concluido:
                _kanban_card(t, db, now)

    finally:
        db.close()


def _col_header(col, title, color, bg, count):
    with col:
        st.markdown(f"""
        <div style="background:{bg};border:1px solid {color}33;border-top:3px solid {color};
            border-radius:8px 8px 0 0;padding:0.6rem 1rem;margin-bottom:0.5rem;
            display:flex;justify-content:space-between;align-items:center;">
            <span style="font-weight:700;font-size:0.88rem;color:{color};">{title}</span>
            <span style="background:{color}22;color:{color};border-radius:12px;
                padding:0.1rem 0.55rem;font-size:0.72rem;font-weight:600;">{count}</span>
        </div>
        """, unsafe_allow_html=True)


def _kanban_card(t, db, now):
    is_done = t.status == "Concluído"
    is_late = t.prazo and t.prazo < now and not is_done

    PRIO_COLORS = {"Crítica": "#ff4444", "Alta": "#ff8c42", "Média": "#fbbf24", "Baixa": "#60b8ff"}
    prio_col = PRIO_COLORS.get(t.prioridade, "#fbbf24")

    border_l = {"Crítica": "#ff4444", "Alta": "#ff8c42", "Média": "#f59e0b", "Baixa": "#3b9eff"}.get(t.prioridade, "#f59e0b")
    if is_done:
        border_l = "#10b981"
    if is_late:
        border_l = "#ff4444"

    prazo_str = t.prazo.strftime("%d/%m/%Y") if t.prazo else "—"
    dias_atraso = (now - t.prazo).days if is_late else 0
    resp_nome = t.responsavel_user.nome.split()[0] if t.responsavel_user else "—"
    proj_nome = (t.projeto.nome[:35] + "..." if t.projeto and len(t.projeto.nome) > 35 else (t.projeto.nome if t.projeto else "")) if t.projeto else ""

    titulo_style = "text-decoration:line-through;opacity:0.6;" if is_done else ""
    late_badge = f'<span style="color:#ff4444;font-size:0.65rem;font-weight:700;">⚠ {dias_atraso}d</span>' if is_late else ""
    card_bg = "#0d2118" if is_done else "#161b27"

    st.markdown(f"""
    <div style="background:{card_bg};border:1px solid #1e2d45;border-left:3px solid {border_l};
        border-radius:8px;padding:0.7rem 0.9rem;margin-bottom:0.4rem;">
        {f'<div style="font-size:0.65rem;color:#2e4a6a;margin-bottom:0.25rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">📁 {proj_nome}</div>' if proj_nome else ''}
        <div style="font-size:0.83rem;font-weight:600;color:#c8d6f0;line-height:1.3;margin-bottom:0.4rem;{titulo_style}">
            {t.titulo[:80] + ('...' if len(t.titulo) > 80 else '')}
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="display:flex;gap:0.4rem;align-items:center;flex-wrap:wrap;">
                <span style="background:{prio_col}22;color:{prio_col};border-radius:4px;
                    padding:0.08rem 0.4rem;font-size:0.63rem;font-weight:600;">{t.prioridade}</span>
                {late_badge}
            </div>
            <div style="font-size:0.65rem;color:#3a5a7a;">👤 {resp_nome}</div>
        </div>
        <div style="font-size:0.65rem;color:{'#ff6b6b' if is_late else '#2e4a6a'};margin-top:0.3rem;">
            📅 {prazo_str}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Move buttons
    opts = ["A Fazer", "Em Andamento", "Concluído"]
    idx = opts.index(t.status) if t.status in opts else 0
    btn_cols = []
    if idx > 0:
        btn_cols.append(("←", opts[idx - 1]))
    if idx < 2:
        btn_cols.append(("→", opts[idx + 1]))

    if btn_cols:
        b_cols = st.columns(len(btn_cols) + 1)
        for i, (arrow, new_status) in enumerate(btn_cols):
            label = f"{arrow} {new_status.split()[0]}"
            with b_cols[i]:
                if st.button(label, key=f"kb_{t.id}_{new_status}", use_container_width=True):
                    t.status = new_status
                    t.atualizado_em = datetime.now()
                    # Update project progress
                    if t.projeto:
                        proj = t.projeto
                        n_done = sum(1 for x in proj.tarefas if
                                     (x.id == t.id and new_status == "Concluído") or
                                     (x.id != t.id and x.status == "Concluído"))
                        proj.progresso = (n_done / len(proj.tarefas) * 100) if proj.tarefas else 0
                    db.commit()
                    st.rerun()

    st.markdown("<div style='height:0.1rem'></div>", unsafe_allow_html=True)

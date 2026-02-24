import streamlit as st
from datetime import datetime
from database import get_db
from models import Project, Task, User
from auth import require_role, get_current_user_id


# ── Status configs ─────────────────────────────────────────────────────────────
STATUS_CFG = {
    "Ativo":        {"icon": "●", "color": "#3b9eff", "bg": "#0d2137", "border": "#1d5a8a"},
    "Concluído":    {"icon": "✓", "color": "#10b981", "bg": "#0d2118", "border": "#1a6040"},
    "Planejamento": {"icon": "◐", "color": "#f59e0b", "bg": "#1f1a08", "border": "#6a4a08"},
    "Cancelado":    {"icon": "✕", "color": "#ef4444", "bg": "#1f0d0d", "border": "#6a1a1a"},
    "Pausado":      {"icon": "⏸", "color": "#64748b", "bg": "#151520", "border": "#2a3a54"},
}

TASK_STATUS_CFG = {
    "A Fazer":      {"color": "#f59e0b", "bg": "#1f1a08", "border": "#6a4a08"},
    "Em Andamento": {"color": "#3b9eff", "bg": "#0d2137", "border": "#1d5a8a"},
    "Concluído":    {"color": "#10b981", "bg": "#0d2118", "border": "#1a6040"},
}

PRIO_CFG = {
    "Crítica":  {"color": "#ff4444", "bg": "#2d0808"},
    "Alta":     {"color": "#ff8c42", "bg": "#2a1508"},
    "Média":    {"color": "#fbbf24", "bg": "#1f1a08"},
    "Baixa":    {"color": "#60b8ff", "bg": "#0d2137"},
}

BUCKET_ICONS = {
    "PELD": "📘", "pré-medição": "📐", "Upload para o BDOC - Files e Scorm": "📤",
    "Validação - Desenvolvimento": "🔍", "Autoria digital": "✍️",
    "Aguardando material base": "⏳", "Validação - PI": "📝",
    "Projetos cancelados/suspensos": "🚫", "Homologação/Instalação": "🔧",
    "Desenvolvimento": "💻", "Projeto Instrucional (PI)": "📋",
    "Fazer Cronograma": "📅", "Revisão Textual/Tradução": "🔤",
    "Aguardando reunião inicial": "🗓️",
}


def show():
    db = get_db()
    try:
        # ── Detect if we're viewing a specific project ──────────────────────
        selected_id = st.session_state.get("proj_detail_id")

        if selected_id:
            proj = db.query(Project).filter(Project.id == selected_id).first()
            if proj:
                _show_project_detail(proj, db)
                return
            else:
                st.session_state.pop("proj_detail_id", None)

        _show_project_list(db)

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
#  PROJECT LIST
# ══════════════════════════════════════════════════════════════════════════════
def _show_project_list(db):
    now = datetime.now()

    # ── Header ────────────────────────────────────────────────────────────────
    col_h, col_btn = st.columns([4, 1])
    with col_h:
        st.markdown("""
        <div style="margin-bottom:0.8rem;">
            <h1 style="font-size:1.8rem;font-weight:700;color:#e2f0ff;margin:0;letter-spacing:-0.5px;">
                📋 Projetos
            </h1>
            <div style="font-size:0.82rem;color:#4a6a8a;margin-top:0.2rem;">
                Clique em um projeto para ver detalhes e tarefas
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_btn:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if require_role("admin", "gestor"):
            if st.button("＋ Novo Projeto", type="primary", use_container_width=True):
                st.session_state["creating_project"] = True
                st.rerun()

    # ── Create form (if triggered) ────────────────────────────────────────────
    if st.session_state.get("creating_project"):
        _create_project_form(db)

    # ── Filters ───────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3, col_f4 = st.columns([3, 1, 1, 1])
    with col_f1:
        search = st.text_input("🔍", placeholder="Buscar projeto por nome ou HRC...", label_visibility="collapsed")
    with col_f2:
        status_f = st.selectbox("Status", ["Todos", "Ativo", "Planejamento", "Concluído", "Cancelado", "Pausado"], label_visibility="collapsed")
    with col_f3:
        users = db.query(User).order_by(User.nome).all()
        user_opts = ["Todos responsáveis"] + [u.nome for u in users]
        resp_f = st.selectbox("Responsável", user_opts, label_visibility="collapsed")
    with col_f4:
        atraso_f = st.selectbox("Atraso", ["Todos", "Com atraso", "Em dia"], label_visibility="collapsed")

    # ── Query ────────────────────────────────────────────────────────────────
    query = db.query(Project)
    if search:
        query = query.filter(Project.nome.ilike(f"%{search}%"))
    if status_f != "Todos":
        query = query.filter(Project.status == status_f)
    if resp_f != "Todos responsáveis":
        user = db.query(User).filter(User.nome == resp_f).first()
        if user:
            query = query.filter(Project.responsavel_id == user.id)

    projects = query.order_by(Project.criado_em.desc()).all()

    # Filter by atraso
    if atraso_f == "Com atraso":
        projects = [p for p in projects if _has_overdue_tasks(p, now)]
    elif atraso_f == "Em dia":
        projects = [p for p in projects if not _has_overdue_tasks(p, now)]

    # ── Count bar ────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="font-size:0.78rem;color:#4a6a8a;margin:0.5rem 0 1rem;
        padding:0.5rem 0.8rem;background:#161b27;border-radius:8px;
        border:1px solid #1e2d45;display:inline-block;">
        {len(projects)} projeto(s) encontrado(s)
    </div>
    """, unsafe_allow_html=True)

    if not projects:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#4a6a8a;">
            <div style="font-size:2rem">📭</div>
            <div style="margin-top:0.5rem">Nenhum projeto encontrado com esses filtros</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Project cards grid ───────────────────────────────────────────────────
    for proj in projects:
        _project_card(proj, now, db)


def _project_card(p, now, db):
    cfg = STATUS_CFG.get(p.status, STATUS_CFG["Ativo"])
    n_tasks = len(p.tarefas)
    n_done = sum(1 for t in p.tarefas if t.status == "Concluído")
    n_andamento = sum(1 for t in p.tarefas if t.status == "Em Andamento")
    overdue = [t for t in p.tarefas if t.prazo and t.prazo < now and t.status != "Concluído"]
    n_overdue = len(overdue)
    max_atraso = max((now - t.prazo).days for t in overdue) if overdue else 0

    pct = p.progresso if p.progresso else (int(n_done / n_tasks * 100) if n_tasks > 0 else 0)
    resp_nome = p.responsavel_user.nome if p.responsavel_user else "—"

    # Extract HRC code
    hrc = ""
    import re
    m = re.search(r'\[HRC\d+\]', p.nome)
    if m:
        hrc = m.group(0)
    nome_clean = re.sub(r'\s*\[HRC\d+\]', '', p.nome).strip()

    # Prazo
    prazo_str = p.data_fim.strftime("%d/%m/%Y") if p.data_fim else "—"
    prazo_late = p.data_fim and p.data_fim < now and p.status not in ["Concluído", "Cancelado"]

    # Atraso badge
    atraso_html = ""
    if n_overdue > 0:
        if max_atraso > 30:
            ac, ab = "#ff4444", "#2d0808"
        elif max_atraso > 7:
            ac, ab = "#ff8c42", "#2a1508"
        else:
            ac, ab = "#fbbf24", "#1f1a08"
        atraso_html = f"""
        <span style="background:{ab};border:1px solid {ac}55;color:{ac};
            border-radius:6px;padding:0.15rem 0.5rem;font-size:0.7rem;font-weight:700;
            margin-left:0.4rem;">⚠ {max_atraso}d atraso</span>
        """

    # Progress bar color
    prog_color = cfg["color"] if pct < 100 else "#10b981"

    card_html = f"""
    <div style="background:#161b27;border:1px solid {cfg['border']};border-left:4px solid {cfg['color']};
        border-radius:12px;padding:1rem 1.2rem;margin-bottom:0.5rem;cursor:pointer;
        transition:all 0.15s;position:relative;" id="proj_{p.id}">

        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.5rem;">
            <div style="flex:1;min-width:200px;">
                <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">
                    <span style="color:{cfg['color']};font-size:0.95rem;">{cfg['icon']}</span>
                    <span style="font-size:0.95rem;font-weight:600;color:#e2f0ff;">{nome_clean}</span>
                    {f'<span style="font-size:0.68rem;color:#3a6a8a;background:#0d2137;padding:0.1rem 0.4rem;border-radius:4px;">{hrc}</span>' if hrc else ''}
                    {atraso_html}
                </div>
                <div style="font-size:0.73rem;color:#4a6a8a;margin-top:0.3rem;">
                    👤 {resp_nome}
                    &nbsp;·&nbsp;
                    📅 <span style="color:{'#ff6b6b' if prazo_late else '#4a6a8a'}">{prazo_str}</span>
                    &nbsp;·&nbsp;
                    📋 {n_done}/{n_tasks} tarefas
                    {f'&nbsp;·&nbsp; <span style="color:#3b9eff">{n_andamento} em andamento</span>' if n_andamento > 0 else ''}
                </div>
            </div>

            <div style="display:flex;align-items:center;gap:1rem;">
                <div style="text-align:right;">
                    <div style="font-size:0.68rem;color:{cfg['color']};font-weight:600;
                        background:{cfg['bg']};border:1px solid {cfg['border']};
                        border-radius:6px;padding:0.2rem 0.6rem;">{cfg['icon']} {p.status}</div>
                </div>
                <div style="font-size:1.3rem;font-weight:700;color:{prog_color};min-width:42px;text-align:right;">
                    {int(pct)}%
                </div>
            </div>
        </div>

        <div style="margin-top:0.75rem;background:#0f1117;border-radius:4px;height:5px;overflow:hidden;">
            <div style="width:{int(pct)}%;height:100%;background:{prog_color};
                border-radius:4px;transition:width 0.3s;"></div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    col_open, col_edit, col_del = st.columns([6, 1, 1])
    with col_open:
        if st.button(f"↗ Ver projeto", key=f"open_{p.id}", use_container_width=False):
            st.session_state["proj_detail_id"] = p.id
            st.rerun()
    if require_role("admin", "gestor"):
        with col_edit:
            if st.button("✏️", key=f"edit_{p.id}", help="Editar"):
                st.session_state["editing_proj_id"] = p.id
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"del_{p.id}", help="Excluir"):
                st.session_state[f"confirm_del_{p.id}"] = True

    if st.session_state.get(f"confirm_del_{p.id}"):
        st.warning(f"⚠️ Excluir **{p.nome}** e todas as {n_tasks} tarefas?")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("✅ Confirmar", key=f"cfm_{p.id}", type="primary"):
                db.delete(p); db.commit()
                st.success("Excluído!"); st.rerun()
        with cc2:
            if st.button("❌ Cancelar", key=f"cnc_{p.id}"):
                del st.session_state[f"confirm_del_{p.id}"]; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PROJECT DETAIL  (estilo Microsoft Planner)
# ══════════════════════════════════════════════════════════════════════════════
def _show_project_detail(p, db):
    now = datetime.now()

    # ── Back button ──────────────────────────────────────────────────────────
    if st.button("← Voltar para Projetos", key="back_btn"):
        st.session_state.pop("proj_detail_id", None)
        st.rerun()

    cfg = STATUS_CFG.get(p.status, STATUS_CFG["Ativo"])
    resp_nome = p.responsavel_user.nome if p.responsavel_user else "—"

    import re
    hrc = ""
    m = re.search(r'\[HRC[\d\s]*\d+\]', p.nome)
    if m:
        hrc = m.group(0)
    nome_clean = re.sub(r'\s*\[HRC[\d\s]*\d+\]', '', p.nome).strip()

    overdue_tasks = [t for t in p.tarefas if t.prazo and t.prazo < now and t.status != "Concluído"]
    max_atraso = max((now - t.prazo).days for t in overdue_tasks) if overdue_tasks else 0

    n_tasks = len(p.tarefas)
    n_done = sum(1 for t in p.tarefas if t.status == "Concluído")
    pct = p.progresso if p.progresso else (int(n_done / n_tasks * 100) if n_tasks > 0 else 0)

    # ── Project header (like Planner card header) ────────────────────────────
    prazo_str = p.data_fim.strftime("%d/%m/%Y") if p.data_fim else "Sem prazo"
    prazo_late = p.data_fim and p.data_fim < now and p.status not in ["Concluído", "Cancelado"]

    atraso_badge = ""
    if overdue_tasks:
        atraso_badge = f"""
        <span style="background:#2d0808;border:1px solid #aa222255;color:#ff6b6b;
            border-radius:8px;padding:0.2rem 0.7rem;font-size:0.75rem;font-weight:700;">
            ⚠ {max_atraso} dia(s) de atraso
        </span>
        """

    # Bucket (fase) icon
    bucket_txt = ""
    if p.descricao:
        for line in p.descricao.split('\n'):
            if line.startswith("Fase:"):
                bucket_txt = line.replace("Fase:", "").strip()
                break
    b_icon = BUCKET_ICONS.get(bucket_txt, "📂")

    st.markdown(f"""
    <div style="background:#161b27;border:1px solid {cfg['border']};border-left:6px solid {cfg['color']};
        border-radius:14px;padding:1.5rem 1.8rem;margin-bottom:1.5rem;">

        <div style="font-size:0.7rem;color:#4a6a8a;margin-bottom:0.4rem;letter-spacing:0.08em;">
            PETROBRAS / SENAI EAD &nbsp;·&nbsp; {b_icon} {bucket_txt or "Projeto EaD"}
        </div>

        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
            <div>
                <h2 style="font-size:1.4rem;font-weight:700;color:#e2f0ff;margin:0 0 0.3rem;
                    max-width:700px;line-height:1.3;">
                    {nome_clean}
                </h2>
                <div style="display:flex;flex-wrap:wrap;gap:0.5rem;align-items:center;">
                    <span style="background:{cfg['bg']};border:1px solid {cfg['border']};
                        color:{cfg['color']};border-radius:6px;padding:0.2rem 0.7rem;
                        font-size:0.75rem;font-weight:600;">
                        {cfg['icon']} {p.status}
                    </span>
                    {f'<span style="background:#0d1a2d;color:#3a6a8a;border-radius:6px;padding:0.2rem 0.6rem;font-size:0.72rem;">{hrc}</span>' if hrc else ''}
                    {atraso_badge}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:2rem;font-weight:700;color:{cfg['color']};">{int(pct)}%</div>
                <div style="font-size:0.7rem;color:#4a6a8a;">progresso</div>
            </div>
        </div>

        <div style="margin-top:1rem;background:#0f1117;border-radius:6px;height:8px;overflow:hidden;">
            <div style="width:{int(pct)}%;height:100%;background:{cfg['color']};border-radius:6px;"></div>
        </div>

        <div style="display:flex;gap:2rem;flex-wrap:wrap;margin-top:1rem;">
            <div>
                <div style="font-size:0.65rem;color:#2e4a6a;text-transform:uppercase;letter-spacing:0.1em;">Responsável</div>
                <div style="font-size:0.85rem;color:#c8d6f0;font-weight:500;">👤 {resp_nome}</div>
            </div>
            <div>
                <div style="font-size:0.65rem;color:#2e4a6a;text-transform:uppercase;letter-spacing:0.1em;">Prazo</div>
                <div style="font-size:0.85rem;color:{'#ff6b6b' if prazo_late else '#c8d6f0'};font-weight:500;">
                    📅 {prazo_str}
                </div>
            </div>
            <div>
                <div style="font-size:0.65rem;color:#2e4a6a;text-transform:uppercase;letter-spacing:0.1em;">Tarefas</div>
                <div style="font-size:0.85rem;color:#c8d6f0;font-weight:500;">📋 {n_done}/{n_tasks}</div>
            </div>
            {f'''<div>
                <div style="font-size:0.65rem;color:#2e4a6a;text-transform:uppercase;letter-spacing:0.1em;">Início</div>
                <div style="font-size:0.85rem;color:#c8d6f0;font-weight:500;">📆 {p.data_inicio.strftime("%d/%m/%Y")}</div>
            </div>''' if p.data_inicio else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Description / annotations ─────────────────────────────────────────────
    if p.descricao:
        desc_lines = [l for l in p.descricao.split('\n') if l.strip() and not l.startswith("Fase:") and not l.startswith("Rótulos:")]
        rotulos_line = next((l for l in p.descricao.split('\n') if l.startswith("Rótulos:")), "")
        rotulos = rotulos_line.replace("Rótulos:", "").strip() if rotulos_line else ""

        if desc_lines or rotulos:
            col_d, col_r = st.columns([3, 1])
            with col_d:
                if desc_lines:
                    st.markdown(f"""
                    <div style="background:#0f1117;border:1px solid #1e2d45;border-radius:10px;
                        padding:1rem 1.2rem;margin-bottom:1rem;">
                        <div style="font-size:0.65rem;color:#2e4a6a;text-transform:uppercase;
                            letter-spacing:0.1em;font-weight:600;margin-bottom:0.5rem;">
                            📝 Anotações
                        </div>
                        <div style="font-size:0.82rem;color:#8aabcc;line-height:1.6;white-space:pre-line;">
                            {chr(10).join(desc_lines[:8])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with col_r:
                if rotulos:
                    tags = [t.strip() for t in rotulos.split(';') if t.strip()]
                    tags_html = "".join([
                        f'<span style="background:#1a2a3d;border:1px solid #2a4060;color:#60a5fa;'
                        f'border-radius:20px;padding:0.2rem 0.7rem;font-size:0.72rem;'
                        f'font-weight:500;margin:0.15rem;display:inline-block;">{t}</span>'
                        for t in tags
                    ])
                    st.markdown(f"""
                    <div style="background:#0f1117;border:1px solid #1e2d45;border-radius:10px;
                        padding:1rem 1.2rem;margin-bottom:1rem;">
                        <div style="font-size:0.65rem;color:#2e4a6a;text-transform:uppercase;
                            letter-spacing:0.1em;font-weight:600;margin-bottom:0.6rem;">
                            🏷️ Rótulos
                        </div>
                        {tags_html}
                    </div>
                    """, unsafe_allow_html=True)

    # ── Action buttons ────────────────────────────────────────────────────────
    col_a1, col_a2, col_a3, _ = st.columns([1, 1, 1, 4])
    with col_a1:
        if require_role("admin", "gestor"):
            if st.button("✏️ Editar Projeto", use_container_width=True):
                st.session_state["editing_proj_inline"] = p.id
    with col_a2:
        if st.button("➕ Nova Tarefa", use_container_width=True, type="primary"):
            st.session_state["creating_task_for"] = p.id
    with col_a3:
        if st.session_state.get("creating_task_for") == p.id or st.session_state.get("editing_task_id"):
            if st.button("✕ Fechar formulário", use_container_width=True):
                st.session_state.pop("creating_task_for", None)
                st.session_state.pop("editing_task_id", None)
                st.rerun()

    # ── Inline edit project form ──────────────────────────────────────────────
    if st.session_state.get("editing_proj_inline") == p.id:
        _edit_project_inline(p, db)

    # ── Create task form ──────────────────────────────────────────────────────
    if st.session_state.get("creating_task_for") == p.id:
        _create_task_form(p, db)

    # ── Edit task form ────────────────────────────────────────────────────────
    edit_tid = st.session_state.get("editing_task_id")

    # ── Checklist section (tasks as checklist, like Planner) ─────────────────
    st.markdown(f"""
    <div style="font-size:0.75rem;color:#4a6a8a;font-weight:600;
        text-transform:uppercase;letter-spacing:0.1em;
        margin:1.2rem 0 0.7rem;padding-bottom:0.4rem;border-bottom:1px solid #1e2d45;">
        ✅ Lista de verificação &nbsp;
        <span style="color:#3b9eff;background:#0d2137;border-radius:4px;
            padding:0.1rem 0.5rem;font-size:0.7rem;">{n_done} / {n_tasks}</span>
    </div>
    """, unsafe_allow_html=True)

    if not p.tarefas:
        st.markdown("""
        <div style="text-align:center;padding:2rem;color:#2e4a6a;">
            <div style="font-size:1.5rem">📭</div>
            <div style="margin-top:0.4rem;font-size:0.85rem">Nenhuma tarefa. Clique em "Nova Tarefa" para começar.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Sort: overdue first, then by status, then by deadline
        def sort_key(t):
            is_over = 1 if (t.prazo and t.prazo < now and t.status != "Concluído") else 0
            s_order = {"Em Andamento": 0, "A Fazer": 1, "Concluído": 2}.get(t.status, 1)
            prazo_ts = t.prazo.timestamp() if t.prazo else 9999999999
            return (-is_over, s_order, prazo_ts)

        tarefas_sorted = sorted(p.tarefas, key=sort_key)

        for t in tarefas_sorted:
            _task_row(t, p, db, now, edit_tid)

    st.markdown("---")


def _task_row(t, p, db, now, edit_tid):
    """Render a single task row in Planner checklist style."""
    is_done = t.status == "Concluído"
    is_late = t.prazo and t.prazo < now and not is_done

    tcfg = TASK_STATUS_CFG.get(t.status, TASK_STATUS_CFG["A Fazer"])
    pcfg = PRIO_CFG.get(t.prioridade, PRIO_CFG["Média"])

    resp_nome = t.responsavel_user.nome if t.responsavel_user else "—"
    prazo_str = t.prazo.strftime("%d/%m/%Y") if t.prazo else "Sem prazo"
    dias_atraso = (now - t.prazo).days if is_late else 0

    titulo_style = "text-decoration:line-through;opacity:0.5;" if is_done else ""

    late_html = ""
    if is_late:
        if dias_atraso > 30:
            lc = "#ff4444"
        elif dias_atraso > 7:
            lc = "#ff8c42"
        else:
            lc = "#fbbf24"
        late_html = f'<span style="color:{lc};font-size:0.7rem;font-weight:700;margin-left:0.4rem;">⚠ {dias_atraso}d</span>'

    # Checkbox icon
    ck = "☑" if is_done else "○"
    ck_col = "#10b981" if is_done else "#3a5a7a"

    row_bg = "#0d2118" if is_done else ("#1f0d0d" if is_late else "#161b27")
    row_border = "#1a6040" if is_done else ("#aa222244" if is_late else "#1e2d45")
    left_color = tcfg["color"]

    row_html = f"""
    <div style="background:{row_bg};border:1px solid {row_border};
        border-left:3px solid {left_color};border-radius:8px;
        padding:0.65rem 1rem;margin-bottom:0.35rem;
        display:flex;align-items:center;gap:0.8rem;flex-wrap:wrap;">

        <span style="font-size:1rem;color:{ck_col};flex-shrink:0;">{ck}</span>

        <div style="flex:1;min-width:150px;">
            <span style="font-size:0.88rem;color:#c8d6f0;font-weight:500;{titulo_style}">
                {t.titulo}
            </span>
            {late_html}
        </div>

        <div style="display:flex;gap:0.7rem;align-items:center;flex-wrap:wrap;">
            <span style="background:{pcfg['bg']};color:{pcfg['color']};
                border-radius:4px;padding:0.1rem 0.5rem;font-size:0.68rem;font-weight:600;">
                {t.prioridade}
            </span>
            <span style="color:#4a6a8a;font-size:0.73rem;">👤 {resp_nome}</span>
            <span style="color:{'#ff6b6b' if is_late else '#4a6a8a'};font-size:0.73rem;">
                📅 {prazo_str}
            </span>
        </div>
    </div>
    """
    st.markdown(row_html, unsafe_allow_html=True)

    # Action buttons (compact)
    col_st, col_e, col_d, _ = st.columns([2, 0.5, 0.5, 6])
    with col_st:
        opts = ["A Fazer", "Em Andamento", "Concluído"]
        idx = opts.index(t.status) if t.status in opts else 0
        new_s = st.selectbox("", opts, index=idx, key=f"ts_{t.id}", label_visibility="collapsed")
        if new_s != t.status:
            t.status = new_s
            t.atualizado_em = datetime.now()
            # Update project progress
            n_done_new = sum(1 for x in p.tarefas if (x.id == t.id and new_s == "Concluído") or
                             (x.id != t.id and x.status == "Concluído"))
            n_total = len(p.tarefas)
            p.progresso = (n_done_new / n_total * 100) if n_total else 0
            db.commit(); st.rerun()
    with col_e:
        if st.button("✏", key=f"te_{t.id}", help="Editar"):
            st.session_state["editing_task_id"] = t.id; st.rerun()
    with col_d:
        if st.button("✕", key=f"td_{t.id}", help="Excluir"):
            db.delete(t)
            # recalc progress
            remaining = [x for x in p.tarefas if x.id != t.id]
            done = sum(1 for x in remaining if x.status == "Concluído")
            p.progresso = (done / len(remaining) * 100) if remaining else 0
            db.commit(); st.rerun()

    # Inline edit form
    if st.session_state.get("editing_task_id") == t.id:
        _edit_task_inline(t, p, db)


# ── Forms ─────────────────────────────────────────────────────────────────────

def _create_task_form(p, db):
    st.markdown("""
    <div style="background:#0f1117;border:1px solid #2a4060;border-radius:12px;
        padding:1.2rem 1.4rem;margin:0.8rem 0;">
        <div style="font-size:0.72rem;color:#3b9eff;font-weight:600;
            text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.8rem;">
            ➕ Nova Tarefa
        </div>
    </div>
    """, unsafe_allow_html=True)

    users = db.query(User).order_by(User.nome).all()
    u_map = {u.nome: u.id for u in users}

    with st.form(f"new_task_{p.id}"):
        titulo = st.text_input("Título *", placeholder="Descreva a tarefa...")
        descricao = st.text_area("Descrição", placeholder="Detalhes opcionais...", height=80)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            responsavel = st.selectbox("Responsável", list(u_map.keys()))
        with c2:
            status = st.selectbox("Status", ["A Fazer", "Em Andamento", "Concluído"])
        with c3:
            prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Crítica"], index=1)
        with c4:
            prazo = st.date_input("Prazo")

        sub = st.form_submit_button("✅ Criar Tarefa", type="primary", use_container_width=True)
        if sub:
            if not titulo:
                st.error("Título obrigatório")
            else:
                t = Task(
                    titulo=titulo, descricao=descricao,
                    projeto_id=p.id, responsavel_id=u_map.get(responsavel),
                    status=status, prioridade=prioridade,
                    prazo=datetime.combine(prazo, datetime.min.time()) if prazo else None,
                )
                db.add(t)
                n_done = sum(1 for x in p.tarefas if x.status == "Concluído") + (1 if status == "Concluído" else 0)
                n_total = len(p.tarefas) + 1
                p.progresso = n_done / n_total * 100
                db.commit()
                st.session_state.pop("creating_task_for", None)
                st.success(f"✅ Tarefa '{titulo}' criada!")
                st.rerun()


def _edit_task_inline(t, p, db):
    st.markdown("""
    <div style="background:#0f1117;border:1px solid #2a4060;border-radius:10px;
        padding:1rem 1.2rem;margin:0.4rem 0 0.8rem;">
        <div style="font-size:0.68rem;color:#3b9eff;font-weight:600;
            text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.6rem;">
            ✏️ Editando tarefa
        </div>
    </div>
    """, unsafe_allow_html=True)

    users = db.query(User).order_by(User.nome).all()
    u_map = {u.nome: u.id for u in users}
    u_names = [u.nome for u in users]
    curr_resp = next((u.nome for u in users if u.id == t.responsavel_id), u_names[0])

    with st.form(f"edit_task_form_{t.id}"):
        titulo = st.text_input("Título", value=t.titulo)
        descricao = st.text_area("Descrição", value=t.descricao or "", height=70)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            responsavel = st.selectbox("Responsável", u_names,
                                       index=u_names.index(curr_resp) if curr_resp in u_names else 0)
        with c2:
            opts = ["A Fazer", "Em Andamento", "Concluído"]
            status = st.selectbox("Status", opts, index=opts.index(t.status) if t.status in opts else 0)
        with c3:
            prios = ["Baixa", "Média", "Alta", "Crítica"]
            prioridade = st.selectbox("Prioridade", prios,
                                      index=prios.index(t.prioridade) if t.prioridade in prios else 1)
        with c4:
            prazo = st.date_input("Prazo", value=t.prazo.date() if t.prazo else None)

        cs, cc = st.columns(2)
        with cs:
            sub = st.form_submit_button("💾 Salvar", type="primary", use_container_width=True)
        with cc:
            cancel = st.form_submit_button("Cancelar", use_container_width=True)

        if sub:
            t.titulo = titulo; t.descricao = descricao
            t.responsavel_id = u_map.get(responsavel)
            t.status = status; t.prioridade = prioridade
            t.prazo = datetime.combine(prazo, datetime.min.time()) if prazo else None
            t.atualizado_em = datetime.now()
            n_done = sum(1 for x in p.tarefas if (x.id == t.id and status == "Concluído") or
                         (x.id != t.id and x.status == "Concluído"))
            p.progresso = (n_done / len(p.tarefas) * 100) if p.tarefas else 0
            db.commit()
            st.session_state.pop("editing_task_id", None)
            st.success("✅ Salvo!"); st.rerun()
        if cancel:
            st.session_state.pop("editing_task_id", None); st.rerun()


def _edit_project_inline(p, db):
    st.markdown("""
    <div style="background:#0f1117;border:1px solid #2a4060;border-radius:12px;
        padding:1.2rem 1.4rem;margin:0.8rem 0;">
        <div style="font-size:0.72rem;color:#3b9eff;font-weight:600;
            text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.8rem;">
            ✏️ Editando Projeto
        </div>
    </div>
    """, unsafe_allow_html=True)

    users = db.query(User).order_by(User.nome).all()
    u_map = {u.nome: u.id for u in users}
    u_names = [u.nome for u in users]
    curr_resp = next((u.nome for u in users if u.id == p.responsavel_id), u_names[0] if u_names else "")

    with st.form(f"edit_proj_{p.id}"):
        nome = st.text_input("Nome", value=p.nome)
        descricao = st.text_area("Descrição / Anotações", value=p.descricao or "", height=100)
        c1, c2 = st.columns(2)
        with c1:
            responsavel = st.selectbox("Responsável", u_names,
                                       index=u_names.index(curr_resp) if curr_resp in u_names else 0)
            di = st.date_input("Início", value=p.data_inicio.date() if p.data_inicio else None)
            status_opts = ["Planejamento", "Ativo", "Pausado", "Concluído", "Cancelado"]
            status = st.selectbox("Status", status_opts,
                                  index=status_opts.index(p.status) if p.status in status_opts else 0)
        with c2:
            df_ = st.date_input("Conclusão", value=p.data_fim.date() if p.data_fim else None)
            progresso = st.slider("Progresso (%)", 0, 100, int(p.progresso))

        cs, cc = st.columns(2)
        with cs:
            sub = st.form_submit_button("💾 Salvar", type="primary", use_container_width=True)
        with cc:
            cancel = st.form_submit_button("Cancelar", use_container_width=True)

        if sub:
            p.nome = nome; p.descricao = descricao
            p.responsavel_id = u_map.get(responsavel)
            p.data_inicio = datetime.combine(di, datetime.min.time()) if di else None
            p.data_fim = datetime.combine(df_, datetime.min.time()) if df_ else None
            p.status = status; p.progresso = float(progresso)
            p.atualizado_em = datetime.now()
            db.commit()
            st.session_state.pop("editing_proj_inline", None)
            st.success("✅ Projeto atualizado!"); st.rerun()
        if cancel:
            st.session_state.pop("editing_proj_inline", None); st.rerun()


def _create_project_form(db):
    st.markdown("""
    <div style="background:#0f1117;border:1px solid #2a4060;border-radius:12px;
        padding:1.2rem 1.4rem;margin:0.8rem 0 1.2rem;">
        <div style="font-size:0.72rem;color:#3b9eff;font-weight:600;
            text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.8rem;">
            ➕ Novo Projeto
        </div>
    </div>
    """, unsafe_allow_html=True)

    users = db.query(User).order_by(User.nome).all()
    u_map = {u.nome: u.id for u in users}

    with st.form("create_project_form"):
        nome = st.text_input("Nome do Projeto *", placeholder="Ex: Treinamento XYZ [HRC1234567]")
        descricao = st.text_area("Descrição / Anotações", placeholder="Informações do projeto...", height=80)
        c1, c2 = st.columns(2)
        with c1:
            responsavel = st.selectbox("Responsável", list(u_map.keys()))
            di = st.date_input("Início")
            status = st.selectbox("Status", ["Planejamento", "Ativo"])
        with c2:
            df_ = st.date_input("Conclusão")
            progresso = st.slider("Progresso (%)", 0, 100, 0)

        cs, cc = st.columns(2)
        with cs:
            sub = st.form_submit_button("🚀 Criar Projeto", type="primary", use_container_width=True)
        with cc:
            cancel = st.form_submit_button("Cancelar", use_container_width=True)

        if sub:
            if not nome:
                st.error("Nome obrigatório.")
            else:
                proj = Project(
                    nome=nome, descricao=descricao,
                    responsavel_id=u_map.get(responsavel),
                    data_inicio=datetime.combine(di, datetime.min.time()),
                    data_fim=datetime.combine(df_, datetime.min.time()),
                    status=status, progresso=float(progresso)
                )
                db.add(proj); db.commit()
                st.session_state.pop("creating_project", None)
                st.success(f"✅ Projeto '{nome}' criado!"); st.rerun()
        if cancel:
            st.session_state.pop("creating_project", None); st.rerun()


def _has_overdue_tasks(p, now):
    return any(t.prazo and t.prazo < now and t.status != "Concluído" for t in p.tarefas)

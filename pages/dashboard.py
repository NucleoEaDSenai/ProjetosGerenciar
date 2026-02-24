import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
from database import get_db
from models import Project, Task, User


STATUS_COLORS = {
    "Ativo":        {"bg": "#0d2137", "border": "#1d6fa4", "text": "#60b8ff", "dot": "#3b9eff"},
    "Concluído":    {"bg": "#0d2118", "border": "#1d7a4a", "text": "#34d399", "dot": "#10b981"},
    "Planejamento": {"bg": "#1f1a08", "border": "#7a5a10", "text": "#fbbf24", "dot": "#f59e0b"},
    "Cancelado":    {"bg": "#1f0d0d", "border": "#7a2020", "text": "#f87171", "dot": "#ef4444"},
    "Pausado":      {"bg": "#151520", "border": "#3a3a5a", "text": "#94a3b8", "dot": "#64748b"},
}


def show():
    db = get_db()
    try:
        now = datetime.now()
        all_projects = db.query(Project).all()

        total = len(all_projects)
        ativos     = sum(1 for p in all_projects if p.status == "Ativo")
        concluidos = sum(1 for p in all_projects if p.status == "Concluído")
        planej     = sum(1 for p in all_projects if p.status == "Planejamento")
        cancelados = sum(1 for p in all_projects if p.status == "Cancelado")

        # Projetos com tarefas atrasadas
        proj_atrasados = []
        for p in all_projects:
            if p.status == "Concluído":
                continue
            tasks_atrasadas = [
                t for t in p.tarefas
                if t.prazo and t.prazo < now and t.status != "Concluído"
            ]
            if tasks_atrasadas:
                max_atraso = max((now - t.prazo).days for t in tasks_atrasadas)
                proj_atrasados.append((p, len(tasks_atrasadas), max_atraso))

        n_atrasados = len(proj_atrasados)

        # ── Header ─────────────────────────────────────────────────────────────
        st.markdown("""
        <div style="margin-bottom:1.5rem;">
            <div style="font-size:0.72rem;color:#4a7fa5;text-transform:uppercase;letter-spacing:0.12em;font-weight:600;">Petrobras / Senai EaD</div>
            <h1 style="font-size:1.8rem;font-weight:700;color:#e2f0ff;margin:0.2rem 0 0.3rem;letter-spacing:-0.5px;">Dashboard</h1>
            <div style="font-size:0.82rem;color:#4a6a8a;">Visão geral · Atualizado em {}</div>
        </div>
        """.format(now.strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)

        # ── KPI Cards ──────────────────────────────────────────────────────────
        c1, c2, c3, c4, c5 = st.columns(5)
        _kpi_card(c1, str(total),      "Total de Projetos",  "#2a4a7a", "#3b82f6", "📁")
        _kpi_card(c2, str(ativos),     "Ativos",             "#0d2137", "#3b9eff", "🟢")
        _kpi_card(c3, str(concluidos), "Concluídos",         "#0d2118", "#10b981", "✅")
        _kpi_card(c4, str(planej),     "Planejamento",       "#1f1a08", "#f59e0b", "🟡")

        # Card de atrasados com destaque vermelho
        with c5:
            bg = "#2d0d0d" if n_atrasados > 0 else "#151520"
            border = "#aa2020" if n_atrasados > 0 else "#2a3a54"
            txt_col = "#ff6b6b" if n_atrasados > 0 else "#94a3b8"
            icon = "🔴" if n_atrasados > 0 else "✅"
            st.markdown(f"""
            <div style="background:{bg};border:1.5px solid {border};border-radius:14px;
                padding:1.1rem 1.2rem;min-height:90px;">
                <div style="font-size:0.75rem;color:{txt_col};font-weight:600;margin-bottom:0.4rem;">{icon} Com Atraso</div>
                <div style="font-size:2.2rem;font-weight:700;color:{txt_col};line-height:1;">{n_atrasados}</div>
                <div style="font-size:0.7rem;color:#5a3a3a;margin-top:0.3rem;">
                    {"projetos com tarefas vencidas" if n_atrasados > 0 else "tudo em dia 🎉"}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        # ── Charts row ─────────────────────────────────────────────────────────
        col_l, col_r = st.columns([3, 2])

        with col_l:
            _section_header("📊 Distribuição por Status")
            # Bar chart — projects grouped by status
            status_data = {}
            for p in all_projects:
                status_data[p.status] = status_data.get(p.status, 0) + 1

            colors_bar = {
                "Ativo": "#3b9eff", "Concluído": "#10b981",
                "Planejamento": "#f59e0b", "Cancelado": "#ef4444", "Pausado": "#64748b"
            }
            df_bar = pd.DataFrame([
                {"Status": k, "Projetos": v, "Cor": colors_bar.get(k, "#6366f1")}
                for k, v in status_data.items()
            ])
            fig = px.bar(df_bar, x="Status", y="Projetos", color="Status",
                         color_discrete_map=colors_bar, text="Projetos")
            fig.update_traces(textposition="outside", textfont=dict(color="#c8d6f0", size=13))
            fig.update_layout(
                height=260, showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0),
                font=dict(color="#8aabcc", size=12),
                xaxis=dict(gridcolor="#1e2d45", linecolor="#1e2d45"),
                yaxis=dict(gridcolor="#1e2d45", linecolor="#1e2d45"),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            _section_header("🍩 Progresso Geral")
            # Donut — tasks status
            all_tasks = db.query(Task).all()
            a_fazer = sum(1 for t in all_tasks if t.status == "A Fazer")
            em_and  = sum(1 for t in all_tasks if t.status == "Em Andamento")
            conc    = sum(1 for t in all_tasks if t.status == "Concluído")
            total_t = a_fazer + em_and + conc

            if total_t > 0:
                fig2 = go.Figure(data=[go.Pie(
                    labels=["A Fazer", "Em Andamento", "Concluído"],
                    values=[a_fazer, em_and, conc],
                    hole=0.6,
                    marker=dict(
                        colors=["#f59e0b", "#3b9eff", "#10b981"],
                        line=dict(color="#0f1117", width=3)
                    ),
                    textinfo="percent",
                    textfont=dict(size=12, color="#c8d6f0"),
                )])
                pct_conc = int(conc / total_t * 100) if total_t else 0
                fig2.add_annotation(
                    text=f"<b>{pct_conc}%</b><br><span style='font-size:10px'>concluído</span>",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=18, color="#c8d6f0"), align="center"
                )
                fig2.update_layout(
                    height=260, showlegend=True,
                    legend=dict(orientation="h", x=0, y=-0.1, font=dict(color="#8aabcc", size=11)),
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=10, b=30),
                )
                st.plotly_chart(fig2, use_container_width=True)

        # ── Projetos atrasados ──────────────────────────────────────────────────
        if proj_atrasados:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            _section_header("🔴 Projetos com Tarefas Atrasadas")

            proj_atrasados_sorted = sorted(proj_atrasados, key=lambda x: x[2], reverse=True)
            for p, n_tasks, max_dias in proj_atrasados_sorted[:15]:
                resp_nome = p.responsavel_user.nome if p.responsavel_user else "—"
                # Urgency color
                if max_dias > 30:
                    urg_bg, urg_col = "#2d0808", "#ff4444"
                elif max_dias > 7:
                    urg_bg, urg_col = "#2a1508", "#ff8c42"
                else:
                    urg_bg, urg_col = "#1f1a08", "#fbbf24"

                st.markdown(f"""
                <div style="background:#161b27;border:1px solid #2a1a1a;border-left:4px solid {urg_col};
                    border-radius:10px;padding:0.8rem 1rem;margin-bottom:0.5rem;
                    display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">
                    <div style="flex:1;min-width:200px;">
                        <div style="font-size:0.85rem;font-weight:600;color:#e2f0ff;
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:500px;">
                            {p.nome}
                        </div>
                        <div style="font-size:0.73rem;color:#6a8aaa;margin-top:0.2rem;">
                            👤 {resp_nome} &nbsp;·&nbsp; {n_tasks} tarefa(s) vencida(s)
                        </div>
                    </div>
                    <div style="background:{urg_bg};border:1px solid {urg_col}33;
                        border-radius:8px;padding:0.3rem 0.8rem;text-align:center;">
                        <div style="font-size:1.1rem;font-weight:700;color:{urg_col};">{max_dias}d</div>
                        <div style="font-size:0.63rem;color:{urg_col};opacity:0.8;">de atraso</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Tabela resumo por responsável ──────────────────────────────────────
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        _section_header("👥 Projetos por Responsável")

        resp_map = {}
        for p in all_projects:
            resp = p.responsavel_user.nome if p.responsavel_user else "Sem responsável"
            if resp not in resp_map:
                resp_map[resp] = {"Ativo": 0, "Concluído": 0, "Planejamento": 0, "Cancelado": 0, "Total": 0}
            resp_map[resp][p.status] = resp_map[resp].get(p.status, 0) + 1
            resp_map[resp]["Total"] += 1

        df_resp = pd.DataFrame([
            {"Responsável": k, **v} for k, v in resp_map.items()
        ]).sort_values("Total", ascending=False)

        st.dataframe(
            df_resp,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Responsável": st.column_config.TextColumn("👤 Responsável", width=220),
                "Total": st.column_config.NumberColumn("Total", width=80),
                "Ativo": st.column_config.NumberColumn("🟢 Ativos", width=90),
                "Concluído": st.column_config.NumberColumn("✅ Concluídos", width=110),
                "Planejamento": st.column_config.NumberColumn("🟡 Planej.", width=100),
                "Cancelado": st.column_config.NumberColumn("❌ Cancelados", width=110),
            }
        )

    finally:
        db.close()


def _kpi_card(col, value, label, bg, color, icon):
    with col:
        st.markdown(f"""
        <div style="background:{bg};border:1.5px solid {color}44;border-radius:14px;
            padding:1.1rem 1.2rem;min-height:90px;">
            <div style="font-size:0.75rem;color:{color};font-weight:600;margin-bottom:0.4rem;">{icon} {label}</div>
            <div style="font-size:2.2rem;font-weight:700;color:{color};line-height:1;">{value}</div>
        </div>
        """, unsafe_allow_html=True)


def _section_header(title):
    st.markdown(f"""
    <div style="font-size:0.82rem;font-weight:700;color:#8aabcc;
        text-transform:uppercase;letter-spacing:0.08em;
        margin:0.2rem 0 0.8rem;padding-bottom:0.4rem;
        border-bottom:1px solid #1e2d45;">
        {title}
    </div>
    """, unsafe_allow_html=True)

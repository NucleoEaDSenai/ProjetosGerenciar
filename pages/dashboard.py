import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from database import get_db
from models import Project, Task, User


def show():
    st.markdown("## 📊 Dashboard")
    st.markdown("---")

    db = get_db()
    try:
        now = datetime.now()

        # KPIs
        total_projetos = db.query(Project).count()
        projetos_ativos = db.query(Project).filter(Project.status == "Ativo").count()
        tarefas_pendentes = db.query(Task).filter(Task.status != "Concluído").count()
        tarefas_atrasadas = db.query(Task).filter(
            Task.prazo < now, Task.status != "Concluído"
        ).count()
        tarefas_concluidas = db.query(Task).filter(Task.status == "Concluído").count()
        total_tarefas = db.query(Task).count()

        # Metrics row
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("📁 Total de Projetos", total_projetos, delta=None)
        with c2:
            st.metric("🟢 Projetos Ativos", projetos_ativos,
                      delta=f"{projetos_ativos}/{total_projetos} ativos")
        with c3:
            st.metric("⏳ Tarefas Pendentes", tarefas_pendentes,
                      delta=f"{tarefas_concluidas} concluídas")
        with c4:
            st.metric("🔴 Tarefas Atrasadas", tarefas_atrasadas,
                      delta=f"{'⚠️ Atenção!' if tarefas_atrasadas > 0 else '✅ Em dia'}",
                      delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)

        col_left, col_right = st.columns([3, 2])

        with col_left:
            # Projects progress chart
            st.markdown("### 📈 Progresso dos Projetos")
            projects = db.query(Project).all()
            if projects:
                df_proj = pd.DataFrame([{
                    "Projeto": p.nome[:30] + "..." if len(p.nome) > 30 else p.nome,
                    "Progresso": p.progresso,
                    "Status": p.status
                } for p in projects])

                color_map = {
                    "Ativo": "#6366f1",
                    "Concluído": "#10b981",
                    "Planejamento": "#f59e0b",
                    "Pausado": "#64748b",
                    "Cancelado": "#ef4444"
                }

                fig = px.bar(
                    df_proj, x="Progresso", y="Projeto",
                    orientation="h",
                    color="Status",
                    color_discrete_map=color_map,
                    range_x=[0, 100],
                    text="Progresso"
                )
                fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
                fig.update_layout(
                    height=300,
                    margin=dict(l=0, r=20, t=10, b=0),
                    showlegend=True,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(size=12),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", title="")
                fig.update_yaxes(title="")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum projeto cadastrado ainda.")

        with col_right:
            # Tasks status donut
            st.markdown("### 🍩 Status das Tarefas")
            if total_tarefas > 0:
                a_fazer = db.query(Task).filter(Task.status == "A Fazer").count()
                em_andamento = db.query(Task).filter(Task.status == "Em Andamento").count()

                labels = ["A Fazer", "Em Andamento", "Concluído"]
                values = [a_fazer, em_andamento, tarefas_concluidas]
                colors = ["#f59e0b", "#6366f1", "#10b981"]

                fig2 = go.Figure(data=[go.Pie(
                    labels=labels, values=values,
                    hole=0.55,
                    marker=dict(colors=colors, line=dict(color="#fff", width=2)),
                    textinfo="label+percent",
                    textfont=dict(size=11)
                )])
                fig2.update_layout(
                    height=300,
                    margin=dict(l=0, r=0, t=10, b=0),
                    showlegend=False,
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Nenhuma tarefa cadastrada.")

        # Overdue tasks
        if tarefas_atrasadas > 0:
            st.markdown("### 🔴 Tarefas em Atraso")
            atrasadas = db.query(Task).filter(
                Task.prazo < now, Task.status != "Concluído"
            ).all()

            data = []
            for t in atrasadas:
                dias = (now - t.prazo).days
                data.append({
                    "📌 Tarefa": t.titulo,
                    "📁 Projeto": t.projeto.nome if t.projeto else "-",
                    "👤 Responsável": t.responsavel_user.nome if t.responsavel_user else "-",
                    "📅 Prazo": t.prazo.strftime("%d/%m/%Y"),
                    "⏰ Atraso": f"{dias} dia(s)",
                    "🎯 Prioridade": t.prioridade,
                })
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

        # Recent projects
        st.markdown("### 🕐 Projetos Recentes")
        projetos_recentes = db.query(Project).order_by(Project.criado_em.desc()).limit(5).all()
        if projetos_recentes:
            data_proj = []
            for p in projetos_recentes:
                status_icon = {"Ativo": "🟢", "Concluído": "✅", "Planejamento": "🟡",
                               "Pausado": "⏸️", "Cancelado": "❌"}.get(p.status, "⚪")
                data_proj.append({
                    "📁 Projeto": p.nome,
                    "Status": f"{status_icon} {p.status}",
                    "📈 Progresso": f"{p.progresso:.0f}%",
                    "👤 Responsável": p.responsavel_user.nome if p.responsavel_user else "-",
                    "📅 Prazo": p.data_fim.strftime("%d/%m/%Y") if p.data_fim else "-",
                })
            st.dataframe(pd.DataFrame(data_proj), use_container_width=True, hide_index=True)

    finally:
        db.close()

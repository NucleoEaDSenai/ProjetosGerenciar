# 🚀 ProjectFlow — Gerenciamento de Projetos

Aplicação web completa de gerenciamento de projetos construída com **Python + Streamlit + SQLite**.

---

## 📁 Estrutura do Projeto

```
project_manager/
│
├── app.py              # Ponto de entrada + layout + roteamento
├── database.py         # Conexão SQLite, SessionLocal, seed de dados
├── models.py           # Modelos SQLAlchemy (User, Project, Task)
├── auth.py             # Autenticação, sessão, login/logout
│
├── pages/
│   ├── __init__.py
│   ├── dashboard.py    # KPIs + gráficos + tarefas atrasadas
│   ├── projetos.py     # CRUD de projetos
│   ├── tarefas.py      # CRUD de tarefas
│   └── kanban.py       # Board Kanban com drag via botões
│
├── requirements.txt
└── README.md
```

---

## 🛠️ Instalação e execução local

### Pré-requisitos
- Python 3.11+
- pip

### Passo a passo

```bash
# 1. Clone ou descompacte o projeto
cd project_manager

# 2. Crie e ative um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Inicie a aplicação
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

> ℹ️ O banco de dados `project_manager.db` é criado automaticamente na primeira execução, com dados de demonstração incluídos.

---

## 🔑 Contas de Acesso (Demo)

| E-mail | Senha | Perfil |
|---|---|---|
| admin@demo.com | admin123 | Admin |
| gestor@demo.com | gestor123 | Gestor |
| colab@demo.com | colab123 | Colaborador |
| ana@demo.com | ana123 | Colaborador |

---

## 🌩️ Deploy no Streamlit Cloud

1. Faça upload do projeto para um repositório **GitHub** (público ou privado)
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Clique em **New app**
4. Selecione o repositório e defina:
   - **Branch:** main
   - **Main file path:** `app.py`
5. Clique em **Deploy!**

> ⚠️ **Atenção:** O SQLite no Streamlit Cloud usa armazenamento efêmero — os dados são reiniciados a cada redeploy. Para persistência permanente em produção, migre para **PostgreSQL** (Supabase, Railway, etc.) e ajuste a `DATABASE_URL` em `database.py`.

---

## ✨ Funcionalidades

### 🔐 Autenticação
- Login com e-mail e senha (bcrypt)
- Sessão via `st.session_state`
- Logout com limpeza de sessão
- 3 perfis: **Admin**, **Gestor**, **Colaborador**

### 📊 Dashboard
- KPIs: total de projetos, projetos ativos, tarefas pendentes, tarefas atrasadas
- Gráfico de barras horizontais com progresso por projeto
- Gráfico donut de status das tarefas
- Lista de tarefas em atraso com alerta
- Projetos recentes

### 📁 Projetos
- Criar, editar e excluir projetos
- Campos: nome, descrição, responsável, data início/fim, status, progresso
- Filtro por nome e status
- Indicador visual de atraso
- Confirmação antes de excluir

### ✅ Tarefas
- Criar, editar e excluir tarefas
- Campos: título, descrição, projeto, responsável, status, prioridade, prazo
- Troca rápida de status no card
- Filtros por projeto, status e prioridade
- Indicador de tarefas atrasadas

### 🗂️ Kanban
- Board com 3 colunas: A Fazer | Em Andamento | Concluído
- Cards coloridos por prioridade
- Filtro por projeto
- Botões para mover tarefas entre colunas
- Badges de prioridade e atraso

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────┐
│             app.py                  │  ← Entry point, CSS global, sidebar
│   (st.set_page_config + roteamento) │
└──────────┬──────────────────────────┘
           │ importa
    ┌──────┴───────────────────────────────────┐
    │  pages/               auth.py            │
    │  ├── dashboard.py     models.py          │
    │  ├── projetos.py      database.py        │
    │  ├── tarefas.py                          │
    │  └── kanban.py                           │
    └──────────────────────────────────────────┘
                    │
              SQLite via SQLAlchemy
```

---

## 📦 Dependências

| Pacote | Uso |
|---|---|
| streamlit | Framework web |
| sqlalchemy | ORM / SQLite |
| plotly | Gráficos interativos |
| pandas | Manipulação de dados |
| bcrypt | Hash de senhas |

---

## 🔧 Personalização

- **Trocar banco de dados:** altere `DATABASE_URL` em `database.py`
- **Adicionar páginas:** crie em `pages/` e registre no roteador em `app.py`
- **Ajustar cores:** edite o CSS no bloco `st.markdown("""<style>...""")` em `app.py`
- **Adicionar campos:** altere os modelos em `models.py` e rode `Base.metadata.create_all()` novamente

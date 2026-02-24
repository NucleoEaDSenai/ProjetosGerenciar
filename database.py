from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Project, Task
import bcrypt
from datetime import datetime, timedelta
import os

DATABASE_URL = "sqlite:///./project_manager.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def init_db():
    """Initialize database and create tables."""
    Base.metadata.create_all(bind=engine)
    seed_data()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    # Support sha256 fallback hashes (when bcrypt not available at seed time)
    if hashed.startswith("sha256$"):
        import hashlib
        _, salt, h = hashed.split("$")
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def seed_data():
    """Create initial data if database is empty."""
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return  # Already seeded (either demo or Petrobras import)

        # Create default users
        users = [
            User(nome="Admin Sistema", email="admin@demo.com",
                 senha_hash=hash_password("admin123"), role="admin", avatar_color="#6366f1"),
            User(nome="Maria Gestora", email="gestor@demo.com",
                 senha_hash=hash_password("gestor123"), role="gestor", avatar_color="#10b981"),
            User(nome="João Colaborador", email="colab@demo.com",
                 senha_hash=hash_password("colab123"), role="colaborador", avatar_color="#f59e0b"),
            User(nome="Ana Silva", email="ana@demo.com",
                 senha_hash=hash_password("ana123"), role="colaborador", avatar_color="#ef4444"),
        ]
        db.add_all(users)
        db.commit()
        for u in users:
            db.refresh(u)

        # Create sample projects
        hoje = datetime.now()
        projects = [
            Project(nome="Portal do Aluno v2.0", descricao="Redesign completo do portal do aluno com nova identidade visual e funcionalidades aprimoradas.",
                    responsavel_id=users[1].id, data_inicio=hoje - timedelta(days=30),
                    data_fim=hoje + timedelta(days=60), status="Ativo", progresso=45.0),
            Project(nome="Curso EAD: Python para Educação", descricao="Desenvolvimento de curso online de Python voltado para profissionais da educação.",
                    responsavel_id=users[1].id, data_inicio=hoje - timedelta(days=10),
                    data_fim=hoje + timedelta(days=90), status="Ativo", progresso=20.0),
            Project(nome="Integração LMS-ERP", descricao="Integração do Moodle com o sistema ERP institucional para sincronização de dados.",
                    responsavel_id=users[0].id, data_inicio=hoje - timedelta(days=60),
                    data_fim=hoje - timedelta(days=5), status="Concluído", progresso=100.0),
            Project(nome="App Mobile Institucional", descricao="Aplicativo mobile para acesso às funcionalidades institucionais.",
                    responsavel_id=users[1].id, data_inicio=hoje + timedelta(days=10),
                    data_fim=hoje + timedelta(days=120), status="Planejamento", progresso=5.0),
        ]
        db.add_all(projects)
        db.commit()
        for p in projects:
            db.refresh(p)

        # Create sample tasks
        tasks = [
            # Project 1 tasks
            Task(titulo="Levantamento de requisitos", descricao="Reunir requisitos com stakeholders e usuários finais.",
                 projeto_id=projects[0].id, responsavel_id=users[2].id, status="Concluído",
                 prioridade="Alta", prazo=hoje - timedelta(days=20)),
            Task(titulo="Wireframes das telas principais", descricao="Criar wireframes para as 10 telas principais do portal.",
                 projeto_id=projects[0].id, responsavel_id=users[3].id, status="Concluído",
                 prioridade="Alta", prazo=hoje - timedelta(days=10)),
            Task(titulo="Desenvolvimento do frontend", descricao="Implementar interface com HTML/CSS moderno seguindo o design system.",
                 projeto_id=projects[0].id, responsavel_id=users[2].id, status="Em Andamento",
                 prioridade="Alta", prazo=hoje + timedelta(days=20)),
            Task(titulo="Integração com API de notas", descricao="Conectar portal com API do sistema acadêmico.",
                 projeto_id=projects[0].id, responsavel_id=users[3].id, status="A Fazer",
                 prioridade="Média", prazo=hoje + timedelta(days=35)),
            Task(titulo="Testes de usabilidade", descricao="Realizar testes com grupo de usuários reais.",
                 projeto_id=projects[0].id, responsavel_id=users[1].id, status="A Fazer",
                 prioridade="Média", prazo=hoje + timedelta(days=50)),
            # Project 2 tasks
            Task(titulo="Roteiro do curso", descricao="Elaborar roteiro completo com objetivos de aprendizagem.",
                 projeto_id=projects[1].id, responsavel_id=users[1].id, status="Em Andamento",
                 prioridade="Alta", prazo=hoje + timedelta(days=15)),
            Task(titulo="Gravação das videoaulas - Módulo 1", descricao="Gravar e editar as videoaulas do primeiro módulo.",
                 projeto_id=projects[1].id, responsavel_id=users[2].id, status="A Fazer",
                 prioridade="Alta", prazo=hoje + timedelta(days=30)),
            Task(titulo="Criação de atividades avaliativas", descricao="Desenvolver quizzes e projetos práticos.",
                 projeto_id=projects[1].id, responsavel_id=users[3].id, status="A Fazer",
                 prioridade="Média", prazo=hoje + timedelta(days=45)),
            # Overdue tasks
            Task(titulo="Documentação técnica API", descricao="Documentar endpoints da API para equipe de desenvolvimento.",
                 projeto_id=projects[0].id, responsavel_id=users[2].id, status="A Fazer",
                 prioridade="Baixa", prazo=hoje - timedelta(days=3)),
            Task(titulo="Relatório de progresso Q1", descricao="Preparar relatório de progresso para diretoria.",
                 projeto_id=projects[1].id, responsavel_id=users[1].id, status="A Fazer",
                 prioridade="Crítica", prazo=hoje - timedelta(days=1)),
        ]
        db.add_all(tasks)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

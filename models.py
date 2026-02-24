from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    admin = "admin"
    gestor = "gestor"
    colaborador = "colaborador"


class ProjectStatus(str, enum.Enum):
    planejamento = "Planejamento"
    ativo = "Ativo"
    pausado = "Pausado"
    concluido = "Concluído"
    cancelado = "Cancelado"


class TaskStatus(str, enum.Enum):
    a_fazer = "A Fazer"
    em_andamento = "Em Andamento"
    concluido = "Concluído"


class TaskPriority(str, enum.Enum):
    baixa = "Baixa"
    media = "Média"
    alta = "Alta"
    critica = "Crítica"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="colaborador")
    avatar_color = Column(String(7), default="#6366f1")
    criado_em = Column(DateTime, default=datetime.utcnow)

    projetos = relationship("Project", back_populates="responsavel_user", foreign_keys="Project.responsavel_id")
    tarefas = relationship("Task", back_populates="responsavel_user", foreign_keys="Task.responsavel_id")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    descricao = Column(Text)
    responsavel_id = Column(Integer, ForeignKey("users.id"))
    data_inicio = Column(DateTime)
    data_fim = Column(DateTime)
    status = Column(String(30), default="Planejamento")
    progresso = Column(Float, default=0.0)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    responsavel_user = relationship("User", back_populates="projetos", foreign_keys=[responsavel_id])
    tarefas = relationship("Task", back_populates="projeto", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descricao = Column(Text)
    projeto_id = Column(Integer, ForeignKey("projects.id"))
    responsavel_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(30), default="A Fazer")
    prioridade = Column(String(20), default="Média")
    prazo = Column(DateTime)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projeto = relationship("Project", back_populates="tarefas")
    responsavel_user = relationship("User", back_populates="tarefas", foreign_keys=[responsavel_id])

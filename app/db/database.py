from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Engine para a APLICAÇÃO — usa conexão pooled + NullPool
# O Neon já gerencia o pool via PgBouncer, não precisamos de pool no SQLAlchemy
engine = create_engine(
    settings.db_url,
    poolclass=NullPool,  # desativa pool do SQLAlchemy (Neon cuida disso)
    connect_args={"sslmode": "require"},  # Neon exige SSL obrigatoriamente
)

# Session factory — each request opens and closes a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency que fornece uma sessão de banco por requisição.
    O 'finally' garante que a sessão sempre será fechada.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

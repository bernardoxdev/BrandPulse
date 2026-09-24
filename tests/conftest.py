import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.analytics import get_repository as get_analytics_repository
from app.api.routes.respostas import get_repository as get_respostas_repository
from app.database.tables import Base
from app.main import app
from app.repositories.respostas import RespostaRepository


@pytest.fixture
def test_engine():
    """
    Cria um banco SQLite em memória exclusivo para cada teste.
    """

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(test_engine):
    """
    Cria um TestClient usando o banco de testes.
    """

    def override_respostas_repository():
        with Session(test_engine) as session:
            yield RespostaRepository(session)

    def override_analytics_repository():
        with Session(test_engine) as session:
            yield RespostaRepository(session)

    app.dependency_overrides[get_respostas_repository] = override_respostas_repository

    app.dependency_overrides[get_analytics_repository] = override_analytics_repository

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def repository(test_engine):
    """
    Cria um RespostaRepository usando o banco de testes.
    """
    with Session(test_engine) as session:
        yield RespostaRepository(session)

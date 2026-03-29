from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.transformer import Transformer, TransformerCriticality


@pytest.fixture()
def client(tmp_path: Path):
    db_path = tmp_path / "test_auth.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        db = testing_session_local()
        db.add(
            Transformer(
                name="Test Transformer",
                criticality=TransformerCriticality.CRITICAL,
            )
        )
        db.commit()
        db.close()

        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def issue_csrf(client: TestClient) -> dict[str, str]:
    response = client.get("/api/v1/auth/csrf")
    assert response.status_code == 200
    token = response.json()["csrf_token"]
    return {"X-CSRF-Token": token}
"""Tests for API."""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker

from core import model
from core.api import core, make_db, schema
from core.repository.orm import metadata, start_mappers


def test_pydantic_schema():  # noqa: D103
    job = schema.Job(
        id=1, name="Test", description="Testing", _status=model.Status.PENDING
    )

    jobs = set()
    jobs.add(job)
    jobs.add(job)
    assert len(jobs) == 1


def test_production_make_db():
    """Test production FastAPI dependency `make_db`."""
    core.dependency_overrides[make_db] = make_db
    with TestClient(core) as client:
        response = client.get("/projects/")

        assert response.status_code == 200


def make_test_db():
    """Override dependency for FastAPI."""
    engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False},
    )
    metadata.create_all(engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    start_mappers()
    try:
        yield session()
    finally:
        clear_mappers()


# Override what database to use for tests
core.dependency_overrides[make_db] = make_test_db


def test_get_projects():
    """Test getting project list endpoint."""
    with TestClient(core) as client:
        response = client.get("/projects/")

        assert response.status_code == 200


def test_add_project():
    """Test posting a new project."""
    with TestClient(core) as client:
        response = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )
        assert response.status_code == 200
        project_data = response.json()
        assert "id" in project_data
        project_id = project_data["id"]

        response = response.json()
        assert response == {
            "id": project_id,
            "name": "Project name",
            "number": "AB-123",
            "description": "A project description",
        }


def test_add_and_get_job():
    """Test posting a new job to a project and getting list of jobs."""
    with TestClient(core) as client:
        response = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )
        assert response.status_code == 200
        project_data = response.json()
        assert "id" in project_data
        project_id = project_data["id"]

        response_job = client.post(
            f"/projects/{project_id}/jobs/",
            json={"name": "Job name", "description": "Job description"},
        )

        assert response_job.status_code == 200

        job_data = response_job.json()
        assert "id" in job_data
        job_id = job_data["id"]
        response_job_json = response_job.json()
        assert response_job_json == {
            "name": "Job name",
            "description": "Job description",
            "id": job_id,
            "_status": "Pending",
        }

        response = client.get(f"/projects/{project_id}/jobs")
        assert response.status_code == 200
        jobs = response.json()
        assert len(jobs) == 1
        assert jobs == [
            {
                "name": "Job name",
                "description": "Job description",
                "id": job_id,
                "_status": "Pending",
            }
        ]


def test_project_not_existing():
    """Test posting a new job to a project and getting list of jobs."""
    with TestClient(core) as client:

        response = client.get(f"/projects/0/jobs")
        assert response.status_code == 404

        response = client.get(f"/projects/abc/jobs")
        assert response.status_code == 422

        response = client.post(
            "/projects/-1/jobs/",
            json={"name": "Job name", "description": "Job description"},
        )
        assert response.status_code == 404
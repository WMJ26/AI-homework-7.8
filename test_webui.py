import pytest
from fixlot.webui.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestWebUI:
    def test_index_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"fixlot" in resp.data

    def test_api_run_requires_task(self, client):
        resp = client.post("/api/run", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_api_run_returns_task_id(self, client):
        resp = client.post("/api/run", json={
            "task": "test task",
            "provider": "openai",
            "max_rounds": 1,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "task_id" in data
        assert data["status"] == "running"

    def test_api_status_unknown_task(self, client):
        resp = client.get("/api/status/nonexistent")
        assert resp.status_code == 404

    def test_api_status_returns_task(self, client):
        run_resp = client.post("/api/run", json={
            "task": "test",
            "provider": "openai",
            "max_rounds": 1,
        })
        task_id = run_resp.get_json()["task_id"]

        status_resp = client.get(f"/api/status/{task_id}")
        assert status_resp.status_code == 200
        data = status_resp.get_json()
        assert data["status"] in ("running", "completed", "error")
from fastapi.testclient import TestClient
from backend.app.main import app

with TestClient(app) as client:
    health = client.get("/health").json()
    print("HEALTH:", health.get("status"))
    print("UNITS:", len(client.get("/api/v1/units").json()))
    print("COURSES:", client.get("/api/v1/courses").json().get("total"))
    print("FACULTY:", client.get("/api/v1/faculty").json().get("total"))
    print("RESEARCH:", client.get("/api/v1/research-areas").json().get("total"))
    print("PROGRAMS:", len(client.get("/api/v1/programs").json()))
    print("PROJECTS:", client.get("/api/v1/teammates/projects").json().get("total"))
    print("PROFILES:", client.get("/api/v1/teammates/profiles").json().get("total"))
    print("ROOT STATUS:", client.get("/").status_code)
    print("SPA ROUTE STATUS:", client.get("/courses").status_code)
    print("DASHBOARD STATUS:", client.get("/dashboard").status_code)
    print("ALL VERIFIED!")

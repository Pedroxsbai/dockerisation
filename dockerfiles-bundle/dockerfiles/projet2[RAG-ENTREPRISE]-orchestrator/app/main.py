"""
Hello-world FastAPI app for projet2-orchestrator.
Sera étendu pour gérer le routing multi-source (Jira, ServiceNow, SharePoint, SQL).
"""
from fastapi import FastAPI

app = FastAPI(title="Projet 2 — Orchestrator", version="0.0.1")


@app.get("/health")
async def health():
    """Endpoint utilisé par ECS et le HEALTHCHECK Docker."""
    return {"status": "ok", "service": "orchestrator"}


@app.get("/")
async def root():
    return {"message": "Orchestrator is running"}

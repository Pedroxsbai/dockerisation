"""
Hello-world FastAPI app for projet1-ai-service.
Remplacer le contenu de ce fichier par le vrai code quand il sera prêt.
"""
from fastapi import FastAPI

app = FastAPI(title="Projet 1 — AI Service", version="0.0.1")


@app.get("/health")
async def health():
    """Endpoint utilisé par ECS et le HEALTHCHECK Docker."""
    return {"status": "ok", "service": "ai-service"}


@app.get("/")
async def root():
    return {"message": "AI Service is running"}

from fastapi import FastAPI

from backend.api.middleware.cors import setup_cors
from backend.api.routes import health

app = FastAPI(
    title="IAC-032 Unified Scraper",
    version="0.1.0",
    description="Multi-platform content intelligence engine",
)

setup_cors(app)
app.include_router(health.router)


@app.get("/")
async def root():
    return {"message": "IAC-032 Unified Scraper API", "docs": "/docs"}

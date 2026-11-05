"""Application entry point: creates the app and registers the router only."""
from fastapi import FastAPI

from app.core.config import settings
from app.routers import auth_routes

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Independent Authentication microservice (registration, login, JWT).",
)
app.include_router(auth_routes.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"service": settings.APP_NAME, "status": "running", "version": settings.APP_VERSION}

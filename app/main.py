from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import urls, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup: Initialize relational database schema
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown logic if required


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "⚡ High-performance, production-ready URL shortener service "
        "providing collision-free short hashing, custom aliases, click telemetry, "
        "and real-time referrer analytics."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root_endpoint():
    """Service landing endpoint with API metadata and documentation links."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe endpoint for container orchestration and uptime monitors."""
    return {"status": "healthy"}


# Mount application routers - analytics and specific routes first, wildcard /{short_code} last
app.include_router(analytics.router)
app.include_router(urls.router)

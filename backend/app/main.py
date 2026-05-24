# launchkit/backend/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth as auth_router
from app.routers import oauth as oauth_router
from app.routers import user as user_router
from app.routers import org as org_router
from app.routers import billing as billing_router
from app.routers import usage as usage_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.jobs.scheduler import start_scheduler
    start_scheduler()
    yield
    # Shutdown
    from app.jobs.scheduler import stop_scheduler
    stop_scheduler()


app = FastAPI(
    title="LaunchKit API",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(oauth_router.router)
app.include_router(user_router.router)
app.include_router(org_router.router)
app.include_router(billing_router.router)
app.include_router(usage_router.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "environment": settings.ENVIRONMENT}
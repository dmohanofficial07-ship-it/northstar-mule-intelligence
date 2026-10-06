from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import SessionLocal, init_db
from .routers import auth, cases, dashboard, events, investigations, transactions
from .seed_data import seed_database, seed_graph
from .services.integrations import integrations

ROOT = Path(__file__).resolve().parents[2]


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        seed_database(db)
    integrations.connect()
    seed_graph(integrations.neo4j)
    yield
    integrations.close()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Explainable transaction screening and mule-account investigation API.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(investigations.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(events.router, prefix="/api")


@app.get("/api/health", tags=["operations"])
def health() -> dict:
    return {"status": "operational", "service": "northstar-api", "version": "1.0.0", "dependencies": integrations.statuses()}


@app.get("/", include_in_schema=False)
def frontend() -> FileResponse:
    return FileResponse(ROOT / "index.html")


@app.get("/styles.css", include_in_schema=False)
def stylesheet() -> FileResponse:
    return FileResponse(ROOT / "styles.css", media_type="text/css")


@app.get("/script.js", include_in_schema=False)
def javascript() -> FileResponse:
    return FileResponse(ROOT / "script.js", media_type="application/javascript")


if (ROOT / "assets").exists():
    app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")

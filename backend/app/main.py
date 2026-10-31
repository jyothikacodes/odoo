import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.db import engine, Base, SessionLocal
from app.core.errors import AppError
from app.services.seed_data import seed_database
from app.routers import auth, catalog, subscriptions, invoices, payments, reports, simulation, portal

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Seed database
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="Brightloop Subscription Management Platform",
    description="Unified platform for recurring revenue, plans, subscriptions, automated billing, and revenue analytics",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# App error handler
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

# Include API routers
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(subscriptions.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(reports.router)
app.include_router(simulation.router)
app.include_router(portal.router)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))

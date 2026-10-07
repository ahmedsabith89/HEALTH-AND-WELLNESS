import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.seed_data import seed_database
from app.routes.auth_routes import router as auth_router
from app.routes.student_routes import router as student_router
from app.routes.presentation_routes import router as presentation_router
from app.routes.admin_routes import router as admin_router
from app.routes.tester_routes import router as tester_router

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB and ensure seed data exists
    init_db()
    seed_database(force_reseed=False)
    yield

app = FastAPI(
    title="HEALTH AND WELLNESS - PRESENTATION",
    description="Private college-class presentation management system for exactly 69 students organized into 10 wellness presentation teams.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router)
app.include_router(student_router)
app.include_router(presentation_router)
app.include_router(admin_router)
app.include_router(tester_router)

# Mount static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h1>Class Presentation Hub</h1><p>Starting up...</p>")

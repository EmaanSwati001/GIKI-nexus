"""
GIKI Nexus — FastAPI Backend Application Entrypoint.
Initializes the academic knowledge repository, in-memory graph service,
CORS middleware, and REST API routes for academic & research discovery.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.database.academic_repository import AcademicRepository
from backend.app.graph.service import AcademicGraphService
from backend.app.services.academic_service import AcademicService
from backend.app.api.routes.academic import router as academic_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("giki_nexus")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager:
    Loads processed academic datasets and builds the knowledge graph at startup.
    """
    logger.info("Starting GIKI Nexus Academic Backend...")

    # 1. Initialize Academic Repository
    repo = AcademicRepository(data_dir=settings.PROCESSED_DATA_DIR)
    repo.load_datasets()
    app.state.repository = repo

    # 2. Build Academic Knowledge Graph
    graph_service = AcademicGraphService()
    graph_service.build_graph(repo)
    app.state.graph_service = graph_service

    # 3. Initialize Academic Service
    academic_service = AcademicService(repo=repo, graph_service=graph_service)
    app.state.academic_service = academic_service

    logger.info("GIKI Nexus Academic Backend initialization complete.")
    yield

    logger.info("Shutting down GIKI Nexus Academic Backend...")


app = FastAPI(
    title="GIKI Nexus Academic Discovery API",
    description=(
        "Institutional academic and research discovery platform for Ghulam Ishaq Khan Institute (GIKI). "
        "Provides course exploration, prerequisite tracking, faculty profiles, research areas, "
        "and knowledge graph discovery."
    ),
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers for uniform JSON error responses
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing request {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please check logs for details."},
    )


# Register API Routers
app.include_router(academic_router, prefix=settings.API_V1_PREFIX)


# System Health Check Endpoint
@app.get("/health", tags=["System"], summary="System health and dataset status")
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Return operational health status, loaded entity counts, and knowledge graph size.
    """
    repo: AcademicRepository = getattr(request.app.state, "repository", None)
    graph_service: AcademicGraphService = getattr(request.app.state, "graph_service", None)

    is_repo_ready = repo is not None and repo.is_loaded
    is_graph_ready = graph_service is not None and graph_service._is_built

    stats = graph_service.get_graph_stats() if is_graph_ready else {}

    return {
        "status": "healthy" if (is_repo_ready and is_graph_ready) else "degraded",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "datasets_loaded": is_repo_ready,
        "graph_initialized": is_graph_ready,
        "entity_counts": {
            "units": len(repo.units) if is_repo_ready else 0,
            "faculty": len(repo.faculty) if is_repo_ready else 0,
            "courses": len(repo.courses) if is_repo_ready else 0,
            "publications": len(repo.publications) if is_repo_ready else 0,
            "research_areas": len(repo.research_areas) if is_repo_ready else 0,
            "programs": len(repo.programs) if is_repo_ready else 0,
        },
        "graph": stats,
    }

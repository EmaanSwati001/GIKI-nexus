"""
Core configuration settings for GIKI Nexus backend application.
Lightweight configuration supporting local file-based datasets and in-memory graph.
"""

import os
from pathlib import Path
from typing import List

# Determine project root dynamically from this file location:
# backend/app/core/config.py -> backend/app/core -> backend/app -> backend -> project_root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings:
    PROJECT_NAME: str = "GIKI Nexus"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Path configuration
    BASE_DIR: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    PROCESSED_DATA_DIR: Path = PROJECT_ROOT / "data" / "processed"
    RAW_DATA_DIR: Path = PROJECT_ROOT / "data" / "raw"
    SAMPLE_DATA_DIR: Path = PROJECT_ROOT / "data" / "sample"
    
    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Graph Engine Selection (defaults to networkx for zero-dep local execution)
    GRAPH_BACKEND: str = os.getenv("GRAPH_BACKEND", "networkx")


settings = Settings()

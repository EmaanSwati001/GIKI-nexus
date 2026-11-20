"""
API routes package for GIKI Nexus.
"""

from .academic import router as academic_router
from .teammates import router as teammates_router

__all__ = ["academic_router", "teammates_router"]

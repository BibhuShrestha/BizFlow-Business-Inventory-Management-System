"""
Unified namespace package for Vercel serverless functions and backend API modules.
Extends package __path__ to seamlessly include backend/api (routers, schemas, deps, main).
"""
import sys
from pathlib import Path

_backend_api = Path(__file__).resolve().parent.parent / "backend" / "api"
if _backend_api.exists() and str(_backend_api) not in __path__:
    __path__.append(str(_backend_api))

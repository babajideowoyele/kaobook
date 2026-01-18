"""
RoleBox Database Module

Unified SQLite-based annotation storage for all RoleBox workflows.
"""

from .db import RoleBoxDB, get_db

__all__ = ["RoleBoxDB", "get_db"]

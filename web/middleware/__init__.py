"""
Middleware module initialization.
"""
from .cors import init_cors, add_cors_headers
from .error_handlers import init_error_handlers

__all__ = [
    'init_cors',
    'add_cors_headers',
    'init_error_handlers',
]

"""
CORS Middleware
Handles Cross-Origin Resource Sharing (CORS) headers.
"""
from flask import Flask
from ..config import Config


def add_cors_headers(response):
    """
    Add CORS headers to response.
    
    Args:
        response: Flask response object
        
    Returns:
        Modified response with CORS headers
    """
    response.headers.add("Access-Control-Allow-Origin", Config.CORS_ORIGINS)
    response.headers.add("Access-Control-Allow-Headers", Config.CORS_HEADERS)
    response.headers.add("Access-Control-Allow-Methods", Config.CORS_METHODS)
    return response


def init_cors(app: Flask):
    """
    Initialize CORS middleware for Flask app.
    
    Args:
        app: Flask application instance
    """
    app.after_request(add_cors_headers)

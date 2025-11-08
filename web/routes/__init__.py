"""
API module initialization.
Registers all API blueprints.
"""
from flask import Flask
from .chat import chat_bp
from .equity import equity_bp
from .crypto import crypto_bp
from .data import data_bp
from .health import health_bp


def register_blueprints(app: Flask):
    """
    Register all API blueprints with the Flask app.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(chat_bp)
    app.register_blueprint(equity_bp)
    app.register_blueprint(crypto_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(health_bp)


__all__ = [
    'register_blueprints',
    'chat_bp',
    'equity_bp',
    'crypto_bp',
    'data_bp',
    'health_bp',
]

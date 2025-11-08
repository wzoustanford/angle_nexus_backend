"""
Error Handlers Middleware
Centralized error handling for the Flask application.
"""
from flask import Flask, jsonify
from pydantic import ValidationError
from ..logging_config import logger


def handle_validation_error(error):
    """Handle Pydantic validation errors"""
    logger.warning("Validation error: %s", error)
    return jsonify({"error": f"Invalid input: {str(error)}"}), 400


def handle_generic_error(error):
    """Handle generic exceptions"""
    logger.exception("An unexpected error occurred: %s", error)
    return jsonify({"error": f"An error occurred: {str(error)}"}), 500


def handle_404_error(error):
    """Handle 404 errors"""
    logger.warning("404 error: %s", error)
    return jsonify({"error": "Resource not found"}), 404


def handle_500_error(error):
    """Handle 500 errors"""
    logger.error("500 error: %s", error, exc_info=True)
    return jsonify({"error": "Internal server error"}), 500


def init_error_handlers(app: Flask):
    """
    Initialize error handlers for Flask app.
    
    Args:
        app: Flask application instance
    """
    app.errorhandler(ValidationError)(handle_validation_error)
    app.errorhandler(404)(handle_404_error)
    app.errorhandler(500)(handle_500_error)
    app.errorhandler(Exception)(handle_generic_error)

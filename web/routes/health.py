"""
Health API Blueprint
Handles health check and status endpoints.
"""
from flask import Blueprint, jsonify
from ..config import Config

health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response indicating service health
    """
    return jsonify({
        "status": "healthy",
        "service": "AngleNexus API",
        "version": Config.API_VERSION
    }), 200


@health_bp.route('/status', methods=['GET'])
def status_check():
    """
    Detailed status endpoint.
    
    Returns:
        JSON response with service status details
    """
    return jsonify({
        "status": "operational",
        "service": "AngleNexus API",
        "version": Config.API_VERSION,
        "models": Config.ALLOWED_MODELS,
        "default_model": Config.DEFAULT_MODEL
    }), 200

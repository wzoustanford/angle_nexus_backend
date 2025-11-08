"""
Equity API Blueprint
Handles equity search endpoints.
"""
from flask import Blueprint, request, jsonify
from ..logging_config import logger
from ..extensions import iSearch

equity_bp = Blueprint('equity', __name__, url_prefix='/api/equity')


@equity_bp.route('/search', methods=['GET', 'POST'])
def search_equity():
    """
    Search for equity stocks.
    
    Query Parameters:
        query (str): Search query string
        
    Returns:
        JSON response with search results
    """
    query = request.args.get('query', '')
    
    if not query:
        logger.warning("Empty query provided to /api/equity/search")
        return jsonify({"error": "Query parameter is required"}), 400
    
    logger.info("Equity Query: %s", query)
    search_res = iSearch.query(query)
    
    return jsonify(search_res), 200

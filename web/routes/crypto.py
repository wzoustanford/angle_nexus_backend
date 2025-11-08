"""
Crypto API Blueprint
Handles cryptocurrency search endpoints.
"""
from flask import Blueprint, request, jsonify
from ..logging_config import logger
from ..extensions import iCryptoSearch

crypto_bp = Blueprint('crypto', __name__, url_prefix='/api/crypto')


@crypto_bp.route('/search', methods=['GET', 'POST'])
def search_crypto():
    """
    Search for cryptocurrencies.
    
    Query Parameters:
        query (str): Search query string
        
    Returns:
        JSON response with search results
    """
    query = request.args.get('query', '')
    
    if not query:
        logger.warning("Empty query provided to /api/crypto/search")
        return jsonify({"error": "Query parameter is required"}), 400
    
    logger.info("Crypto Query: %s", query)
    search_res = iCryptoSearch.query(query)
    
    return jsonify(search_res), 200


@crypto_bp.route('/companies', methods=['GET'])
def get_companies():
    """
    Get cryptocurrency companies.
    Legacy endpoint for testing.
    """
    query = "bitcoin"
    logger.info("GET /api/crypto/companies invoked. Querying iCryptoSearch with '%s'", query)
    search_res = iCryptoSearch.query(query)
    return jsonify(search_res), 200

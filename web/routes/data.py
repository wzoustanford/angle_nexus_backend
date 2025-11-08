"""
Data API Blueprint
Handles data fetching endpoints for DynamoDB operations.
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from ..logging_config import logger
from ..services.dynamo_service import fetch_data_from_dynamo

data_bp = Blueprint('data', __name__, url_prefix='/api/data')


@data_bp.route('/fetch', methods=['POST'])
def fetch_dynamo_data():
    """
    Fetch data from DynamoDB for a specific date and set of symbols.
    
    Request Body (JSON):
        date (str): Date in ISO format (YYYY-MM-DD)
        symbols (list): List of stock ticker symbols
        
    Returns:
        JSON response with fetched data
    """
    data = request.get_json()
    if not data:
        logger.warning("No JSON data provided in /api/data/fetch request.")
        return jsonify({'error': 'No input data provided'}), 400

    date_str = data.get('date')
    symbols = data.get('symbols')

    if not date_str or not symbols:
        logger.warning("Missing 'date' or 'symbols' in /api/data/fetch request.")
        return jsonify({'error': 'Missing required parameters: date or symbols'}), 400

    # Validate date format
    try:
        datetime.fromisoformat(date_str)
    except ValueError:
        logger.warning("Invalid date format received in /api/data/fetch: '%s'", date_str)
        return jsonify({'error': 'Invalid date format, expected ISO format'}), 400

    logger.info("Fetching DynamoDB data for date='%s', symbols=%s", date_str, symbols)
    dynamo_response = fetch_data_from_dynamo(symbols, date_str)
    
    return jsonify({'data': dynamo_response}), 200

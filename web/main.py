import json
import copy
import decimal
from datetime import date, datetime, timedelta
from flask import Response, request, jsonify
from pydantic import ValidationError
from concurrent.futures import ThreadPoolExecutor, as_completed

from web import create_app, iSearch, iCryptoSearch, fetch_data_from_dynamo
from .logging_config import logger
from .config import Config
from .utils.util import *
from .prompts.prompts import *
from .clients.fmp_api import RateLimiter, get_finance_api_data
from .models.model import ChatRequest
from .clients.reasoning import ReasoningChatClient
from .routes.subscription_routes import subscription_bp
from .services.weaver_service import process_weaver_request
from .services.chat_service import process_chat_request


app = create_app()

# Register subscription routes
app.register_blueprint(subscription_bp)

model = "o3-mini"  # Options: "o3-mini", "deepseek-reasoner"
chat_client = ReasoningChatClient(model=model)
ALLOWED_MODELS = Config.ALLOWED_MODELS


# Legacy helper function (kept for backward compatibility)
def convert_decimals(obj):
    """
    Recursively converts Decimal objects in a data structure to int or float.
    Note: This is now also available in services.dynamo_service
    """
    return convert_decimals(obj)


def parse_json_from_text(text: str) -> dict:
    """
    Attempts to extract and parse a JSON object from a text string.
    Returns the dictionary if successful or None if parsing fails.
    Note: This is now also available in services.classification_service
    """
    try:
        if "{" in text and "}" in text:
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            json_text = text[json_start:json_end]
            return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error("JSON parsing failed: %s", e)
    return None


def weaver_chat(request_payload):
    """
    Process a financial chat request using Weaver agent.
    Legacy function - now delegates to the modular service layer.
    """
    user_input = request_payload.get('user_input') or request_payload.get('message')
    model_name = request_payload.get('model_name', Config.DEFAULT_MODEL)
    history = request_payload.get('history', [])
    
    result = process_weaver_request(
        user_input=user_input,
        history=history,
        model_name=model_name
    )
    return result


# Legacy helper function (kept for backward compatibility)
def fetch_data(key, api_url):
    """
    Helper for concurrency-based data fetch.
    Note: This is now also available in services.weaver_service
    """
    logger.debug("Fetching data for key='%s' from URL='%s'", key, api_url)
    rate_limiter = RateLimiter(calls_per_minute=280) 
    response = get_finance_api_data(api_url, rate_limiter)
    return key, response


@app.after_request
def add_cors_headers(response):
    """
    Legacy CORS handler (kept for backward compatibility).
    Note: CORS is now handled by middleware.cors
    """
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response


@app.route("/", methods=['POST'])
def test():
    """Legacy test endpoint"""
    return "<p>Test, Api is working.</p>"


@app.route('/companies', methods=['GET'])
def get_companies():
    """Legacy companies endpoint"""
    query = "bitcoin"
    logger.info("GET /companies invoked. Querying iCryptoSearch with '%s'", query)
    search_res = iCryptoSearch.query(query)
    return jsonify(search_res)


@app.route('/equity-api', methods=['GET', 'POST'])
def equity_api():
    """Legacy equity API endpoint - redirects to new service"""
    query = request.args.get('query', '')
    logger.info("Equity Query: %s", query)
    search_res = iSearch.query(query)
    return jsonify(search_res)


@app.route('/crypto-api', methods=['GET', 'POST'])
def crypto_api():
    """Legacy crypto API endpoint - redirects to new service"""
    query = request.args.get('query', '')
    logger.info("Crypto Query: %s", query)
    search_res = iCryptoSearch.query(query)
    return jsonify(search_res)



@app.route('/fetch_data', methods=['POST'])
def fetch_dynamo_data():
    """
    Legacy endpoint to fetch data from DynamoDB - now uses new service layer.
    Expects JSON payload with 'date' and 'symbols'.
    """
    data = request.get_json()
    if not data:
        logger.warning("No JSON data provided in /fetch_data request.")
        return jsonify({'error': 'No input data provided'}), 400

    date_str = data.get('date')
    symbols = data.get('symbols')

    if not date_str or not symbols:
        logger.warning("Missing 'date' or 'symbols' in /fetch_data request.")
        return jsonify({'error': 'Missing required parameters: date or symbols'}), 400

    # Validate date format
    try:
        datetime.fromisoformat(date_str)
    except ValueError:
        logger.warning("Invalid date format received in /fetch_data: '%s'", date_str)
        return jsonify({'error': 'Invalid date format, expected ISO format'}), 400

    logger.info("Fetching DynamoDB data for date='%s', symbols=%s", date_str, symbols)
    dynamo_response = fetch_data_from_dynamo(symbols, date_str)
    return jsonify({'data': dynamo_response}), 200


if __name__ == '__main__':
    app.run(host=Config.HOST, debug=Config.DEBUG, port=Config.PORT)

@app.route('/chat', methods=['POST'])
def chat():
    """
    Legacy chat endpoint - now uses the new modular service layer.
    Maintains backward compatibility with existing API contracts.
    """
    try:
        # Extract and validate JSON payload from request
        request_payload = request.get_json(force=True, silent=True)
        if not request_payload:
            logger.warning("No JSON payload provided in /chat request.")
            return jsonify({"error": "Invalid JSON request"}), 400

        user_message = request_payload.get('message')
        if not user_message:
            logger.warning("No 'message' found in /chat request payload.")
            return jsonify({"error": "No prompt provided"}), 400

        # Command trigger handling (e.g., a special keyword in the message)
        command_handlers = {
            "/weaver": lambda: weaver_chat(request_payload),
        }
        for command, handler in command_handlers.items():
            if command in user_message:
                logger.info("Command '%s' detected in user message. Routing to handler.", command)
                response = handler()
                return jsonify(response), 200

        # Use the new modular service layer for processing
        model_name = request_payload.get('model_name', Config.DEFAULT_MODEL)
        history = request_payload.get('history', [])
        
        result = process_chat_request(
            user_message=user_message,
            model_name=model_name,
            history=history
        )
        
        return jsonify(result), 200

    except Exception as exc:
        logger.exception("An error occurred in /chat endpoint.")
        return jsonify({"error": f"An error occurred: {str(exc)}"}), 500


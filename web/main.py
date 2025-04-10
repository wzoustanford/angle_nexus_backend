import json
import copy
import logging
import decimal
from datetime import date, datetime, timedelta
from flask import Response, request, jsonify
from pydantic import ValidationError

from web import create_app, iSearch, iCryptoSearch
from . import fetch_data_from_dynamo
from .utils.util import *
from .prompts.prompts import *
from .apis.fmp_api import get_finance_api_data
from .models.model import ChatRequest
from .apis.reasoning import ReasoningChatClient
from concurrent.futures import ThreadPoolExecutor, as_completed

app = create_app()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = "o3-mini"  # Options: "o3-mini" or "deepseek-reasoner"
chat_client = ReasoningChatClient(model=model)
ALLOWED_MODELS = ["o3-mini", "GPT-4o","deepseek-reasoner","o1","o1-mini"] # allowed models


def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, decimal.Decimal):
        # Convert to int if possible, otherwise float
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj

def parse_json_from_text(text: str) -> dict:
    """
    Attempts to extract and parse a JSON object from a text string.
    Returns the dictionary if successful or None if parsing fails.
    """
    try:
        if "{" in text and "}" in text:
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            json_text = text[json_start:json_end]
            return json.loads(json_text)
    except json.JSONDecodeError as e:
        logging.error("JSON parsing failed: %s", e)
    return None



def weaver_chat(request):
    """
        Process a financial chat request by validating input, fetching financial API data,
        and generating a final response using a reasoning chat client.
    """

    today_date = date.today()
    request.setdefault("user_input", request.get('message'))
    request.setdefault("model_name", "o3-mini")
    request.setdefault("history", [])

    try:
        chat_request = ChatRequest(**request)
    except ValidationError as e:
        return Response(f"Invalid input: {e}", status=400)
    
    if chat_request.model_name not in ALLOWED_MODELS:
        return Response(f"Model '{chat_request.model_name}' is not allowed.", status=400)

    chat_client = ReasoningChatClient(model=chat_request.model_name)
    sys_prompt = q_analysis_sys_prompt()
    fin_apis_details = finapis_details()

    user_query = (
        f"Here is Financial apis details:\n {fin_apis_details}, and here is the user input: "
        f"{chat_request.user_input}.\n Today Date is: {today_date}"
    )

    messages = format_conversation(chat_request.history, user_query, sys_prompt, window_size=6)
    k_topics_str = chat_client.create_chat_completion(messages)
    k_topics_json = json.loads(k_topics_str)

    finance_api_responses = {}
    if k_topics_json:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(fetch_data, key, api_json['api']): key
                for key, api_json in k_topics_json.items()
            }
            for future in as_completed(futures):
                key, response = future.result()
                if response:
                    finance_api_responses[key] = response
        if finance_api_responses:
            user_input = (
                f"Here is Financial apis responses:\n {json.dumps(finance_api_responses)}, "
                f"and here is the user input: {chat_request.user_input}.\n Today Date is: {today_date}"
            )
            messages2 = format_conversation(chat_request.history, user_input, combine_results_sys_promt(), window_size=6)
        else:
            messages2 = format_conversation(chat_request.history, f"Here is the user input: {chat_request.user_input}.\n", combine_results_sys_promt(), window_size=6)
    else:
        messages2 = format_conversation(chat_request.history, f"Here is the user input: {chat_request.user_input}.\n", combine_results_sys_promt(), window_size=6)

    results = chat_client.create_chat_completion(messages2)
    return {"message": results}


def fetch_data(key, api_url):
    response = get_finance_api_data(api_url)
    return key, response

@app.after_request
def add_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response

@app.route("/", methods=['POST'])
def test():
    return "<p>Test, Api is working.</p>"

@app.route('/companies', methods=['GET'])
def get_companies():
    query = "bitcoin"
    search_res = iCryptoSearch.query(query)
    return jsonify(search_res)

@app.route('/equity-api', methods=['GET', 'POST'])
def equity_api():
    query = request.args.get('query', '')
    logger.info(f'Equity Query: {query}')
    search_res = iSearch.query(query)
    return jsonify(search_res)

@app.route('/crypto-api', methods=['GET', 'POST'])
def crypto_api():
    query = request.args.get('query', '')
    logger.info(f'Crypto Query: {query}')
    search_res = iCryptoSearch.query(query)
    return jsonify(search_res)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Extract and validate JSON payload from request
        request_payload = request.get_json(force=True, silent=True)
        if not request_payload:
            return jsonify({"error": "Invalid JSON request"}), 400

        user_message = request_payload.get('message')
        if not user_message:
            return jsonify({"error": "No prompt provided"}), 400

        # Command trigger handling (e.g., a special keyword in the message)
        command_handlers = {
            "/weaver": lambda: weaver_chat(request_payload),
        }
        for command, handler in command_handlers.items():
            if command in user_message:
                logging.info("Command '%s' detected in user message. Routing to its handler.", command)
                return handler()

        current_date = date.today()

        # --- 1. Classification Phase ---
        classification_system_prompt = classify_sys_prompt()  # Returns a system prompt string
        classification_request = [
            {"role": "system", "content": classification_system_prompt},
            {"role": "user", "content": f"User input: {user_message}\nToday: {current_date}"}
        ]
        logging.info("Processing classification chat completion with model: %s", model)
        classification_response_str = chat_client.create_chat_completion(classification_request)
        logging.info("Classification response received: %s", classification_response_str)

        classification_json = parse_json_from_text(classification_response_str)
        if classification_json:
            extracted_symbols = list(classification_json.get('symbols', []))
            user_intent = classification_json.get('message', '')
        else:
            extracted_symbols = []
            user_intent = ""

        logging.info("User Intent: %s", user_intent)
        if not user_intent:
            return jsonify({
                "message": "Unable to process your request",
                "data": []
            }), 200

        # --- 2. DynamoDB Data Fetch ---
        dynamo_data = fetch_data_from_dynamo(extracted_symbols, current_date.isoformat())
        widget_data = convert_decimals(dynamo_data)
        full_widget_data = copy.deepcopy(widget_data)

        keys_to_remove = ['chart', 'ttl_timestamp']
        for item in widget_data:
            for key in keys_to_remove:
                item.pop(key, None)

        # --- 3. Final Widget Phase ---
        final_prompt_message = (
            f"Based on the user intention {user_intent}\n"
            f"and the DynamoDB Data: {json.dumps(widget_data)}"
        )

        widget_request = [
            {"role": "system", "content": widget_sys_prompt()},
            {"role": "user", "content": final_prompt_message}
        ]
        final_response_str = chat_client.create_chat_completion(widget_request)

        final_json = parse_json_from_text(final_response_str)
        final_message = final_json.get('message') if final_json and 'message' in final_json else final_response_str

        return jsonify({
            "message": final_message,
            "data": full_widget_data
        }), 200

    except Exception as exc:
        logging.exception("An error occurred in /chat endpoint.")
        return jsonify({"error": f"An error occurred: {str(exc)}"}), 500

@app.route('/fetch_data', methods=['POST'])
def fetch_dynamo_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    date_str = data.get('date')
    symbols = data.get('symbols')

    if not date_str or not symbols:
        return jsonify({'error': 'Missing required parameters: date or symbols'}), 400

    try:
        # Validate the date format; expecting ISO format.
        datetime.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format, expected ISO format'}), 400

    dynamo_response = fetch_data_from_dynamo(symbols, date_str)
    return jsonify({'data': dynamo_response}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)

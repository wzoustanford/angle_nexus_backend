import json
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
ALLOWED_MODELS = ["o3-mini", "GPT-4o","deepseek-reasoner","o1","o1-mini"]# allowed models


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
        # Extract user input
        request_data = request.get_json()
        user_input = request_data.get('message') if request_data else None
        if not user_input:
            return Response("No prompt provided", status=400)
        
        # Check for command triggers
        command_handlers = {
            "/weaver": lambda: weaver_chat(request_data),
        }
        for command, handler in command_handlers.items():
            if command in user_input:
                print(f"Command '{command}' detected in user input. Routing to its handler.")
                return handler()

        today_date = date.today()

        # 1. Classification Phase
        # Build classification prompt by passing user_input into classify_sys_prompt.
        classification_prompt = classify_sys_prompt()
        classification_messages = [
            {"role": "system", "content": classification_prompt},
            {"role": "user", "content": f"User input: {user_input}\nToday: {today_date}"}
        ]
        print(f"Processing classification chat completion with {model}...")
        classification_response_text = chat_client.create_chat_completion(classification_messages)

        print(f"Classification response: {classification_response_text}")

        # Extract symbols from the classification response
        symbols = []
        user_intent = ""
        try:
            if "{" in classification_response_text and "}" in classification_response_text:
                json_start = classification_response_text.find('{')
                json_end = classification_response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    classification_response = json.loads(classification_response_text[json_start:json_end])
                    symbols = list(classification_response.get('symbols', []))
                    user_intent = classification_response.get('message', '')
        except json.JSONDecodeError as json_err:
            print(f"Classification JSON extraction failed: {json_err}")

        print('User Intent:', user_intent)

        if not user_intent: #symbols:
            return {
                "message": "Unable to process your request",
                "data": []
            }

        # 2. DynamoDB Data Fetch
        # Call DynamoDB to fetch company details using the returned symbols.
        dynamo_response = fetch_data_from_dynamo(symbols, today_date.isoformat())

        keys_to_remove = ['chart', 'ttl_timestamp']

        # Convert Decimal objects in the DynamoDB data
        # converted_data = convert_decimals(valid_dynamo_response)
        
        converted_data = convert_decimals(dynamo_response)
        full_converted_data = convert_decimals(dynamo_response)
        # Iterate over each object in the list and remove keys in the list
        for item in converted_data:
            for key in keys_to_remove:
                item.pop(key, None)  

        # If the item is a dictionary, remove the 'key' key if it exists
        # Final widget phase (example from previous refactored code)
        final_user_message = f"""Based on the user intention {user_intent} \n and the DynamoDB Data: {json.dumps(converted_data)}"""
        # Specify the file name where you want to save the text
        file_name = "output.txt"

        # Open the file in write mode and save the message
        with open(file_name, "w") as file:
            file.write(final_user_message)

        final_messages = [
            {"role": "system", "content": widget_sys_prompt()},
            {"role": "user", "content": final_user_message}
        ]
        final_response_text = chat_client.create_chat_completion(final_messages)

        # Extract final message and return the response
        try:
            if "{" in final_response_text and "}" in final_response_text:
                json_start = final_response_text.find('{')
                json_end = final_response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    final_response = json.loads(final_response_text[json_start:json_end])
                    final_message = final_response.get('message', final_response_text)
            else:
                final_message = final_response_text
        except json.JSONDecodeError as json_err:
            final_message = final_response_text

        return {
            "message": final_message,
            "data": full_converted_data
        }

    except Exception as e:
        return Response(f"An error occurred: {str(e)}", status=500)


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

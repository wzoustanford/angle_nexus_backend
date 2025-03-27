import json
import logging
from datetime import date
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

@app.route('/weaver', methods=['POST'])
def weaver_chat():
    try:
        chat_request = ChatRequest(**request.get_json())
    except ValidationError as e:
        return Response(f"Invalid input: {e}", status=400)
    
    if chat_request.model_name not in ALLOWED_MODELS:
        return Response(f"Model '{chat_request.model_name}' is not allowed.", status=400)

    # chat_client = OpenAIChatClient(model=chat_request.model_name)
    chat_client = ReasoningChatClient(model=chat_request.model_name)
    sys_prompt = q_analysis_sys_prompt()
    fin_apis_details = finapis_details()
    today_date = date.today()

    user_query=f"Here is Financial apis details:\n {fin_apis_details}, and here is ther user input: {chat_request.user_input}.\n Today Date is: {today_date}"

    messages = format_conversation(chat_request.history, user_query, sys_prompt, window_size=6)

    #generate json response k topis with right finance APIs 
    k_topics_str = chat_client.create_chat_completion(messages)
    k_topics_json=json.loads(k_topics_str)
    print("k_topics_json: ",k_topics_json)

    finance_api_responses={}
    if k_topics_json:
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all API calls to the executor.
            futures = {executor.submit(fetch_data, key, api_json['api']): key 
                    for key, api_json in k_topics_json.items()}
            
            # As each future completes, get the result and update the response dictionary.
            for future in as_completed(futures):
                key, response = future.result()
                if response:
                    finance_api_responses[key] = response
        if finance_api_responses:
            user_input=f"Here is Financial apis reponses:\n {json.dumps(finance_api_responses)}, and here is ther user input: {chat_request.user_input}.\n Today Date is: {today_date}"
            messages2=format_conversation(chat_request.history, user_input, combine_results_sys_promt(), window_size=6)
        else:
            messages2=format_conversation(chat_request.history, f"here is ther user input: {chat_request.user_input}.\n", combine_results_sys_promt(), window_size=6)
    else:
        messages2=format_conversation(chat_request.history, f"here is ther user input: {chat_request.user_input}.\n", combine_results_sys_promt(), window_size=6)
    return Response(chat_client.create_chat_stream(messages2),mimetype='text/plain')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        request_data = request.get_json()
        user_input = request_data.get('message') if request_data else None

        if not user_input:
            return Response("No prompt provided", status=400)

        today_date = date.today()

        initial_messages = [
            {"role": "system", "content": widget_sys_prompt()},
            {"role": "user", "content": f"User input: {user_input}\nToday: {today_date}"},
        ]

        print(f"Processing chat completion with {model}...")
        response_text = chat_client.create_chat_completion(initial_messages)
        print("Raw response:", response_text)  

        # Clean the response text
        response_text_clean = response_text.strip().replace('```json', '').replace('```', '')
        reasoning_response = json.loads(response_text_clean)

        print("SYMBOLS:", list(reasoning_response['symbols']))
        dynamo_response = fetch_data_from_dynamo(list(reasoning_response['symbols']), today_date.isoformat())
        print("DynamoDB response:", len(dynamo_response))

        return {
            "message": reasoning_response['message'],
            "data": dynamo_response
        }
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        return Response(f"Invalid JSON response from API: {response_text}", status=500)
    except Exception as e:
        print(f"Error: {str(e)}")
        return Response(f"An error occurred: {str(e)}", status=500)

    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)

import json
import logging
from datetime import date
from flask import Response, request, jsonify
from . import fetch_data_from_dynamo
from .apis.reasoning import ReasoningChatClient
from .prompts.prompts import widget_sys_prompt
from web import create_app, iSearch, iCryptoSearch

app = create_app()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = "o3-mini"  # Options: "o3-mini" or "deepseek-reasoner"
chat_client = ReasoningChatClient(model=model)

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

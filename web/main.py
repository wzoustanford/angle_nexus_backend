import os
import sys
import json
import requests
import logging
from web import create_app, iSearch, iCryptoSearch
from flask import Response, request, jsonify
from datetime import datetime, timedelta
# from sseclient import SSEClient
from . import stop, query_dynamo, chat_query_processor, find_company_by_name
from .keywords import keywords

from fuzzywuzzy import process  # For fuzzy string matching
# Add the parent directory (project root) to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

# Constants
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

app = create_app()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/companies', methods=['GET'])
def get_companies():
    query = "bitcoin"
    search_res = iCryptoSearch.query(query)
    return jsonify(search_res)

@app.route('/equity-api', methods=['GET', 'POST'])
def equity_api():
    query = request.args.get('query', '')
    print('Equity_Query:', query)
    search_res = iSearch.query(query)
    return jsonify(search_res)

@app.route('/crypto-api', methods=['GET', 'POST'])
def crypto_api():
    query = request.args.get('query', '')
    print('Crypto_Query:', query)
    search_res = iCryptoSearch.query(query)
    return jsonify(search_res)

"""
@app.route('/stream/v2')
def streamv2():
    print('Stream2')
    question = request.args.get('question')
    print('Question:', question)
    print('OPEN_API_KEY:', os.getenv('OPEN_API_KEY'))
    
    yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')

    def performRequestWithStreaming():
        if question:
            filtered_words = [
                word.lower() for word in question.split()
                if word.lower() not in stop
            ]
            symbols = [find_company_by_name(word, keywords) for word in filtered_words]
            options = [
                query_dynamo(yesterday, symbol)
                for symbol in symbols if symbol is not None
            ]
            prompts = [
                chat_query_processor(option, question)
                for option in options
            ]

            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                 "Authorization": f"Bearer {os.getenv('OPEN_API_KEY')}",
            }

            content = ' '.join(prompts)

            print('Content:', content)
            data = {
                "model": "gpt-4o", # gpt-4
                "max_tokens": 700,
                "temperature": 0.7,
                "messages": [{"role": "user", "content": content}],
            }
            response = requests.post(url, headers=headers, json=data)
            yield response.json()['choices'][0]['message']['content']

    return Response(performRequestWithStreaming(), mimetype='text/event-stream')

"""

# def filter_and_find_symbols(question, stop_words, keywords):
#     """Filter out stop words and find symbols for the remaining words."""
#     filtered_words = [word.lower() for word in question.split() if word.lower() not in stop_words]
#     symbols = [find_company_by_name(word, keywords) for word in filtered_words]
#     return [symbol for symbol in symbols if symbol is not None]



# def filter_and_find_symbols(question, keywords):
#     """
#     Identify company names in the question contextually and return their symbols.
    
#     Args:
#         question (str): The user's question.
#         keywords (dict): A dictionary mapping company names to their symbols.
    
#     Returns:
#         list: A list of symbols for the identified companies.
#     """
#     print('filter_and_find_symbols', len(keywords))
#     # Convert the question to lowercase for case-insensitive matching
#     question_lower = question.lower()
    
#     # Extract company names from the keywords dictionary
#     company_names = list(keywords.keys())
    
#     # Use fuzzy matching to find the best match for each company name in the question
#     matched_symbols = []
#     for company_name in company_names:
#         # Use fuzzy matching to find the best match
#         match_score = process.extractOne(company_name.lower(), [question_lower])
        
#         # If the match score is above a threshold (e.g., 80), consider it a match
#         if match_score[1] > 90:
#             matched_symbols.append(keywords[company_name])
    
#     print('matched_symbols:', matched_symbols)
#     return matched_symbols[:4]

def filter_and_find_symbols(question, keywords):
    # Convert question to lowercase for case-insensitive matching
    lower_question = question.lower()
    
    # First, try exact company name matching
    for company, symbol in keywords.items():
        if company.lower() in lower_question:
            return symbol
    
    # If no exact match, try partial matching with additional heuristics
    matched_symbols = []
    for company, symbol in keywords.items():
        # Split company name into words and check for partial matches
        company_words = company.lower().split()
        question_words = lower_question.split()
        
        # Check if any company word is in the question
        if any(word in question_words for word in company_words):
            matched_symbols.append(symbol)
    
    # Return first match or None if no matches
    return matched_symbols[0] if matched_symbols else None

def fetch_data_from_dynamo(symbols, date):
    """Fetch data from DynamoDB for the given symbols and date."""
    return [query_dynamo(date, symbol) for symbol in symbols]

def generate_prompts(options, question):
    """Generate prompts for OpenAI API based on the options and question."""
    return [chat_query_processor(option, question) for option in options]

def call_openai_api(prompts):
    """Call OpenAI API with the generated prompts."""
    # headers = {
    #     "Content-Type": "application/json",
    #     "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
    # }
    
    headers = {
                "Content-Type": "application/json",
                 "Authorization": f"Bearer {os.getenv('OPEN_API_KEY')}",
            }
    
    content = ' '.join(prompts)
    data = {
        "model": "gpt-4",
        "max_tokens": 700,
        "temperature": 0.7,
        "messages": [{"role": "user", "content": content}],
    }
    response = requests.post(OPENAI_API_URL, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

@app.route('/stream/v2')
def streamv2():
    """Stream endpoint to handle questions and return OpenAI API responses."""
    question = request.args.get('question')
    yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')

    logger.info(f'Received question: {question}')

    if not question:
        return Response("No question provided", status=400)

    try:
        symbols = filter_and_find_symbols(question, keywords)
        print('Symbols:', symbols)
        options = fetch_data_from_dynamo(symbols, yesterday)
        print('Options:', options)
        prompts = generate_prompts(options, question)
        print('Prompts:', prompts)
        openai_response = call_openai_api(prompts)
        # print('Prompts:', prompts)
        return Response(openai_response, mimetype='text/event-stream')
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return Response(f"An error occurred: {e}", status=500)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)

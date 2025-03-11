import os
import sys
import json
import requests
import logging
import numpy as np
from flask import Response, request, jsonify
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from web import create_app, iSearch, iCryptoSearch
from . import stop, query_dynamo, chat_query_processor, find_company_by_name
from .keywords import keywords

widget_mappings = {
    'equity_coin_carousel': {
        'description': 'Displays a carousel of equity coins with relevant data.',
        'expected_parameters': {
            'name': 'Name of the equity coin',
            'ticker': 'Ticker symbol of the equity coin',
            'currency': 'Currency of the equity coin',
            'stockValue': 'Current stock value',
            'duration': 'Duration of the data',
            'isPositiveChange': 'Boolean indicating if the change is positive',
            'changeValue': 'Change value in percentage',
            'chart1w': 'Chart data for the last week',
            'capsule': 'List of capsule data'
        }
    },
    'entity_card_img': {
        'description': 'Displays an entity card with an image and relevant data.',
        'expected_parameters': {
            'route': 'Route for the entity',
            'entityName': 'Name of the entity',
            'currency': 'Currency of the entity',
            'value': 'Current value of the entity',
            'percentageValue': 'Percentage value of the entity',
            'isProfit': 'Boolean indicating if the entity is profitable',
            'color': 'Color of the entity card',
            'dropShadow': 'Boolean indicating if the card should have a drop shadow',
            'hasImage': 'Boolean indicating if the card has an image',
            'imgUrl': 'URL of the image'
        }
    }
}


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
    logger.info(f'Equity Query: {query}')
    search_res = iSearch.query(query)
    return jsonify(search_res)

@app.route('/crypto-api', methods=['GET', 'POST'])
def crypto_api():
    query = request.args.get('query', '')
    logger.info(f'Crypto Query: {query}')
    search_res = iCryptoSearch.query(query)
    return jsonify(search_res)

def filter_and_find_symbols(question, keywords, top_n=5):
    """
    Filter and find symbols based on the question and keywords using TF-IDF and exact matching.
    """
    # Step 1: Exact matching
    lower_question = question.lower()
    exact_matches = []

    for company, symbol in keywords.items():
        if company.lower() in lower_question:
            exact_matches.append(symbol)

    # If exact matches are found, return them immediately
    if exact_matches:
        return exact_matches

    # Step 2: TF-IDF similarity for partial or contextual matches
    company_names = list(keywords.keys())
    vectorizer = TfidfVectorizer().fit_transform([question] + company_names)
    vectors = vectorizer.toarray()

    # Calculate cosine similarity
    question_vector = vectors[0].reshape(1, -1)
    company_vectors = vectors[1:]
    cosine_similarities = cosine_similarity(question_vector, company_vectors).flatten()

    # Get the indices of the top_n most similar company names
    top_indices = np.argsort(cosine_similarities)[-top_n:][::-1]  # Reverse to get highest similarity first

    # Get the corresponding company symbols
    matched_symbols = [list(keywords.values())[i] for i in top_indices]

    return matched_symbols if matched_symbols else None


def fetch_data_from_dynamo(symbols, date):
    """
    Fetch data from DynamoDB for the given symbols and date.
    """
    results = []
    for symbol in symbols:
        result = query_dynamo(date, symbol)
        results.append(result)
    
    # print('results:', results)
    return results

def generate_prompts(options, question, previous_context):
    """
    Generate prompts for OpenAI API based on the options, question, and previous context.
    """
    prompts = [chat_query_processor(option, question) for option in options]
    prompts.append(previous_context)
    return prompts

def call_openai_api(prompts):
    """
    Call OpenAI API with the generated prompts.
    """
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


@app.route('/chat', methods=['POST'])
def chat():
    """
    Stream endpoint to handle questions and return OpenAI API responses.
    """
    try:
        prompt = request.form.get('prompt')
        if not prompt:
            return Response("No prompt provided", status=400)

        # Parse the JSON payload from the prompt
        payload = json.loads(prompt)
        current_question = payload.get('current_question')
        previous_questions = payload.get('previous_questions', [])
        previous_answers = payload.get('previous_answers', [])

        if not current_question:
            return Response("No current question provided", status=400)

        logger.info(f'Received question: {current_question}')
        logger.info(f'Previous questions: {previous_questions}')
        logger.info(f'Previous answers: {previous_answers}')

        yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')

        # Build the previous context
        previous_context = ''
        # for q, a in zip(previous_questions, previous_answers):
        #     previous_context += f"Q: {q}\nA: {a}\n"

        symbols = filter_and_find_symbols(current_question, keywords)
        print('symbols:', symbols)
        options = fetch_data_from_dynamo(symbols, yesterday)
        print('options:', options)
        prompts = generate_prompts(options, current_question, previous_context)
        print('prompts:', prompts)
        openai_response = call_openai_api(prompts)
        print('openai_response:', openai_response)
       

        # Check if the response contains a widget command
        try:
            response_data = json.loads(openai_response)
            if 'widget' in response_data:
                widget_command = response_data['widget']
                widget_payload = response_data.get('payload', {})
                response_data['widget_info'] = widget_mappings.get(widget_command, {})
                response_data['widget_payload'] = widget_payload

                print('plain_text:')
                print('openai_response:', openai_response)

            return Response(json.dumps(response_data), mimetype='application/json')
        except json.JSONDecodeError:
            # If the response is not JSON, return it as plain text
            print('plain_text:')
            print('openai_response:', openai_response)
            return Response(openai_response, mimetype='text/event-stream')
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return Response(f"An error occurred: {e}", status=500)

    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)

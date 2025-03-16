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
# from openai import OpenAI
from openai import OpenAI

from web import create_app, iSearch, iCryptoSearch
from . import stop, query_dynamo, chat_query_processor, find_company_by_name
from .keywords import keywords


# Initialize the client
client = OpenAI(api_key="sk-", base_url="htek.com")

def call_reasoning_model(content):
    messages = [{"role": "user", "content": content}]
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=messages
    )

    # reasoning_content = response.choices[0].message.reasoning_content
    message = response.choices[0].message.content

    return message



widgets_mappings = [
    {
        "id": "companies_organization_business_widget",
        "widget_type": "equity",
        "category": "equity",
        "related_keywords": ["companies", "organization", "business"],
        "description": "Here is a brief description for the equity widget and prompt.",
        "parameters": [
            {"name": "entityCardData", "type": "List", "description": "List of data objects for EntityCards"},
            {"name": "route", "type": "String", "description": "Navigation route"},
            {"name": "entityName", "type": "String", "description": "Display name of entity"},
            {"name": "currency", "type": "String", "description": "Currency symbol"},
            {"name": "value", "type": "double", "description": "Numerical value"},
            {"name": "percentageValue", "type": "double", "description": "Percentage change"},
            {"name": "isProfit", "type": "bool", "description": "Profit/loss indicator"},
            {"name": "color", "type": "Color", "description": "Card background color"},
            {"name": "dropShadow", "type": "bool", "description": "Shadow visibility"},
            {"name": "hasImage", "type": "bool", "description": "Image display toggle"},
            {"name": "imgUrl", "type": "String", "description": "Image URL"}
        ]
    },
    {
        "id": "cryptocurrency_widget",
        "widget_type": "WidgetType.cryptoCardWidget",
        "category": "crypto",
        "related_keywords": ["crypto", "cryptocurrencies", "bitcoin", "ethereum", "btc"],
        "description": "Here is a brief description for the equity widget and prompt.",
        "parameters": []
    },
    {
        "id": "ceo_leadership_widget",
        "widget_type": "WidgetType.metricsEquity",
        "category": "crypto",
        "related_keywords": ["crypto", "cryptocurrencies", "bitcoin", "ethereum", "btc"],
        "description": "Here is a brief description for the ceo widget and prompt.",
        "parameters": [
            {"name": "metrics", "type": "List", "description": "List of metrics"},
            {"name": "person", "type": "Profile", "description": "CEO profile data"},
            {"name": "description", "type": "String", "description": "Company description"}
        ]
    },
    {
        "id": "earnings_revenue_widget",
        "widget_type": "WidgetType.customTabs",
        "category": "crypto",
        "related_keywords": ["crypto", "cryptocurrencies", "bitcoin", "ethereum", "btc"],
        "description": "Here is the breakdown of earnings.",
        "parameters": [
            {"name": "annualEarnings", "type": "List", "description": "Yearly earnings data"},
            {"name": "quaterlyEarnings", "type": "List", "description": "Quarterly earnings data"},
            {"name": "metrics", "type": "List", "description": "Company performance metrics"}
        ]
    },
    {
        "id": "web_internet_widget",
        "widget_type": "WidgetType.browserWidget",
        "category": "crypto",
        "related_keywords": ["crypto", "cryptocurrencies", "bitcoin", "ethereum", "btc"],
        "description": "Here is a brief description for the web widget and prompt.",
        "parameters": [
            {"name": "height", "type": "int", "description": "Fixed height"},
            {"name": "query", "type": "String", "description": "Search query from parameters"}
        ]
    },
    {
        "id": "document_text_widget",
        "widget_type": "WidgetType.documentWidget",
        "category": "crypto",
        "related_keywords": ["crypto", "cryptocurrencies", "bitcoin", "ethereum", "btc"],
        "description": "Here is a brief description for the document widget and prompt.",
        "parameters": []
    },
    {
        "id": "stocks_time_series_widget",
        "widget_type": "WidgetType.timeSeriesWidget",
        "category": "crypto",
        "related_keywords": ["crypto", "cryptocurrencies", "bitcoin", "ethereum", "btc"],
        "description": "Here is a brief description for the chart widget and prompt.",
        "parameters": [
            {"name": "chartAll", "type": "ChartData", "description": ""},
            {"name": "chart1y", "type": "ChartData", "description": ""},
            {"name": "chart6m", "type": "ChartData", "description": ""},
            {"name": "chart1w", "type": "ChartData", "description": ""},
            {"name": "chart1m", "type": "ChartData", "description": ""},
            {"name": "chart1yStepLine", "type": "ChartData", "description": ""},
            {"name": "stepLineLeastValue", "type": "double", "description": ""},
            {"name": "stepLineMaxValue", "type": "double", "description": ""}
        ]
    },
    {
        "id": "balance_sheet_widget",
        "widget_type": "WidgetType.balanceSheetWidget",
        "category": "crypto",
        "related_keywords": ["crypto", "cryptocurrencies", "bitcoin", "ethereum", "btc"],
        "description": "Here is a brief description for the balance sheet widget and prompt.",
        "parameters": [
            {"name": "benchmark", "type": "List", "description": "Benchmark data"},
            {"name": "assets", "type": "List", "description": "Assets data"},
            {"name": "liability", "type": "List", "description": "Liabilities data"}
        ]
    },
    {
        "id": "pdf_widget",
        "widget_type": "WidgetType.pdfWidget",
        "category": "pdf",
        "related_keywords": ["pdf", "doc"],
        "description": "Here is a brief description for the pdf widget and prompt.",
        "parameters": [
            {"name": "url", "type": "String", "description": "PDF URL"}
        ]
    }
]


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
        print('CHAT<>')
        prompt = request.get_json('message')
        print('prompt1:', prompt)
        if not prompt:
            return Response("No prompt provided", status=400)

        print('prompt:', prompt)
        """
        {
            "current_question": "What is the market cap of Apple?",
            "previous_questions": ["What is the market cap of Apple?"],
            # "previous_answers": ["Apple's market cap is $2 trillion."]
        }
        """
        # Step 1: Ask o1 "what information do you think the user is asking? (returns a list of multiple topics, break it down)"
        # Add a check to return company code i.e APPL for Apple or MSFT for Microsoft etc Also add for crypto
        # result = call_reasoning_model(prompt)
        # print('result:', result)

        widget_prompt = f" ```{widgets_mappings}```"
        print('widget_prompt:', widget_prompt)
        
        # Step2: Ask o1 "With each topics(widgets) in the list `widgets_mappings` (indexed by K): (for loop over all topics/widgets)
        #  could you tell me which widgets from the widget list we should call for the user's question? (returns a list of widgets)"
        #  "

        # # Parse the JSON payload from the prompt
        # payload = json.loads(prompt)
        # current_question = payload.get('current_question')
        # previous_questions = payload.get('previous_questions', [])
        # previous_answers = payload.get('previous_answers', [])

        # if not current_question:
        #     return Response("No current question provided", status=400)

        # logger.info(f'Received question: {current_question}')
        # logger.info(f'Previous questions: {previous_questions}')
        # logger.info(f'Previous answers: {previous_answers}')

        # yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')

        # Build the previous context
        # previous_context = ''
        # for q, a in zip(previous_questions, previous_answers):
        #     previous_context += f"Q: {q}\nA: {a}\n"

        # symbols = filter_and_find_symbols(current_question, keywords)
        # print('symbols:', symbols)
        # options = fetch_data_from_dynamo(symbols, yesterday)
        # print('options:', options)
        # prompts = generate_prompts(options, current_question, previous_context)
        # print('prompts:', prompts)
        # openai_response = call_openai_api(prompts)
        # print('openai_response:', openai_response)
       

        # Check if the response contains a widget command
        try:
            # response_data = json.loads(openai_response)
            response_data = 'json.loads(openai_response)'
            # if 'widget' in response_data:
            #     widget_command = response_data['widget']
            #     widget_payload = response_data.get('payload', {})
            #     response_data['widget_info'] = widget_mappings.get(widget_command, {})
            #     response_data['widget_payload'] = widget_payload

            #     print('plain_text:')
            #     # print('openai_response:', openai_response)

            return Response(json.dumps(response_data), mimetype='application/json')
        except json.JSONDecodeError:
            # If the response is not JSON, return it as plain text
            print('plain_text:')
            # print('openai_response:', openai_response)
            # return Response(openai_response, mimetype='text/event-stream')
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return Response(f"An error occurred: {e}", status=500)

    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)

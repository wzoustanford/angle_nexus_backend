import os
import sys
import json
import requests
import decimal
import logging
import numpy as np
from flask import Response, request, jsonify
from datetime import date, datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from decimal import Decimal

from web import create_app, iSearch, iCryptoSearch
from . import stop, query_dynamo, chat_query_processor, find_company_by_name
from .keywords import keywords
from .apis.fmp_api import get_finance_api_data
from .apis.reasoning import ReasoningChatClient
from .prompts.prompts import query_analysis_prompt, fintech_apis_prompt, combine_results_sys_promt, widget_sys_prompt

app = create_app()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Choose the model for the chat client (switch easily if needed)
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
        print("Fetching data for symbol:", symbol)
        result = query_dynamo(date, symbol)
        if result is not None:
            results.append(result)
    return results

def generate_prompts(options, question, previous_context):
    """
    Generate prompts for OpenAI API based on the options, question, and previous context.
    """
    prompts = [chat_query_processor(option, question) for option in options]
    prompts.append(previous_context)
    return prompts



@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint to handle chat requests and return responses using the OpenAI API.
    """
    try:
        # Retrieve the JSON prompt from the request
        request_data = request.get_json()
        user_input = request_data.get('message') if request_data else None
        # user_input = """"""
        print('user_input:', user_input)

        if not user_input:
            return Response("No prompt provided", status=400)

        # Prepare system prompts and API details
        system_prompt = query_analysis_prompt()
        fin_apis_details = fintech_apis_prompt()
        today_date = date.today()

        # Compose the initial message for LLM processing
        initial_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (
                f"Here is Financial APIs details:\n{fin_apis_details}, and here is the user input: {user_input}.\n"
                f"Today Date is: {today_date}"
            )},
        ]

        print(f"Processing initial chat completion using {model} model...")
        llm_response_text = chat_client.create_chat_completion(initial_messages)
        print("Initial chat completion complete.")
        with open('messages1.json', 'w') as file:
                    json.dump(llm_response_text, file)

        # Process the LLM response for JSON content
        if model == "deepseek-reasoner":
            cleaned_response = llm_response_text.strip("```json").strip("```").strip()
            llm_json_response = json.loads(cleaned_response)
        else:
            llm_json_response = json.loads(llm_response_text)

        print("LLM API Response:", json.dumps(llm_json_response, indent=4))
        
        # Initialize a list to store symbols
        symbols_set = set()

        # Call Finance APIs based on LLM response keys and accumulate results
        finance_api_responses = {}
        if llm_json_response:
            for key, api_json in llm_json_response.items():
                # Extract the symbol and add it to the symbols list
                symbol = api_json.get('symbol')
                if symbol:
                    symbols_set.add(symbol)

                response = get_finance_api_data(api_json['api'])
                if response:
                    finance_api_responses[key] = response
            
            # extract all the symbols from the variable and call dynmodb
            # call the function to get the data from dynamoDB
            dynamo_response = fetch_data_from_dynamo(list(symbols_set), today_date.isoformat())
            

            print("Finance API calls complete.")

            # If finance API data is available, combine results and generate widget response
            if finance_api_responses:
                # Combine results with a follow-up LLM call
                combine_messages = [
                    {"role": "system", "content": combine_results_sys_promt()},
                    {"role": "user", "content": (
                        f"Here is Financial APIs responses:\n{json.dumps(finance_api_responses)}, and here is the user input: {user_input}.\n"
                        f"Today Date is: {today_date}"
                    )},
                ]
                print(f"Combining results using {model} model...")
                combined_response = chat_client.create_chat_completion(combine_messages)
                print("Combined results complete.")
                with open('messages2.json', 'w') as file:
                    json.dump(combined_response, file)

                # Create widget message using combined response and original LLM output
                widget_messages = [
                    {"role": "system", "content": widget_sys_prompt()},
                    {"role": "user", "content": (
                        f"Here is the user input {llm_json_response} \n and here is the explanation: {combined_response}"
                    )},
                ]

                # Optionally save the widget messages to a file for debugging or logging
                print('Saving widget messages to messages3.json')
                with open('messages3.json', 'w') as file:
                    json.dump(widget_messages, file)

                widget = chat_client.create_chat_completion(widget_messages)
                print("Widget response complete.")
                print("Widget:", widget)
                return {"widget": widget, "message": combined_response, "data":dynamo_response}
            else:
                print("No finance API data found.")
        else:
            print("No LLM API response found.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return Response(f"An error occurred: {e}", status=500)


@app.route('/update_dynamo_response', methods=['POST'])
def update_dynamo_response():
    try:
        today_date = date.today()
        symbols = ['TSLA', 'MSFT']

        if not symbols or not today_date:
            return jsonify({"error": "Missing symbols or today_date in request"}), 400
        
        print("Fetching data from DynamoDB for symbols:", symbols)

        # Fetch data from DynamoDB
        dynamo_response = fetch_data_from_dynamo(symbols, today_date.isoformat())

        return jsonify({"message": "Data saved to text file.", "response": dynamo_response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)

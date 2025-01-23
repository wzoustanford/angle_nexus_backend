import os
import sys
import json
import requests
from web import create_app, iSearch, iCryptoSearch
from flask import Response, request, jsonify
from datetime import datetime, timedelta
# from sseclient import SSEClient
from . import stop, query_dynamo, chat_query_processor, find_company_by_name
from .keywords import keywords

# Add the parent directory (project root) to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

app = create_app()

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)

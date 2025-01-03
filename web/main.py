import sys
import os
from web import create_app, iSearch, iCryptoSearch
from flask import jsonify, request

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)

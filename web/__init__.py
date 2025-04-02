import os
import logging
from dotenv import load_dotenv
from flask import Flask
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import nltk
from nltk.corpus import stopwords
from search.illumenti_search import IllumentiSearch
from search.illumenti_crypto_search import IllumentiCryptoSearch

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))
# Construct the path to the .env file in the parent directory
dotenv_path = os.path.join(script_dir, '../.env')

# Load the .env file
load_dotenv(dotenv_path=dotenv_path)

# Initialize search objects
iSearch = IllumentiSearch()
iCryptoSearch = IllumentiCryptoSearch()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

nltk.download("stopwords")

# Setup shared resources
stop = set(stopwords.words("english"))

# Initialize DynamoDB connection
client = boto3.resource(
    service_name='dynamodb',
    region_name=os.getenv('AWS_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
equity_table = client.Table('Equity')

# Shared Helper Functions
def find_company_by_name(name, companies):
    """
    Find a company ticker by name.
    """
    for company, ticker in companies.items():
        if company.lower().find(name.lower()) != -1:
            return ticker
    return None

def query_dynamo(symbol, date):
    """
    Query DynamoDB for a given date and symbol.
    """
    try:
        print("Date:", date, "Symbol: ", symbol)
        response = equity_table.get_item(Key={'ds': date, 'symbol': symbol})
        if 'Item' in response:
            return response['Item']
        else:
            print(f"No item found for date: {date}, symbol: {symbol}")
            print('RESPONSEEEEE', response)
            return None
    except ClientError as e:
        logger.error(f"Failed to query DynamoDB: {e}")
        return None
    
def  fetch_data_from_dynamo(symbols, date):
    """
    Fetch data from DynamoDB for the given symbols and date.
    """
    results = []
    for symbol in symbols:
        print("Fetching data for symbol:", symbol)
        result = query_dynamo(symbol, date)
        if result is not None:
            results.append(result)
    return results
    

def chat_query_processor(response, current_context):
    """
    Process the DynamoDB response and generate a prompt for the chat model.
    """
    if 'Item' not in response:
        return "No data found."

    data = response['Item']
    company_name = data.get('name', 'Unknown Company')

    market_cap_value = data.get('key_metrics', [{}])[0].get('value', None)
    market_cap_unit = data.get('key_metrics', [{}])[0].get('unit', 'Unknown')
    market_cap_unit = 'billion' if market_cap_unit == 'B' else 'million'

    annual_earnings = data.get('annual_earnings', [{}])[0]
    equity_liabilities = data.get('equity_liabilities', [{}])[0]
    key_metrics = data.get('key_metrics', [{}])[0]
    quarterly_earnings = data.get('quaterly_earnings', [{}])[0]

    prompt = f"""
    B is for billion, M is for Million.
    {company_name}.
    Key Metrics: {key_metrics}.
    Annual Earnings: {annual_earnings}.
    Quarterly Earnings: {quarterly_earnings}.
    Equity Liabilities: {equity_liabilities}.
    Market Cap: {market_cap_value} {market_cap_unit}.
    """
    return prompt.strip() + current_context

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'wearetherebels'

    # Blueprint imports
    from .views import views  # to avoid circular imports
    app.register_blueprint(views, url_prefix='/')

    # Use dynamic paths for dataset loading
    base_path = os.path.dirname(os.path.abspath(__file__))
    # Updated path to point to root 'data' directory
    data_path = os.path.join(base_path, '..', 'data')

    # Load datasets
    try:
        nyse_file = os.path.join(data_path, 'equity_nyse_exported_table.csv')
        nasdaq_file = os.path.join(data_path, 'equity_nasdaq_exported_table.csv')
        logger.info(f"Loading equity datasets: NYSE ({nyse_file}), NASDAQ ({nasdaq_file})")
        iSearch.load_dataset(nyse_file, nasdaq_file)
        iSearch.build_index()
        logger.info("Equity datasets loaded and indexed successfully.")
    except Exception as e:
        logger.error(f"Failed to load or index equity datasets: {e}", exc_info=True)

    try:
        crypto_file = os.path.join(data_path, 'crypto_info_table_full.csv')
        logger.info(f"Loading crypto dataset: {crypto_file}")
        iCryptoSearch.load_dataset(crypto_file)
        iCryptoSearch.build_index()
        logger.info("Crypto dataset loaded and indexed successfully.")
    except Exception as e:
        logger.error(f"Failed to load or index crypto dataset: {e}", exc_info=True)

    return app

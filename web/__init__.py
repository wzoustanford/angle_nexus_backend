import os
from dotenv import load_dotenv
from flask import Flask
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import nltk
import finnhub
from nltk.corpus import stopwords
from .logging_config import logger 
from search.illumenti_search import IllumentiSearch
from search.illumenti_crypto_search import IllumentiCryptoSearch

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))
dotenv_path = os.path.join(script_dir, '../.env')

# Load the .env file
load_dotenv(dotenv_path=dotenv_path)

# Download the NLTK stopwords
nltk.download("stopwords")

# Setup shared resources
stop = set(stopwords.words("english"))

# Initialize DynamoDB connection
try:
    client = boto3.resource(
        service_name='dynamodb',
        region_name=os.getenv('AWS_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    equity_table = client.Table('Equity')
except Exception as e:
    logger.error("Failed to initialize DynamoDB client or table: %s", e, exc_info=True)

# Finnhub REST client – requires env var FINNHUB_API_KEY
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
if not FINNHUB_API_KEY:
    raise RuntimeError("Missing FINNHUB_API_KEY environment variable")

finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

def fetch_company_news(symbol: str, date_from: str, date_to: str) -> list[dict]:
    """Wrap finnhub.company_news, always returns a *list* (possibly empty).
    Adds the originating symbol to each item so the client knows the source.
    Swallows Finnhub errors but logs them – prevents one bad ticker from
    breaking the whole response.
    """
    try:
        raw = finnhub_client.company_news(symbol, _from=date_from, to=date_to)
    except Exception as exc:  
        logger.exception("Finnhub company_news failed for %s: %s", symbol, exc)
        return []

    for item in raw:
        item["symbol"] = symbol  
    return raw

# Initialize search objects
iSearch = IllumentiSearch()
iCryptoSearch = IllumentiCryptoSearch()

def query_dynamo(symbol, date):
    """
    Query DynamoDB for a given date and symbol.
    """
    if not symbol or not date:
        logger.warning("query_dynamo called with empty symbol/date. symbol=%s, date=%s", symbol, date)
        return None

    try:
        response = equity_table.get_item(Key={'ds': date, 'symbol': symbol})
        item = response.get('Item')

        if item:
            logger.debug("DynamoDB item retrieved for symbol=%s, date=%s", symbol, date)
            return item
        else:
            logger.warning("No item found for date=%s, symbol=%s", date, symbol)
            return {}
    except ClientError as e:
        logger.error("Failed to query DynamoDB for symbol=%s, date=%s: %s", symbol, date, e, exc_info=True)
        return None
    except Exception as e:
        logger.error("Unexpected error querying DynamoDB: %s", e, exc_info=True)
        return None

def fetch_data_from_dynamo(symbols, date):
    """
    Fetch data from DynamoDB for the given symbols and date.
    """
    if not symbols:
        logger.warning("fetch_data_from_dynamo called with no symbols provided.")
        return []

    results = []
    for symbol in symbols:
        logger.info("Fetching data for symbol=%s, date=%s", symbol, date)
        result = query_dynamo(symbol, date)

        if result is None:
            # Query failed or unexpected error
            logger.warning("Skipping symbol=%s due to failed DynamoDB query.", symbol)
            continue

        if not result:
            # The query returned an empty dict (no data found)
            logger.warning("No data returned for symbol=%s on date=%s", symbol, date)
            continue

        # If we have valid data, add it to results
        results.append(result)
    
    return results

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'wearetherebels'

    # Blueprint imports
    from .views import views  # to avoid circular imports
    app.register_blueprint(views, url_prefix='/')

    # Use dynamic paths for dataset loading
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, '..', 'data')

    # Load equity datasets
    try:
        nyse_file = os.path.join(data_path, 'equity_nyse_exported_table.csv')
        nasdaq_file = os.path.join(data_path, 'equity_nasdaq_exported_table.csv')
        logger.info("Loading equity datasets: NYSE (%s), NASDAQ (%s)", nyse_file, nasdaq_file)
        iSearch.load_dataset(nyse_file, nasdaq_file)
        iSearch.build_index()
        logger.info("Equity datasets loaded and indexed successfully.")
    except Exception as e:
        logger.error("Failed to load or index equity datasets: %s", e, exc_info=True)

    # Load crypto dataset
    try:
        crypto_file = os.path.join(data_path, 'crypto_info_table_full.csv')
        logger.info("Loading crypto dataset: %s", crypto_file)
        iCryptoSearch.load_dataset(crypto_file)
        iCryptoSearch.build_index()
        logger.info("Crypto dataset loaded and indexed successfully.")
    except Exception as e:
        logger.error("Failed to load or index crypto dataset: %s", e, exc_info=True)

    return app

"""
Shared extensions and global objects for the Flask application.
This module initializes objects that need to be shared across the application.
"""
import boto3
from botocore.exceptions import ClientError
from .logging_config import logger
from .config import Config
from search.illumenti_search import IllumentiSearch
from search.illumenti_crypto_search import IllumentiCryptoSearch

# Initialize search objects (shared across application)
iSearch = IllumentiSearch()
iCryptoSearch = IllumentiCryptoSearch()

# Initialize DynamoDB connection
try:
    dynamodb_client = boto3.resource(
        service_name='dynamodb',
        region_name=Config.AWS_REGION,
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
    )
    equity_table = dynamodb_client.Table(Config.DYNAMODB_TABLE)
    logger.info("DynamoDB client initialized successfully")
except Exception as e:
    logger.error("Failed to initialize DynamoDB client or table: %s", e, exc_info=True)
    equity_table = None


def init_search_indexes():
    """Initialize search indexes with data"""
    try:
        # Load equity datasets
        logger.info("Loading equity datasets: NYSE (%s), NASDAQ (%s)", Config.NYSE_FILE, Config.NASDAQ_FILE)
        iSearch.load_dataset(Config.NYSE_FILE, Config.NASDAQ_FILE)
        iSearch.build_index()
        logger.info("Equity datasets loaded and indexed successfully.")
    except Exception as e:
        logger.error("Failed to load or index equity datasets: %s", e, exc_info=True)

    # Load crypto dataset
    try:
        logger.info("Loading crypto dataset: %s", Config.CRYPTO_FILE)
        iCryptoSearch.load_dataset(Config.CRYPTO_FILE)
        iCryptoSearch.build_index()
        logger.info("Crypto dataset loaded and indexed successfully.")
    except Exception as e:
        logger.error("Failed to load or index crypto dataset: %s", e, exc_info=True)

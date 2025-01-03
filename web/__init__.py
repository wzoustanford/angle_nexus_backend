import logging
import os
from flask import Flask
from search.illumenti_search import IllumentiSearch
from search.illumenti_crypto_search import IllumentiCryptoSearch

# Initialize search objects
iSearch = IllumentiSearch()
iCryptoSearch = IllumentiCryptoSearch()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

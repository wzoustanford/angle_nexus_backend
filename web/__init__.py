import os
import nltk
from nltk.corpus import stopwords
from flask import Flask
from .logging_config import logger
from .config import get_config
from .extensions import iSearch, iCryptoSearch, init_search_indexes
from .middleware import init_cors, init_error_handlers
from .api import register_blueprints

# Download the NLTK stopwords
nltk.download("stopwords")

# Setup shared resources
stop = set(stopwords.words("english"))


def create_app(config_name=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_name: Configuration environment name (development, production, testing)
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config_obj = get_config(config_name)
    app.config.from_object(config_obj)
    
    # Initialize middleware
    init_cors(app)
    init_error_handlers(app)
    
    # Register traditional views blueprint (for backward compatibility)
    from .views import views
    app.register_blueprint(views, url_prefix='/')
    
    # Register new API blueprints
    register_blueprints(app)
    
    # Initialize search indexes
    init_search_indexes()
    
    logger.info("Flask application created and configured successfully")
    
    return app


# For backward compatibility - expose these at module level
from .services.dynamo_service import query_dynamo, fetch_data_from_dynamo

__all__ = [
    'create_app',
    'iSearch',
    'iCryptoSearch',
    'query_dynamo',
    'fetch_data_from_dynamo',
]

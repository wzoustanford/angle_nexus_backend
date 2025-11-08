"""
Configuration management for the Flask application.
Centralizes all configuration settings, environment variables, and constants.
"""
import os
from dotenv import load_dotenv

# Load environment variables
script_dir = os.path.dirname(os.path.realpath(__file__))
dotenv_path = os.path.join(script_dir, '../.env')
load_dotenv(dotenv_path=dotenv_path)


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'wearetherebels')
    
    # AWS Configuration
    AWS_REGION = os.environ.get('AWS_REGION')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    DYNAMODB_TABLE = 'Equity'
    
    # API Keys
    FINANCIAL_KEY = os.environ.get('FINANCIAL_KEY')
    OPENAI_KEY = os.environ.get('OPENAI_KEY')
    DEEPSEEK_KEY = os.environ.get('DEEPSEEK_KEY')
    DEEPSEEK_BASE_URL = os.environ.get('DEEPSEEK_BASE_URL')
    
    # AI Model Configuration
    DEFAULT_MODEL = "o3-mini"
    ALLOWED_MODELS = ["o3-mini", "GPT-4o", "deepseek-reasoner", "o1", "o1-mini"]
    
    # CORS Configuration
    CORS_ORIGINS = "*"
    CORS_HEADERS = "Content-Type,Authorization"
    CORS_METHODS = "GET,PUT,POST,DELETE,OPTIONS"
    
    # Data Paths
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(BASE_PATH, '..', 'data')
    NYSE_FILE = os.path.join(DATA_PATH, 'equity_nyse_exported_table.csv')
    NASDAQ_FILE = os.path.join(DATA_PATH, 'equity_nasdaq_exported_table.csv')
    CRYPTO_FILE = os.path.join(DATA_PATH, 'crypto_info_table_full.csv')
    
    # Application Settings
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5001
    
    # Conversation Settings
    CONVERSATION_WINDOW_SIZE = 6
    
    # API Settings
    API_VERSION = 'v1'
    MAX_RETRIES = 3
    WAIT_TIME = 5


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

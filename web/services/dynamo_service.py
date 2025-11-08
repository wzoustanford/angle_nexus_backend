"""
DynamoDB Service
Handles all DynamoDB operations for fetching equity data.
"""
from botocore.exceptions import ClientError
from ..logging_config import logger
from ..extensions import equity_table
import decimal
from typing import List, Dict, Any, Optional


def convert_decimals(obj):
    """
    Recursively converts Decimal objects in a data structure to int or float.
    
    Args:
        obj: The object to convert (can be list, dict, Decimal, or any other type)
        
    Returns:
        The converted object with Decimals replaced by int or float
    """
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, decimal.Decimal):
        # Convert to int if possible, otherwise float
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj


def query_dynamo(symbol: str, date: str) -> Optional[Dict[str, Any]]:
    """
    Query DynamoDB for a given date and symbol.
    
    Args:
        symbol: Stock ticker symbol
        date: Date in ISO format (YYYY-MM-DD)
        
    Returns:
        Dictionary containing the item data, empty dict if not found, None on error
    """
    if not symbol or not date:
        logger.warning("query_dynamo called with empty symbol/date. symbol=%s, date=%s", symbol, date)
        return None

    if equity_table is None:
        logger.error("DynamoDB table not initialized")
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


def fetch_data_from_dynamo(symbols: List[str], date: str) -> List[Dict[str, Any]]:
    """
    Fetch data from DynamoDB for the given symbols and date.
    
    Args:
        symbols: List of stock ticker symbols
        date: Date in ISO format (YYYY-MM-DD)
        
    Returns:
        List of dictionaries containing data for each symbol
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

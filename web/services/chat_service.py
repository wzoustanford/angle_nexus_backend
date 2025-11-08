"""
Chat Service (Daimon Agent)
Handles the main chat functionality with classification, data fetch, and widget generation.
"""
import json
from datetime import date
from typing import Dict, Any, List, Optional
from ..logging_config import logger
from ..config import Config
from .classification_service import classify_user_query
from .dynamo_service import fetch_data_from_dynamo
from .widget_service import generate_widget_response


def process_chat_request(
    user_message: str,
    model_name: str = None,
    history: List[Dict[str, str]] = None,
    current_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Process a chat request through the Daimon agent pipeline.
    
    Args:
        user_message: User's input message
        model_name: AI model to use (defaults to configured model)
        history: Conversation history
        current_date: Current date (defaults to today)
        
    Returns:
        Dictionary with 'message' and 'data' keys
    """
    if model_name is None:
        model_name = Config.DEFAULT_MODEL
    
    if history is None:
        history = []
    
    if current_date is None:
        current_date = date.today()
    
    # --- 1. Classification Phase ---
    logger.info("Starting classification phase for message: %s", user_message[:100])
    extracted_symbols, user_intent, classification_response = classify_user_query(
        user_message,
        model_name,
        current_date
    )
    
    if not user_intent:
        logger.warning("No user_intent found, returning default message.")
        return {
            "message": "Unable to process your request",
            "data": []
        }
    
    # --- 2. DynamoDB Data Fetch ---
    logger.info("Fetching data from DynamoDB for symbols=%s, date=%s", extracted_symbols, current_date)
    dynamo_data = fetch_data_from_dynamo(extracted_symbols, current_date.isoformat())
    
    if not dynamo_data:
        logger.warning("No data returned from DynamoDB")
        return {
            "message": user_intent,
            "data": []
        }
    
    # --- 3. Final Widget Phase ---
    final_message, full_widget_data = generate_widget_response(
        user_intent,
        dynamo_data,
        model_name
    )
    
    return {
        "message": final_message,
        "data": full_widget_data
    }

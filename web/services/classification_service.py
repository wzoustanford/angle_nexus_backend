"""
Classification Service
Handles the classification of user queries to extract symbols and intent.
"""
import json
from datetime import date
from typing import Dict, List, Tuple, Optional
from ..logging_config import logger
from ..prompts.prompts import classify_sys_prompt
from ..clients.reasoning import ReasoningChatClient


def parse_json_from_text(text: str) -> Optional[Dict]:
    """
    Attempts to extract and parse a JSON object from a text string.
    
    Args:
        text: String potentially containing JSON
        
    Returns:
        Dictionary if successful, None if parsing fails
    """
    try:
        if "{" in text and "}" in text:
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            json_text = text[json_start:json_end]
            return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error("JSON parsing failed: %s", e)
    return None


def classify_user_query(
    user_message: str,
    model_name: str = "o3-mini",
    current_date: Optional[date] = None
) -> Tuple[List[str], str, str]:
    """
    Classify user query to extract symbols and intent.
    
    Args:
        user_message: The user's input message
        model_name: The AI model to use for classification
        current_date: Current date (defaults to today)
        
    Returns:
        Tuple of (extracted_symbols, user_intent, classification_response_str)
    """
    if current_date is None:
        current_date = date.today()
    
    chat_client = ReasoningChatClient(model=model_name)
    classification_system_prompt = classify_sys_prompt()
    
    classification_request = [
        {"role": "system", "content": classification_system_prompt},
        {"role": "user", "content": f"User input: {user_message}\nToday: {current_date}"}
    ]
    
    logger.info("Processing classification with model='%s'", model_name)
    classification_response_str = chat_client.create_chat_completion(classification_request)
    logger.info("Classification response received: %s", classification_response_str)

    classification_json = parse_json_from_text(classification_response_str)
    
    if classification_json:
        extracted_symbols = list(classification_json.get('symbols', []))
        user_intent = classification_json.get('message', '')
    else:
        extracted_symbols = []
        user_intent = ""

    logger.info("User Intent extracted: %s", user_intent if user_intent else "None")
    
    return extracted_symbols, user_intent, classification_response_str

"""
Widget Service
Handles widget generation and data processing for financial visualizations.
"""
import json
import copy
from typing import Dict, List, Any, Tuple
from ..logging_config import logger
from ..prompts.prompts import widget_sys_prompt
from ..apis.reasoning import ReasoningChatClient
from .dynamo_service import convert_decimals
from .classification_service import parse_json_from_text


def process_widget_data(
    widget_data: List[Dict[str, Any]],
    keys_to_remove: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Process widget data by removing specified keys.
    
    Args:
        widget_data: List of widget data dictionaries
        keys_to_remove: List of keys to remove from each item
        
    Returns:
        Processed widget data
    """
    if keys_to_remove is None:
        keys_to_remove = ['chart', 'ttl_timestamp']
    
    processed_data = copy.deepcopy(widget_data)
    for item in processed_data:
        for key in keys_to_remove:
            item.pop(key, None)
    
    return processed_data


def generate_widget_response(
    user_intent: str,
    widget_data: List[Dict[str, Any]],
    model_name: str = "o3-mini"
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Generate final widget response with AI-enhanced message.
    
    Args:
        user_intent: The extracted user intent
        widget_data: Financial data from DynamoDB
        model_name: AI model to use
        
    Returns:
        Tuple of (final_message, full_widget_data)
    """
    # Convert decimals in data
    widget_data_converted = convert_decimals(widget_data)
    full_widget_data = copy.deepcopy(widget_data_converted)
    
    # Process data for widget prompt (remove unnecessary keys)
    processed_data = process_widget_data(widget_data_converted)
    
    # Create prompt
    final_prompt_message = (
        f"Based on the user intention {user_intent}\n"
        f"and the DynamoDB Data: {json.dumps(processed_data)}"
    )
    
    # Generate widget response
    chat_client = ReasoningChatClient(model=model_name)
    widget_request = [
        {"role": "system", "content": widget_sys_prompt()},
        {"role": "user", "content": final_prompt_message}
    ]
    
    logger.info("Generating final widget response with model='%s'", model_name)
    final_response_str = chat_client.create_chat_completion(widget_request)
    
    final_json = parse_json_from_text(final_response_str)
    final_message = final_json.get('message') if final_json and 'message' in final_json else final_response_str
    
    return final_message, full_widget_data

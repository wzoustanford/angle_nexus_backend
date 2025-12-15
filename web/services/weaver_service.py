"""
Weaver Service
Handles the Weaver agent logic for gathering and combining financial information.
"""
import json
from datetime import date
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..logging_config import logger
from ..prompts.prompts import q_analysis_sys_prompt, finapis_details, combine_results_sys_promt
from ..clients.reasoning import ReasoningChatClient
from ..clients.fmp_api import get_finance_api_data, RateLimiter
from ..utils.util import format_conversation

# Create a module-level rate limiter for API calls
_rate_limiter = RateLimiter(calls_per_minute=280)


def fetch_data(key: str, api_url: str) -> tuple:
    """
    Helper for concurrency-based data fetch.
    
    Args:
        key: Identifier for the data being fetched
        api_url: URL to fetch data from
        
    Returns:
        Tuple of (key, response)
    """
    logger.debug("Fetching data for key='%s' from URL='%s'", key, api_url)
    response = get_finance_api_data(api_url, _rate_limiter)
    return key, response


def process_weaver_request(
    user_input: str,
    history: List[Dict[str, str]] = None,
    model_name: str = "o3-mini",
    today_date: Optional[date] = None
) -> Dict[str, str]:
    """
    Process a financial chat request using the Weaver agent.
    
    Args:
        user_input: User's query
        history: Conversation history
        model_name: AI model to use
        today_date: Current date (defaults to today)
        
    Returns:
        Dictionary with 'message' key containing the response
    """
    if history is None:
        history = []
    
    if today_date is None:
        today_date = date.today()
    
    # Initialize chat client
    chat_client = ReasoningChatClient(model=model_name)
    sys_prompt = q_analysis_sys_prompt()
    fin_apis_details = finapis_details()

    user_query = (
        f"Here is Financial apis details:\n {fin_apis_details}, and here is the user input: "
        f"{user_input}.\n Today Date is: {today_date}"
    )

    # Build initial conversation
    messages = format_conversation(history, user_query, sys_prompt, window_size=6)
    logger.info("Generating knowledge topics (phase 1) with model='%s'", model_name)
    k_topics_str = chat_client.create_chat_completion(messages)

    # Attempt to parse potential JSON from response
    try:
        k_topics_json = json.loads(k_topics_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse knowledge topics JSON: %s", e)
        k_topics_json = {}

    finance_api_responses = {}
    if k_topics_json:
        # Use ThreadPoolExecutor for parallel data fetch
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(fetch_data, key, api_json['api']): key
                for key, api_json in k_topics_json.items()
            }

            for future in as_completed(futures):
                # Each future returns (key, response)
                key, response = future.result()
                if response:
                    finance_api_responses[key] = response

        # Build next conversation phase with or without finance API data
        if finance_api_responses:
            logger.info("Merging finance API responses into final context.")
            user_input_with_data = (
                f"Here is Financial apis responses:\n {json.dumps(finance_api_responses)}, "
                f"and here is the user input: {user_input}.\n Today Date is: {today_date}"
            )
            messages2 = format_conversation(history, user_input_with_data, combine_results_sys_promt(), window_size=6)
        else:
            logger.warning("No Finance API responses returned, continuing with user input only.")
            messages2 = format_conversation(
                history,
                f"Here is the user input: {user_input}.\n",
                combine_results_sys_promt(),
                window_size=6
            )
    else:
        logger.warning("No knowledge topic JSON extracted, proceeding with user input only.")
        messages2 = format_conversation(
            history,
            f"Here is the user input: {user_input}.\n",
            combine_results_sys_promt(),
            window_size=6
        )

    logger.info("Generating final response (phase 2) with model='%s'", model_name)
    results = chat_client.create_chat_completion(messages2)
    return {"message": results}

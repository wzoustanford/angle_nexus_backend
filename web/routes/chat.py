"""
Chat API Blueprint
Handles all chat-related endpoints (Daimon, Weaver, Avvocato, Sophon agents).
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from ..logging_config import logger
from ..models.model import ChatRequest
from ..config import Config
from ..services.chat_service import process_chat_request
from ..services.weaver_service import process_weaver_request

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


@chat_bp.route('/daimon', methods=['POST'])
def daimon_chat():
    """
    Daimon agent endpoint - Main financial analysis agent.
    Handles classification, data fetching, and widget generation.
    """
    try:
        request_payload = request.get_json(force=True, silent=True)
        if not request_payload:
            logger.warning("No JSON payload provided in /api/chat/daimon request.")
            return jsonify({"error": "Invalid JSON request"}), 400

        user_message = request_payload.get('message')
        if not user_message:
            logger.warning("No 'message' found in /api/chat/daimon request payload.")
            return jsonify({"error": "No message provided"}), 400

        model_name = request_payload.get('model_name', Config.DEFAULT_MODEL)
        history = request_payload.get('history', [])

        # Validate model
        if model_name not in Config.ALLOWED_MODELS:
            logger.warning("Model '%s' not allowed.", model_name)
            return jsonify({"error": f"Model '{model_name}' is not allowed."}), 400

        # Process chat request
        result = process_chat_request(
            user_message=user_message,
            model_name=model_name,
            history=history
        )

        return jsonify(result), 200

    except ValidationError as e:
        logger.warning("Validation error in /api/chat/daimon: %s", e)
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400
    except Exception as exc:
        logger.exception("An error occurred in /api/chat/daimon endpoint.")
        return jsonify({"error": f"An error occurred: {str(exc)}"}), 500


@chat_bp.route('/weaver', methods=['POST'])
def weaver_chat():
    """
    Weaver agent endpoint - Information gathering and synthesis agent.
    Fetches data from external APIs and combines results.
    """
    try:
        request_payload = request.get_json(force=True, silent=True)
        if not request_payload:
            logger.warning("No JSON payload provided in /api/chat/weaver request.")
            return jsonify({"error": "Invalid JSON request"}), 400

        # Ensure required fields are populated
        request_payload.setdefault("user_input", request_payload.get('message'))
        request_payload.setdefault("model_name", Config.DEFAULT_MODEL)
        request_payload.setdefault("history", [])

        try:
            chat_request = ChatRequest(**request_payload)
        except ValidationError as e:
            logger.warning("Validation error in weaver_chat: %s", e)
            return jsonify({"error": f"Invalid input: {str(e)}"}), 400

        if chat_request.model_name not in Config.ALLOWED_MODELS:
            logger.warning("Model '%s' not allowed.", chat_request.model_name)
            return jsonify({"error": f"Model '{chat_request.model_name}' is not allowed."}), 400

        # Process weaver request
        result = process_weaver_request(
            user_input=chat_request.user_input,
            history=chat_request.history,
            model_name=chat_request.model_name
        )

        return jsonify(result), 200

    except Exception as exc:
        logger.exception("An error occurred in /api/chat/weaver endpoint.")
        return jsonify({"error": f"An error occurred: {str(exc)}"}), 500


@chat_bp.route('/avvocato', methods=['POST'])
def avvocato_chat():
    """
    Avvocato agent endpoint - Legal and compliance agent.
    Placeholder for future legal/compliance functionality.
    """
    try:
        request_payload = request.get_json(force=True, silent=True)
        if not request_payload:
            return jsonify({"error": "Invalid JSON request"}), 400

        user_message = request_payload.get('message')
        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Placeholder response - to be implemented
        response = {
            "message": f"Avvocato agent received your query: '{user_message}'. Legal analysis coming soon.",
            "agent": "avvocato",
            "status": "placeholder"
        }

        return jsonify(response), 200

    except Exception as exc:
        logger.exception("An error occurred in /api/chat/avvocato endpoint.")
        return jsonify({"error": f"An error occurred: {str(exc)}"}), 500


@chat_bp.route('/sophon', methods=['POST'])
def sophon_chat():
    """
    Sophon agent endpoint - Interface orchestration agent.
    Determines what users see and orchestrates UX components.
    """
    try:
        request_payload = request.get_json(force=True, silent=True)
        if not request_payload:
            return jsonify({"error": "Invalid JSON request"}), 400

        user_message = request_payload.get('message')
        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Placeholder response - to be implemented
        response = {
            "message": f"Sophon agent received your query: '{user_message}'. Interface orchestration coming soon.",
            "agent": "sophon",
            "status": "placeholder"
        }

        return jsonify(response), 200

    except Exception as exc:
        logger.exception("An error occurred in /api/chat/sophon endpoint.")
        return jsonify({"error": f"An error occurred: {str(exc)}"}), 500

"""
Subscription Routes
Flask endpoints for subscription management
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from ..logging_config import logger
from ..models.subscription_model import (
    ReceiptVerificationRequest,
    VerificationResponse,
    Platform
)
from ..services.subscription_service import SubscriptionService
from ..clients.subscription_api import ReceiptVerificationAPI


subscription_bp = Blueprint('subscription', __name__, url_prefix='/api/subscription')

# Initialize services
subscription_service = SubscriptionService()
verification_api = ReceiptVerificationAPI()


@subscription_bp.route('/verify', methods=['POST'])
def verify_purchase():
    """
    Verify a purchase receipt from iOS or Android
    
    Request Body:
    {
        "user_id": "cognito_user_id",
        "receipt_data": "base64_receipt_or_token",
        "platform": "ios" or "android",
        "product_id": "com.angle.premium.monthly",
        "transaction_id": "optional_transaction_id"
    }
    """
    try:
        # Parse and validate request
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                'success': False,
                'message': 'No JSON data provided',
                'error_code': 'INVALID_REQUEST'
            }), 400
        
        try:
            verification_request = ReceiptVerificationRequest(**request_data)
        except ValidationError as e:
            logger.warning(f"Validation error in verify_purchase: {e}")
            return jsonify({
                'success': False,
                'message': f'Invalid request data: {e}',
                'error_code': 'VALIDATION_ERROR'
            }), 400
        
        logger.info(f"Verifying purchase for user_id={verification_request.user_id}, "
                   f"platform={verification_request.platform}, product_id={verification_request.product_id}")
        
        # Verify receipt with Apple/Google
        success, verified_data, error_msg = verification_api.verify_receipt(
            receipt_data=verification_request.receipt_data,
            platform=verification_request.platform,
            product_id=verification_request.product_id,
            transaction_id=verification_request.transaction_id
        )
        
        if not success:
            logger.error(f"Receipt verification failed: {error_msg}")
            return jsonify({
                'success': False,
                'message': error_msg or 'Receipt verification failed',
                'error_code': 'VERIFICATION_FAILED'
            }), 400
        
        # Extract account identifier from verified data (Apple/Google account)
        # This will be used as the actual user_id for premium users
        account_identifier = verified_data.get('account_identifier')
        
        if account_identifier:
            # Link device ID to Apple/Google account
            # The account_identifier becomes the new user_id
            logger.info(f"Linking device {verification_request.user_id} to account {account_identifier}")
            actual_user_id = account_identifier
            
            # Optional: Migrate existing device data to account
            # You could copy chat counts, etc. here if needed
        else:
            # Fallback to device ID if no account identifier (shouldn't happen)
            logger.warning("No account_identifier in verified_data, using device ID")
            actual_user_id = verification_request.user_id
        
        # Create subscription record with account identifier
        subscription = verification_api.create_subscription_from_receipt(
            user_id=actual_user_id,  # Use Apple/Google account ID
            platform=verification_request.platform,
            receipt_data=verification_request.receipt_data,
            verified_data=verified_data
        )
        
        # Save to DynamoDB
        if not subscription_service.create_or_update_subscription(subscription):
            logger.error("Failed to save subscription to database")
            return jsonify({
                'success': False,
                'message': 'Failed to save subscription',
                'error_code': 'DATABASE_ERROR'
            }), 500
        
        # Get updated status
        status = subscription_service.get_subscription_status(
            user_id=actual_user_id,  # Use Apple/Google account ID
            platform=verification_request.platform
        )
        
        response = VerificationResponse(
            success=True,
            message='Purchase verified successfully',
            subscription=status,
            linked_user_id=actual_user_id  # Return the account ID to frontend
        )
        
        logger.info(f"Purchase verified successfully for user_id={actual_user_id} (device: {verification_request.user_id})")
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error in verify_purchase: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'SERVER_ERROR'
        }), 500


@subscription_bp.route('/status', methods=['GET'])
def get_subscription_status():
    """
    Get subscription status for a user
    
    Query Parameters:
    - user_id: Cognito user ID (required)
    - platform: ios or android (optional, checks both if not specified)
    """
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'user_id parameter required',
                'error_code': 'MISSING_PARAMETER'
            }), 400
        
        platform_str = request.args.get('platform')
        platform = None
        if platform_str:
            try:
                platform = Platform(platform_str.lower())
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid platform. Must be "ios" or "android"',
                    'error_code': 'INVALID_PLATFORM'
                }), 400
        
        logger.info(f"Getting subscription status for user_id={user_id}, platform={platform}")
        
        status = subscription_service.get_subscription_status(user_id, platform)
        
        logger.info(f"📋 STATUS RESPONSE: user_id={user_id}, tier={status.subscription_tier}, "
                   f"chat_count={status.chat_count_today}, remaining={status.remaining_chats}, "
                   f"limit_reached={status.chat_limit_reached}, can_chat={not status.chat_limit_reached or status.features.unlimited_chat}")
        
        return jsonify({
            'success': True,
            'subscription': status.dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_subscription_status: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'SERVER_ERROR'
        }), 500


@subscription_bp.route('/refresh', methods=['POST'])
def refresh_subscription():
    """
    Refresh subscription by re-verifying the receipt
    
    Request Body:
    {
        "user_id": "cognito_user_id",
        "platform": "ios" or "android"
    }
    """
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                'success': False,
                'message': 'No JSON data provided',
                'error_code': 'INVALID_REQUEST'
            }), 400
        
        user_id = request_data.get('user_id')
        platform_str = request_data.get('platform')
        
        if not user_id or not platform_str:
            return jsonify({
                'success': False,
                'message': 'user_id and platform required',
                'error_code': 'MISSING_PARAMETER'
            }), 400
        
        try:
            platform = Platform(platform_str.lower())
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid platform',
                'error_code': 'INVALID_PLATFORM'
            }), 400
        
        logger.info(f"Refreshing subscription for user_id={user_id}, platform={platform}")
        
        # Get existing subscription
        subscription = subscription_service.get_subscription(user_id, platform)
        if not subscription or not subscription.receipt_data:
            return jsonify({
                'success': False,
                'message': 'No subscription found to refresh',
                'error_code': 'NO_SUBSCRIPTION'
            }), 404
        
        # Re-verify receipt
        success, verified_data, error_msg = verification_api.verify_receipt(
            receipt_data=subscription.receipt_data,
            platform=platform,
            product_id=subscription.product_id,
            transaction_id=subscription.transaction_id
        )
        
        if not success:
            logger.warning(f"Receipt re-verification failed: {error_msg}")
            # Don't immediately revoke access, just log the failure
            return jsonify({
                'success': False,
                'message': error_msg or 'Re-verification failed',
                'error_code': 'REVERIFICATION_FAILED'
            }), 400
        
        # Update subscription with new data
        updated_subscription = verification_api.create_subscription_from_receipt(
            user_id=user_id,
            platform=platform,
            receipt_data=subscription.receipt_data,
            verified_data=verified_data
        )
        
        # Preserve chat count
        updated_subscription.chat_count_today = subscription.chat_count_today
        updated_subscription.chat_count_reset_date = subscription.chat_count_reset_date
        
        subscription_service.create_or_update_subscription(updated_subscription)
        
        # Get updated status
        status = subscription_service.get_subscription_status(user_id, platform)
        
        logger.info(f"Subscription refreshed successfully for user_id={user_id}")
        return jsonify({
            'success': True,
            'message': 'Subscription refreshed successfully',
            'subscription': status.dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in refresh_subscription: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'SERVER_ERROR'
        }), 500


@subscription_bp.route('/increment_chat', methods=['POST'])
def increment_chat():
    """
    Increment chat count for a user
    
    Request Body:
    {
        "user_id": "cognito_user_id",
        "platform": "ios" or "android" (optional)
    }
    """
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                'success': False,
                'message': 'No JSON data provided'
            }), 400
        
        user_id = request_data.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'user_id required'
            }), 400
        
        logger.info(f"📊 INCREMENT REQUEST: user_id={user_id}")
        
        platform_str = request_data.get('platform')
        platform = None
        if platform_str:
            try:
                platform = Platform(platform_str.lower())
            except ValueError:
                pass  # Use None if invalid
        
        # Check current status before incrementing
        status = subscription_service.get_subscription_status(user_id, platform)
        
        logger.info(f"📊 BEFORE INCREMENT: user_id={user_id}, tier={status.subscription_tier}, "
                   f"chat_count={status.chat_count_today}, remaining={status.remaining_chats}, "
                   f"limit_reached={status.chat_limit_reached}, unlimited={status.features.unlimited_chat}")
        
        # If limit reached and not premium, deny
        if status.chat_limit_reached and not status.features.unlimited_chat:
            logger.warning(f"⛔ CHAT LIMIT REACHED for user_id={user_id}")
            return jsonify({
                'success': False,
                'message': 'Daily chat limit reached. Upgrade to premium for unlimited chats.',
                'error_code': 'LIMIT_REACHED',
                'subscription': status.dict()
            }), 403
        
        # Increment count
        subscription_service.increment_chat_count(user_id, platform)
        
        # Get updated status
        updated_status = subscription_service.get_subscription_status(user_id, platform)
        
        logger.info(f"✅ AFTER INCREMENT: user_id={user_id}, chat_count={updated_status.chat_count_today}, "
                   f"remaining={updated_status.remaining_chats}, limit_reached={updated_status.chat_limit_reached}")
        
        return jsonify({
            'success': True,
            'message': 'Chat count incremented',
            'subscription': updated_status.dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ ERROR in increment_chat: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@subscription_bp.route('/webhook', methods=['POST'])
def handle_webhook():
    """
    Handle webhooks from Apple/Google for subscription updates
    (Renewals, cancellations, etc.)
    
    TODO: Implement proper webhook validation and signature verification
    """
    try:
        request_data = request.get_json()
        logger.info(f"Received webhook: {request_data}")
        
        # TODO: Implement webhook processing
        # This requires:
        # 1. Signature validation
        # 2. Event type parsing
        # 3. Subscription updates based on events
        
        return jsonify({
            'success': True,
            'message': 'Webhook received (not yet processed)'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in webhook handler: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@subscription_bp.route('/test_mode_status', methods=['GET'])
def test_mode_status():
    """Check if subscription system is in test mode"""
    return jsonify({
        'test_mode': verification_api.test_mode,
        'message': 'Test mode enabled - using mock verification' if verification_api.test_mode else 'Production mode'
    }), 200

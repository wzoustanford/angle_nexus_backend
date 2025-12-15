"""
Receipt Verification APIs
Handles verification of App Store and Google Play receipts
"""
import os
import requests
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from ..logging_config import logger
from ..models.subscription_model import (
    Platform,
    SubscriptionRecord,
    SubscriptionStatus,
    SubscriptionTier,
    ProductConfig
)


class ReceiptVerificationAPI:
    """Handle receipt verification with Apple and Google"""
    
    def __init__(self):
        """Initialize with credentials from environment"""
        # Apple
        self.apple_shared_secret = os.getenv('APPLE_SHARED_SECRET', '')
        self.apple_sandbox_url = 'https://sandbox.itunes.apple.com/verifyReceipt'
        self.apple_production_url = 'https://buy.itunes.apple.com/verifyReceipt'
        
        # Google Play
        self.google_package_name = os.getenv('GOOGLE_PACKAGE_NAME', 'com.angle.www')
        self.google_credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', '')
        
        # Test mode flag
        self.test_mode = os.getenv('SUBSCRIPTION_TEST_MODE', 'true').lower() == 'true'
        
        logger.info(f"ReceiptVerificationAPI initialized (test_mode={self.test_mode})")
    
    def verify_receipt(
        self,
        receipt_data: str,
        platform: Platform,
        product_id: str,
        transaction_id: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Verify receipt with appropriate platform
        Returns: (success, parsed_data, error_message)
        """
        if self.test_mode:
            logger.warning("TEST MODE: Returning mock verification data")
            return self._mock_verification(product_id, platform)
        
        if platform == Platform.IOS:
            return self._verify_apple_receipt(receipt_data, product_id)
        elif platform == Platform.ANDROID:
            return self._verify_google_receipt(receipt_data, product_id, transaction_id)
        else:
            return False, {}, "Unknown platform"
    
    def _verify_apple_receipt(
        self,
        receipt_data: str,
        product_id: str
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Verify Apple App Store receipt"""
        try:
            payload = {
                'receipt-data': receipt_data,
                'password': self.apple_shared_secret,
                'exclude-old-transactions': True
            }
            
            # Try production first
            response = requests.post(
                self.apple_production_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Apple verification failed with status {response.status_code}")
                return False, {}, "Apple API error"
            
            result = response.json()
            status = result.get('status', -1)
            
            # Status 21007 means sandbox receipt sent to production
            if status == 21007:
                logger.info("Sandbox receipt detected, retrying with sandbox URL")
                response = requests.post(
                    self.apple_sandbox_url,
                    json=payload,
                    timeout=10
                )
                result = response.json()
                status = result.get('status', -1)
            
            if status != 0:
                error_msg = self._get_apple_error_message(status)
                logger.error(f"Apple receipt verification failed: {error_msg} (status={status})")
                return False, {}, error_msg
            
            # Parse receipt data
            parsed_data = self._parse_apple_receipt(result, product_id)
            if not parsed_data:
                return False, {}, "Failed to parse receipt data"
            
            logger.info(f"Apple receipt verified successfully for product_id={product_id}")
            return True, parsed_data, None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error verifying Apple receipt: {e}", exc_info=True)
            return False, {}, f"Network error: {str(e)}"
        except Exception as e:
            logger.error(f"Error verifying Apple receipt: {e}", exc_info=True)
            return False, {}, f"Verification error: {str(e)}"
    
    def _parse_apple_receipt(self, receipt_response: Dict, product_id: str) -> Optional[Dict[str, Any]]:
        """Parse Apple receipt response and extract account identifier"""
        try:
            latest_receipt_info = receipt_response.get('latest_receipt_info', [])
            pending_renewal_info = receipt_response.get('pending_renewal_info', [])
            receipt = receipt_response.get('receipt', {})
            
            # Extract Apple account identifier
            # This is unique per Apple ID and allows syncing across devices
            apple_account_id = receipt.get('original_application_version', '')
            # Alternative: Use bundle_id + original_transaction_id as stable identifier
            
            # Find the latest transaction for this product
            matching_transactions = [
                info for info in latest_receipt_info
                if info.get('product_id') == product_id
            ]
            
            if not matching_transactions:
                logger.warning(f"No matching transactions found for product_id={product_id}")
                return None
            
            # Get the latest transaction
            latest_transaction = max(
                matching_transactions,
                key=lambda x: int(x.get('expires_date_ms', 0))
            )
            
            # Get renewal info
            renewal_info = pending_renewal_info[0] if pending_renewal_info else {}
            
            # Parse dates
            expires_date_ms = int(latest_transaction.get('expires_date_ms', 0))
            purchase_date_ms = int(latest_transaction.get('purchase_date_ms', 0))
            
            expiry_date = datetime.fromtimestamp(expires_date_ms / 1000, tz=timezone.utc)
            purchase_date = datetime.fromtimestamp(purchase_date_ms / 1000, tz=timezone.utc)
            
            # Check if in trial
            is_trial = latest_transaction.get('is_trial_period', 'false') == 'true'
            is_intro_offer = latest_transaction.get('is_in_intro_offer_period', 'false') == 'true'
            
            # Auto-renew status
            auto_renew_status = renewal_info.get('auto_renew_status', '0') == '1'
            
            # Create a stable account identifier from original_transaction_id
            # This will be consistent across purchases for the same Apple account
            original_txn_id = latest_transaction.get('original_transaction_id')
            account_identifier = f"apple_{original_txn_id}" if original_txn_id else None
            
            return {
                'product_id': product_id,
                'transaction_id': latest_transaction.get('transaction_id'),
                'original_transaction_id': original_txn_id,
                'account_identifier': account_identifier,  # NEW: For user_id
                'purchase_date': purchase_date,
                'expiry_date': expiry_date,
                'is_trial_period': is_trial or is_intro_offer,
                'trial_end_date': expiry_date if (is_trial or is_intro_offer) else None,
                'auto_renew_status': auto_renew_status,
                'cancellation_date': latest_transaction.get('cancellation_date_ms'),
            }
            
        except Exception as e:
            logger.error(f"Error parsing Apple receipt: {e}", exc_info=True)
            return None
    
    def _verify_google_receipt(
        self,
        purchase_token: str,
        product_id: str,
        transaction_id: Optional[str]
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Verify Google Play receipt"""
        try:
            # TODO: Implement Google Play Developer API verification
            # This requires google-auth and google-api-python-client packages
            # For now, we'll return mock data in production if not implemented
            
            logger.warning("Google Play verification not yet fully implemented")
            
            if self.test_mode:
                return self._mock_verification(product_id, Platform.ANDROID)
            
            # Placeholder for actual implementation
            return False, {}, "Google Play verification not implemented yet"
            
        except Exception as e:
            logger.error(f"Error verifying Google receipt: {e}", exc_info=True)
            return False, {}, f"Verification error: {str(e)}"
    
    def _get_apple_error_message(self, status: int) -> str:
        """Get human-readable error message for Apple status codes"""
        error_messages = {
            21000: "The App Store could not read the JSON object you provided.",
            21002: "The data in the receipt-data property was malformed or missing.",
            21003: "The receipt could not be authenticated.",
            21004: "The shared secret you provided does not match the shared secret on file.",
            21005: "The receipt server is not currently available.",
            21006: "This receipt is valid but the subscription has expired.",
            21007: "This receipt is from the test environment, but it was sent to production.",
            21008: "This receipt is from the production environment, but it was sent to test.",
            21009: "Internal data access error.",
            21010: "The user account cannot be found or has been deleted.",
        }
        return error_messages.get(status, f"Unknown error (status={status})")
    
    def _mock_verification(
        self,
        product_id: str,
        platform: Platform
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Return mock verification data for testing"""
        logger.info(f"Generating mock verification for product_id={product_id}, platform={platform}")
        
        # Get product config
        product_config = ProductConfig.get_product_by_id(product_id)
        if not product_config:
            return False, {}, f"Unknown product_id: {product_id}"
        
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=product_config.trial_days)
        expiry = trial_end + timedelta(days=product_config.duration_days)
        
        # Generate mock account identifier based on platform
        if platform == Platform.IOS:
            account_id = f"apple_mock_{int(now.timestamp())}"
        else:
            account_id = f"google_mock_{int(now.timestamp())}"
        
        mock_data = {
            'product_id': product_id,
            'transaction_id': f'mock_txn_{now.timestamp()}',
            'original_transaction_id': f'mock_original_{now.timestamp()}',
            'account_identifier': account_id,  # NEW: For user_id
            'purchase_date': now,
            'expiry_date': expiry,
            'is_trial_period': True,
            'trial_end_date': trial_end,
            'auto_renew_status': True,
            'cancellation_date': None,
        }
        
        logger.info(f"Mock verification successful: {mock_data}")
        return True, mock_data, None
    
    def create_subscription_from_receipt(
        self,
        user_id: str,
        platform: Platform,
        receipt_data: str,
        verified_data: Dict[str, Any]
    ) -> SubscriptionRecord:
        """Create a SubscriptionRecord from verified receipt data"""
        product_id = verified_data['product_id']
        product_config = ProductConfig.get_product_by_id(product_id)
        
        now = datetime.now(timezone.utc)
        
        # Determine status
        is_trial = verified_data.get('is_trial_period', False)
        status = SubscriptionStatus.TRIAL if is_trial else SubscriptionStatus.ACTIVE
        
        subscription = SubscriptionRecord(
            user_id=user_id,
            platform=platform,
            subscription_tier=product_config.tier if product_config else SubscriptionTier.PREMIUM,
            status=status,
            product_id=product_id,
            transaction_id=verified_data.get('transaction_id'),
            original_transaction_id=verified_data.get('original_transaction_id'),
            purchase_date=verified_data.get('purchase_date', now),
            expiry_date=verified_data.get('expiry_date'),
            trial_end_date=verified_data.get('trial_end_date'),
            auto_renew_status=verified_data.get('auto_renew_status', False),
            is_trial_period=is_trial,
            receipt_data=receipt_data,
            last_verified=now,
            created_at=now,
            updated_at=now,
            chat_count_today=0,
            chat_count_reset_date=now
        )
        
        return subscription

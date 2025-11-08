"""
Subscription Service - Business logic for subscription management
Handles DynamoDB operations and subscription state management
"""
import os
import boto3
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
from ..logging_config import logger
from ..models.subscription_model import (
    SubscriptionRecord,
    SubscriptionStatus,
    SubscriptionTier,
    SubscriptionStatusResponse,
    SubscriptionFeatures,
    Platform,
    ProductConfig
)


class SubscriptionService:
    """Service for managing subscriptions in DynamoDB"""
    
    def __init__(self):
        """Initialize DynamoDB connection"""
        try:
            self.dynamodb = boto3.resource(
                service_name='dynamodb',
                region_name=os.getenv('AWS_REGION'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            self.table = self.dynamodb.Table('UserSubscriptions')
            logger.info("SubscriptionService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SubscriptionService: {e}", exc_info=True)
            raise
    
    def _convert_to_dynamodb_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert datetime objects to ISO strings and float to Decimal for DynamoDB"""
        converted = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                converted[key] = value.isoformat()
            elif isinstance(value, float):
                converted[key] = Decimal(str(value))
            elif value is None:
                # Skip None values for DynamoDB
                continue
            else:
                converted[key] = value
        return converted
    
    def _convert_from_dynamodb_format(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DynamoDB item to Python types"""
        converted = {}
        for key, value in item.items():
            if isinstance(value, Decimal):
                converted[key] = float(value) if value % 1 else int(value)
            elif isinstance(value, str):
                # Try to parse ISO datetime strings
                try:
                    if 'T' in value and ('Z' in value or '+' in value or value.endswith(':00')):
                        converted[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    else:
                        converted[key] = value
                except:
                    converted[key] = value
            else:
                converted[key] = value
        return converted
    
    def get_subscription(self, user_id: str, platform: Platform) -> Optional[SubscriptionRecord]:
        """Get subscription record for a user"""
        try:
            response = self.table.get_item(
                Key={
                    'user_id': user_id,
                    'platform': platform.value
                }
            )
            
            if 'Item' in response:
                item = self._convert_from_dynamodb_format(response['Item'])
                return SubscriptionRecord(**item)
            
            logger.info(f"No subscription found for user_id={user_id}, platform={platform}")
            return None
            
        except ClientError as e:
            logger.error(f"Error fetching subscription: {e}", exc_info=True)
            return None
    
    def create_or_update_subscription(self, subscription: SubscriptionRecord) -> bool:
        """Create or update a subscription record"""
        try:
            subscription.updated_at = datetime.now(timezone.utc)
            item = self._convert_to_dynamodb_format(subscription.dict())
            
            self.table.put_item(Item=item)
            logger.info(f"Subscription saved for user_id={subscription.user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Error saving subscription: {e}", exc_info=True)
            return False
    
    def get_subscription_status(self, user_id: str, platform: Optional[Platform] = None) -> SubscriptionStatusResponse:
        """
        Get comprehensive subscription status for a user
        If no platform specified, check both iOS and Android
        """
        try:
            # Try to get subscription for specified platform or both
            subscription = None
            
            if platform:
                subscription = self.get_subscription(user_id, platform)
            else:
                # Check iOS first, then Android
                subscription = self.get_subscription(user_id, Platform.IOS)
                if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
                    android_sub = self.get_subscription(user_id, Platform.ANDROID)
                    if android_sub and android_sub.status == SubscriptionStatus.ACTIVE:
                        subscription = android_sub
            
            # If no subscription exists, create a free tier subscription
            if not subscription:
                subscription = self._create_free_subscription(user_id, platform or Platform.IOS)
            
            # Check if subscription is still valid
            is_active = self._is_subscription_active(subscription)
            
            # Update status if expired
            if not is_active and subscription.status == SubscriptionStatus.ACTIVE:
                subscription.status = SubscriptionStatus.EXPIRED
                subscription.subscription_tier = SubscriptionTier.FREE
                self.create_or_update_subscription(subscription)
            
            # Reset daily chat count if needed
            subscription = self._reset_chat_count_if_needed(subscription)
            
            # Get features for current tier
            features = SubscriptionFeatures.get_features(subscription.subscription_tier)
            
            # Calculate remaining chats
            remaining_chats = None
            chat_limit_reached = False
            if features.daily_chat_limit is not None:
                remaining_chats = max(0, features.daily_chat_limit - subscription.chat_count_today)
                chat_limit_reached = subscription.chat_count_today >= features.daily_chat_limit
            
            return SubscriptionStatusResponse(
                user_id=user_id,
                subscription_tier=subscription.subscription_tier,
                status=subscription.status,
                is_active=is_active,
                is_trial=subscription.is_trial_period,
                expiry_date=subscription.expiry_date,
                trial_end_date=subscription.trial_end_date,
                auto_renew_status=subscription.auto_renew_status,
                features=features,
                chat_count_today=subscription.chat_count_today,
                chat_limit_reached=chat_limit_reached,
                remaining_chats=remaining_chats
            )
            
        except Exception as e:
            logger.error(f"Error getting subscription status: {e}", exc_info=True)
            # Return free tier on error
            return self._get_default_free_status(user_id)
    
    def _create_free_subscription(self, user_id: str, platform: Platform) -> SubscriptionRecord:
        """Create a new free tier subscription"""
        now = datetime.now(timezone.utc)
        subscription = SubscriptionRecord(
            user_id=user_id,
            platform=platform,
            subscription_tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            chat_count_today=0,
            chat_count_reset_date=now
        )
        self.create_or_update_subscription(subscription)
        return subscription
    
    def _is_subscription_active(self, subscription: SubscriptionRecord) -> bool:
        """Check if subscription is currently active"""
        if subscription.subscription_tier == SubscriptionTier.FREE:
            return True
        
        if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
            return False
        
        now = datetime.now(timezone.utc)
        
        # Check if in trial period
        if subscription.is_trial_period and subscription.trial_end_date:
            if now < subscription.trial_end_date:
                return True
            else:
                # Trial expired
                return False
        
        # Check expiry date
        if subscription.expiry_date:
            return now < subscription.expiry_date
        
        return False
    
    def _reset_chat_count_if_needed(self, subscription: SubscriptionRecord) -> SubscriptionRecord:
        """Reset chat count if it's a new day"""
        now = datetime.now(timezone.utc)
        
        if subscription.chat_count_reset_date:
            # Check if it's been more than 24 hours
            if (now - subscription.chat_count_reset_date).total_seconds() >= 86400:
                subscription.chat_count_today = 0
                subscription.chat_count_reset_date = now
                self.create_or_update_subscription(subscription)
        else:
            subscription.chat_count_reset_date = now
            self.create_or_update_subscription(subscription)
        
        return subscription
    
    def increment_chat_count(self, user_id: str, platform: Optional[Platform] = None) -> bool:
        """Increment daily chat count for user"""
        try:
            status = self.get_subscription_status(user_id, platform)
            
            # If unlimited, no need to track
            if status.features.unlimited_chat:
                return True
            
            # Get the actual subscription record
            sub_platform = platform or Platform.IOS
            subscription = self.get_subscription(user_id, sub_platform)
            
            if not subscription:
                subscription = self._create_free_subscription(user_id, sub_platform)
            
            subscription.chat_count_today += 1
            self.create_or_update_subscription(subscription)
            
            logger.info(f"Chat count incremented for user_id={user_id}, count={subscription.chat_count_today}")
            return True
            
        except Exception as e:
            logger.error(f"Error incrementing chat count: {e}", exc_info=True)
            return False
    
    def _get_default_free_status(self, user_id: str) -> SubscriptionStatusResponse:
        """Return default free tier status"""
        features = SubscriptionFeatures.get_features(SubscriptionTier.FREE)
        return SubscriptionStatusResponse(
            user_id=user_id,
            subscription_tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            is_active=True,
            is_trial=False,
            expiry_date=None,
            trial_end_date=None,
            auto_renew_status=False,
            features=features,
            chat_count_today=0,
            chat_limit_reached=False,
            remaining_chats=5
        )

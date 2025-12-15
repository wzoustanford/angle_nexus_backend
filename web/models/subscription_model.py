"""
Subscription Models for Angle Finance
Defines data structures for subscription management
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime, timezone
from enum import Enum


class SubscriptionTier(str, Enum):
    """Subscription tier levels"""
    FREE = "free"
    PREMIUM = "premium"


class SubscriptionStatus(str, Enum):
    """Subscription status states"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"
    TRIAL = "trial"


class Platform(str, Enum):
    """Purchase platforms"""
    IOS = "ios"
    ANDROID = "android"


class ReceiptVerificationRequest(BaseModel):
    """Request model for receipt verification"""
    user_id: str = Field(..., description="Cognito user ID")
    receipt_data: str = Field(..., description="Base64 encoded receipt (iOS) or purchase token (Android)")
    platform: Platform = Field(..., description="Purchase platform")
    product_id: str = Field(..., description="Product ID purchased")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")


class SubscriptionFeatures(BaseModel):
    """Features available per subscription tier"""
    tier: SubscriptionTier
    unlimited_chat: bool = False
    daily_chat_limit: Optional[int] = None
    advanced_search: bool = False
    full_historical_data: bool = False
    priority_support: bool = False
    
    @staticmethod
    def get_features(tier: SubscriptionTier) -> 'SubscriptionFeatures':
        """Get features for a specific tier"""
        if tier == SubscriptionTier.FREE:
            return SubscriptionFeatures(
                tier=SubscriptionTier.FREE,
                unlimited_chat=False,
                daily_chat_limit=5,
                advanced_search=False,
                full_historical_data=False,
                priority_support=False
            )
        elif tier == SubscriptionTier.PREMIUM:
            return SubscriptionFeatures(
                tier=SubscriptionTier.PREMIUM,
                unlimited_chat=True,
                daily_chat_limit=None,
                advanced_search=True,
                full_historical_data=True,
                priority_support=True
            )


class SubscriptionRecord(BaseModel):
    """Main subscription record stored in DynamoDB"""
    user_id: str = Field(..., description="Cognito user ID (Partition Key)")
    platform: Platform = Field(..., description="Platform (Sort Key)")
    subscription_tier: SubscriptionTier = Field(default=SubscriptionTier.FREE)
    status: SubscriptionStatus = Field(default=SubscriptionStatus.ACTIVE)
    
    # Purchase details
    product_id: Optional[str] = Field(None, description="com.angle.premium.monthly, etc.")
    transaction_id: Optional[str] = Field(None, description="Apple/Google transaction ID")
    original_transaction_id: Optional[str] = Field(None, description="Original transaction ID for renewals")
    
    # Dates
    purchase_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    
    # Status flags
    auto_renew_status: bool = Field(default=False)
    is_trial_period: bool = Field(default=False)
    
    # Receipt data (encrypted in production)
    receipt_data: Optional[str] = Field(None, description="Stored for re-verification")
    last_verified: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Usage tracking
    chat_count_today: int = Field(default=0)
    chat_count_reset_date: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SubscriptionStatusResponse(BaseModel):
    """Response model for subscription status queries"""
    user_id: str
    subscription_tier: SubscriptionTier
    status: SubscriptionStatus
    is_active: bool
    is_trial: bool
    expiry_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    auto_renew_status: bool
    features: SubscriptionFeatures
    
    # Usage stats
    chat_count_today: int
    chat_limit_reached: bool
    remaining_chats: Optional[int] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class VerificationResponse(BaseModel):
    """Response from receipt verification"""
    success: bool
    message: str
    subscription: Optional[SubscriptionStatusResponse] = None
    error_code: Optional[str] = None
    linked_user_id: Optional[str] = None  # Apple/Google account ID after linking


class ProductConfig(BaseModel):
    """Product configuration for easy modification"""
    product_id: str
    platform: Platform
    tier: SubscriptionTier
    duration_days: int
    trial_days: int = 7
    price_usd: float
    
    @staticmethod
    def get_all_products():
        """Returns all configured products"""
        return [
            ProductConfig(
                product_id="com.angle.premium.monthly",
                platform=Platform.IOS,
                tier=SubscriptionTier.PREMIUM,
                duration_days=30,
                trial_days=7,
                price_usd=1.99
            ),
            ProductConfig(
                product_id="com.angle.premium.annual",
                platform=Platform.IOS,
                tier=SubscriptionTier.PREMIUM,
                duration_days=365,
                trial_days=7,
                price_usd=5.99
            ),
            ProductConfig(
                product_id="angle_premium_monthly",
                platform=Platform.ANDROID,
                tier=SubscriptionTier.PREMIUM,
                duration_days=30,
                trial_days=7,
                price_usd=1.99
            ),
            ProductConfig(
                product_id="angle_premium_annual",
                platform=Platform.ANDROID,
                tier=SubscriptionTier.PREMIUM,
                duration_days=365,
                trial_days=7,
                price_usd=5.99
            ),
        ]
    
    @staticmethod
    def get_product_by_id(product_id: str) -> Optional['ProductConfig']:
        """Get product config by ID"""
        for product in ProductConfig.get_all_products():
            if product.product_id == product_id:
                return product
        return None

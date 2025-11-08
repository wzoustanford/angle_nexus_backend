#!/usr/bin/env python3
"""
Test script to verify subscription system end-to-end
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5005"
TEST_USER = f"testuser_{datetime.now().timestamp()}@example.com"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_test_mode():
    """Test 1: Verify test mode is enabled"""
    print_section("TEST 1: Verify Test Mode")
    
    url = f"{BASE_URL}/api/subscription/test_mode_status"
    response = requests.get(url)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()["test_mode"] == True
    print("✅ Test mode is enabled")

def test_default_subscription():
    """Test 2: Get default free tier subscription"""
    print_section("TEST 2: Get Default Free Tier")
    
    url = f"{BASE_URL}/api/subscription/status"
    params = {"user_id": TEST_USER}
    response = requests.get(url, params=params)
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    assert response.status_code == 200
    assert data["tier"] == "free"
    assert data["daily_chat_limit"] == 5
    assert data["chat_count"] == 0
    print("✅ Default free tier returned correctly")

def test_chat_increment():
    """Test 3: Increment chat count"""
    print_section("TEST 3: Increment Chat Count")
    
    url = f"{BASE_URL}/api/subscription/increment_chat"
    
    # Increment 5 times (free tier limit)
    for i in range(1, 6):
        response = requests.post(url, json={"user_id": TEST_USER})
        data = response.json()
        
        print(f"Chat {i}: Count={data['chat_count']}, Remaining={data['remaining_chats']}")
        
        assert response.status_code == 200
        assert data["success"] == True
        assert data["chat_count"] == i
    
    print("✅ Chat count incremented correctly")
    
    # Try to send 6th chat (should still work but remaining = -1)
    print("\nTrying 6th chat (over limit)...")
    response = requests.post(url, json={"user_id": TEST_USER})
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    print("⚠️  Note: Backend allows increment, frontend enforces limit")

def test_verify_purchase():
    """Test 4: Verify mock purchase (test mode)"""
    print_section("TEST 4: Verify Mock Purchase")
    
    url = f"{BASE_URL}/api/subscription/verify"
    payload = {
        "user_id": TEST_USER,
        "receipt_data": "mock_receipt_data_12345",
        "platform": "ios"
    }
    
    response = requests.post(url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    assert response.status_code == 200
    assert data["success"] == True
    print("✅ Purchase verified successfully (mock)")

def test_premium_status():
    """Test 5: Get premium subscription status"""
    print_section("TEST 5: Get Premium Status After Purchase")
    
    url = f"{BASE_URL}/api/subscription/status"
    params = {"user_id": TEST_USER}
    response = requests.get(url, params=params)
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    assert response.status_code == 200
    assert data["tier"] == "premium"
    assert data["daily_chat_limit"] == -1  # Unlimited
    print("✅ Premium status returned correctly")

def test_unlimited_chats():
    """Test 6: Verify unlimited chats for premium"""
    print_section("TEST 6: Test Unlimited Chats (Premium)")
    
    url = f"{BASE_URL}/api/subscription/increment_chat"
    
    # Increment 10 times (well over free limit)
    for i in range(1, 11):
        response = requests.post(url, json={"user_id": TEST_USER})
        data = response.json()
        
        if i <= 3 or i >= 8:  # Print first 3 and last 3
            print(f"Chat {i}: Count={data['chat_count']}, Remaining={data['remaining_chats']}")
        elif i == 4:
            print("...")
        
        assert response.status_code == 200
        assert data["success"] == True
    
    print("✅ Unlimited chats working for premium user")

def test_refresh_subscription():
    """Test 7: Refresh subscription status"""
    print_section("TEST 7: Refresh Subscription")
    
    url = f"{BASE_URL}/api/subscription/refresh"
    payload = {"user_id": TEST_USER}
    
    response = requests.post(url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    assert response.status_code == 200
    print("✅ Subscription refreshed successfully")

def main():
    """Run all tests"""
    print("\n" + "🚀"*30)
    print("  SUBSCRIPTION SYSTEM TEST SUITE")
    print("🚀"*30)
    print(f"\nTest User: {TEST_USER}")
    print(f"Backend URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        test_test_mode()
        test_default_subscription()
        test_chat_increment()
        test_verify_purchase()
        test_premium_status()
        test_unlimited_chats()
        test_refresh_subscription()
        
        print("\n" + "✅"*30)
        print("  ALL TESTS PASSED!")
        print("✅"*30)
        print("\n✨ Subscription system is working correctly!")
        print("\n📝 Next Steps:")
        print("   1. Test frontend integration")
        print("   2. Test daily reset (change system date)")
        print("   3. Test subscription expiry")
        print("   4. Perform end-to-end user flow testing")
        
    except AssertionError as e:
        print("\n" + "❌"*30)
        print(f"  TEST FAILED: {e}")
        print("❌"*30)
        return 1
    except requests.exceptions.ConnectionError:
        print("\n" + "❌"*30)
        print("  CONNECTION ERROR")
        print("❌"*30)
        print("\n⚠️  Make sure the backend server is running:")
        print("   cd angle_backend")
        print("   source env/bin/activate")
        print("   python web/main.py")
        return 1
    except Exception as e:
        print("\n" + "❌"*30)
        print(f"  UNEXPECTED ERROR: {e}")
        print("❌"*30)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

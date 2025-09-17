#!/usr/bin/env python3
"""
Test the full Gmail monitoring and Slack posting application
"""

import sys
import os
from app import GmailSlackMonitor

def test_gmail_access():
    """Test Gmail API access"""
    print("🔍 Testing Gmail API access...")
    try:
        monitor = GmailSlackMonitor()
        if not monitor.gmail_service:
            print("❌ Gmail service not initialized")
            return False
        
        # Test Gmail API call
        results = monitor.gmail_service.users().messages().list(
            userId='me', 
            q='from:noreply@forthcrm.com newer_than:7d', 
            maxResults=5
        ).execute()
        
        message_count = len(results.get('messages', []))
        print(f"✅ Gmail API working! Found {message_count} messages from Forth CRM")
        return True
        
    except Exception as e:
        print(f"❌ Gmail API error: {e}")
        return False

def test_slack_webhook():
    """Test Slack webhook"""
    print("\n🔍 Testing Slack webhook...")
    try:
        monitor = GmailSlackMonitor()
        test_message = {
            "text": "🧪 Test message from Gmail Monitor",
            "channel": "#forth-alerts",
            "username": "Gmail Monitor"
        }
        
        response = monitor.send_slack_message(test_message)
        if response.status_code == 200:
            print("✅ Slack webhook working!")
            return True
        else:
            print(f"❌ Slack webhook failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Slack webhook error: {e}")
        return False

def test_full_monitoring():
    """Test the full monitoring process"""
    print("\n🔍 Testing full monitoring process...")
    try:
        monitor = GmailSlackMonitor()
        
        # Run one polling cycle
        print("Running one polling cycle...")
        monitor.poll_gmail()
        print("✅ Monitoring cycle completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Monitoring error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Full Gmail-Slack Monitoring Application")
    print("=" * 50)
    
    # Test Gmail access
    gmail_ok = test_gmail_access()
    
    # Test Slack webhook
    slack_ok = test_slack_webhook()
    
    # Test full monitoring
    monitoring_ok = test_full_monitoring()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"Gmail API: {'✅ PASS' if gmail_ok else '❌ FAIL'}")
    print(f"Slack Webhook: {'✅ PASS' if slack_ok else '❌ FAIL'}")
    print(f"Full Monitoring: {'✅ PASS' if monitoring_ok else '❌ FAIL'}")
    
    if gmail_ok and slack_ok and monitoring_ok:
        print("\n🎉 ALL TESTS PASSED! Application is ready for deployment!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

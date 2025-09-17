#!/usr/bin/env python3
"""
Gmail to Slack Monitor
Polls Gmail inbox using search query and posts matching messages to Slack via webhook.
Supports three modes: server (Flask health check), worker (polling loop), and combined (both).
"""

import os
import sqlite3
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import json
import base64
import email
from email.mime.text import MIMEText

import pytz
from flask import Flask, jsonify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailSlackMonitor:
    def __init__(self):
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.slack_channel = os.getenv('SLACK_CHANNEL', '#alerts')
        self.slack_username = os.getenv('SLACK_USERNAME', 'Gmail Monitor')
        self.gmail_query = os.getenv('GMAIL_QUERY', 'label:inbox is:unread newer_than:7d')
        self.poll_interval = int(os.getenv('POLL_INTERVAL_SECONDS', '60'))
        self.timezone = os.getenv('TIMEZONE', 'UTC')
        self.return_full_body = os.getenv('RETURN_FULL_BODY', 'false').lower() == 'true'
        self.mode = os.getenv('MODE', 'server')
        
        # Initialize timezone
        try:
            self.tz = pytz.timezone(self.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"Unknown timezone {self.timezone}, falling back to UTC")
            self.tz = pytz.UTC
            
        # Initialize database
        self.init_database()
        
        # Initialize Gmail service
        self.gmail_service = None
        self.init_gmail_service()

    def init_database(self):
        """Initialize SQLite database for deduplication."""
        try:
            conn = sqlite3.connect('state.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed (
                    id TEXT PRIMARY KEY,
                    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def init_gmail_service(self):
        """Initialize Gmail API service with OAuth authentication."""
        try:
            creds = None
            
            # Try to load from environment variables first (for Render deployment)
            if self._load_credentials_from_env():
                logger.info("Loading OAuth credentials from environment variables")
                creds = self._get_credentials_from_env()
            else:
                # Fallback to file-based credentials (for local development)
                logger.info("Loading OAuth credentials from files")
                creds = self._load_credentials_from_file()
            
            # If no valid credentials, run OAuth flow (local only)
            if not creds or not creds.valid:
                # Only run OAuth flow in local development
                if os.getenv('RENDER') or os.getenv('DYNO'):
                    logger.error("OAuth credentials are invalid or expired. Please check your environment variables:")
                    logger.error("- GOOGLE_CLIENT_ID: Check if it's correct")
                    logger.error("- GOOGLE_CLIENT_SECRET: Check if it's correct") 
                    logger.error("- GOOGLE_REFRESH_TOKEN: May be expired, regenerate it")
                    logger.error("To fix: Run the OAuth setup locally to get fresh credentials")
                    raise Exception("OAuth credentials are invalid or expired. Please regenerate them.")
                
                logger.info("Starting OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                
                # Save credentials for next run (local only)
                if not os.getenv('RENDER') and not os.getenv('DYNO'):
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
                    logger.info("Credentials saved to token.json")
            
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            raise

    def _load_credentials_from_env(self):
        """Check if OAuth credentials are available in environment variables."""
        required_vars = [
            'GOOGLE_CLIENT_ID',
            'GOOGLE_CLIENT_SECRET',
            'GOOGLE_REFRESH_TOKEN'
        ]
        has_all_vars = all(os.getenv(var) for var in required_vars)
        logger.info(f"Environment variables check: {has_all_vars}")
        for var in required_vars:
            value = os.getenv(var)
            logger.info(f"{var}: {'SET' if value else 'NOT SET'}")
        return has_all_vars

    def _get_credentials_from_env(self):
        """Load OAuth credentials from environment variables."""
        try:
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
            refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
            
            # Create credentials from environment variables
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES
            )
            
            # Refresh the credentials to get a valid access token
            logger.info("Refreshing credentials from environment variables")
            creds.refresh(Request())
            logger.info("Credentials refreshed successfully from environment variables")
            
            return creds
            
        except Exception as e:
            logger.error(f"Failed to load credentials from environment: {e}")
            return None

    def _load_credentials_from_file(self):
        """Load OAuth credentials from file (local development)."""
        try:
            token_file = 'token.json'
            
            # Load existing token
            if os.path.exists(token_file):
                return Credentials.from_authorized_user_file(token_file, SCOPES)
            
            # Check for credentials.json
            if not os.path.exists('credentials.json'):
                logger.error("credentials.json not found. Please download from Google Cloud Console.")
                return None
                
            return None  # Will trigger OAuth flow
            
        except Exception as e:
            logger.error(f"Failed to load credentials from file: {e}")
            return None

    def is_message_processed(self, message_id: str) -> bool:
        """Check if message has already been processed."""
        try:
            conn = sqlite3.connect('state.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM processed WHERE id = ?', (message_id,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking processed message: {e}")
            return False

    def mark_message_processed(self, message_id: str):
        """Mark message as processed."""
        try:
            conn = sqlite3.connect('state.db')
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO processed (id) VALUES (?)', (message_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error marking message as processed: {e}")

    def get_message_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get full message details from Gmail API."""
        try:
            message = self.gmail_service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            header_dict = {h['name'].lower(): h['value'] for h in headers}
            
            # Extract basic info
            subject = header_dict.get('subject', 'No Subject')
            sender = header_dict.get('from', 'Unknown Sender')
            date_str = header_dict.get('date', '')
            
            # Parse date
            try:
                if date_str:
                    # Parse email date format
                    email_date = email.utils.parsedate_to_datetime(date_str)
                    if email_date.tzinfo is None:
                        email_date = email_date.replace(tzinfo=timezone.utc)
                    local_date = email_date.astimezone(self.tz)
                    formatted_date = local_date.strftime('%Y-%m-%d %H:%M:%S %Z')
                else:
                    formatted_date = 'Unknown Date'
            except Exception:
                formatted_date = date_str or 'Unknown Date'
            
            # Extract body
            body = self.extract_message_body(message['payload'])
            if not self.return_full_body and len(body) > 200:
                body = body[:200] + "..."
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': formatted_date,
                'body': body,
                'thread_id': message.get('threadId', ''),
                'snippet': message.get('snippet', '')
            }
            
        except HttpError as e:
            logger.error(f"Gmail API error for message {message_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting message details for {message_id}: {e}")
            return None

    def extract_message_body(self, payload: Dict[str, Any]) -> str:
        """Extract text body from email payload."""
        body = ""
        
        def extract_from_part(part):
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    try:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
                    except Exception:
                        return ""
            elif part.get('mimeType') == 'text/html':
                data = part.get('body', {}).get('data', '')
                if data:
                    try:
                        html = base64.urlsafe_b64decode(data).decode('utf-8')
                        # Simple HTML to text conversion
                        import re
                        text = re.sub(r'<[^>]+>', '', html)
                        return text
                    except Exception:
                        return ""
            elif 'parts' in part:
                for subpart in part['parts']:
                    result = extract_from_part(subpart)
                    if result:
                        return result
            return ""
        
        if payload.get('mimeType') == 'text/plain':
            data = payload.get('body', {}).get('data', '')
            if data:
                try:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
                except Exception:
                    pass
        
        if 'parts' in payload:
            for part in payload['parts']:
                result = extract_from_part(part)
                if result:
                    body = result
                    break
        
        return body or payload.get('snippet', '')

    def post_to_slack(self, message_data: Dict[str, Any]) -> bool:
        """Post message to Slack via webhook."""
        try:
            # Create Gmail link
            gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{message_data['thread_id']}"
            
            # Format message
            text = f"📧 New Email: {message_data['subject']}"
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📧 {message_data['subject']}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*From:*\n{message_data['sender']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Date:*\n{message_data['date']}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Query:* `{self.gmail_query}`"
                    }
                }
            ]
            
            # Add body preview
            if message_data['body']:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Preview:*\n```{message_data['body']}```"
                    }
                })
            
            # Add Gmail button
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Open in Gmail"
                        },
                        "url": gmail_link,
                        "action_id": "open_gmail"
                    }
                ]
            })
            
            payload = {
                "channel": self.slack_channel,
                "username": self.slack_username,
                "text": text,
                "blocks": blocks
            }
            
            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully posted message {message_data['id']} to Slack")
                return True
            else:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error posting to Slack: {e}")
            return False

    def poll_gmail(self):
        """Poll Gmail for new messages matching the query."""
        try:
            logger.info(f"Polling Gmail with query: {self.gmail_query}")
            
            # Search for messages
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=self.gmail_query,
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} messages")
            
            new_messages = 0
            for message in messages:
                message_id = message['id']
                
                # Skip if already processed
                if self.is_message_processed(message_id):
                    continue
                
                # Get full message details
                message_data = self.get_message_details(message_id)
                if not message_data:
                        continue

                # Post to Slack
                if self.post_to_slack(message_data):
                    self.mark_message_processed(message_id)
                    new_messages += 1
                    logger.info(f"Processed new message: {message_data['subject']}")
                else:
                    logger.error(f"Failed to post message {message_id} to Slack")
            
            logger.info(f"Polling complete. Processed {new_messages} new messages")
            
        except HttpError as e:
            logger.error(f"Gmail API error during polling: {e}")
        except Exception as e:
            logger.error(f"Error during polling: {e}")

    def run_worker(self):
        """Run the polling worker loop."""
        logger.info(f"Starting Gmail polling worker (interval: {self.poll_interval}s)")
        
        while True:
            try:
                self.poll_gmail()
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                logger.info("Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                logger.info(f"Retrying in {self.poll_interval} seconds...")
                time.sleep(self.poll_interval)

# Flask app for health checks
app = Flask(__name__)

@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        # Get timezone from environment
        timezone_str = os.getenv('TIMEZONE', 'UTC')
        try:
            tz = pytz.timezone(timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            tz = pytz.UTC
            
        current_time = datetime.now(tz).isoformat()
        return jsonify({
            'ok': True,
            'time': current_time,
            'timezone': str(tz),
            'mode': os.getenv('MODE', 'server')
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500

def main():
    """Main entry point."""
    monitor = GmailSlackMonitor()
    
    if monitor.mode == 'worker':
        logger.info("Starting in worker mode")
        monitor.run_worker()
    elif monitor.mode == 'server':
        logger.info("Starting in server mode")
        port = int(os.getenv('PORT', '10000'))
        from waitress import serve
        serve(app, host='0.0.0.0', port=port)
    else:
        # Combined mode: run both health server and worker
        logger.info("Starting in combined mode (server + worker)")
        
        import threading
        import time
        
        # Start the worker in a separate thread
        def run_worker():
            time.sleep(5)  # Wait for server to start
            monitor.run_worker()
        
        worker_thread = threading.Thread(target=run_worker, daemon=True)
        worker_thread.start()
        
        # Start the Flask server
        port = int(os.getenv('PORT', '10000'))
        from waitress import serve
        serve(app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()

# Deployment Guide for Gmail to Slack Monitor

This guide explains how to deploy the Gmail to Slack notification service for monitoring emails sent to `reporting@deudaslibres.com`.

## Overview

The application monitors Gmail for emails sent to `reporting@deudaslibres.com` with cancellation-related keywords and posts notifications to Slack.

## Configuration

### Environment Variables Required

Set these environment variables in your deployment platform (Render, Heroku, etc.):

```env
# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR_WEBHOOK_URL
SLACK_CHANNEL=forth-alerts
SLACK_USERNAME=Gmail Monitor

# Gmail Configuration
GMAIL_QUERY=to:reporting@deudaslibres.com (subject:"Cancellation" OR subject:"Cancel" OR subject:"cancelled" OR subject:"cancelled") newer_than:7d

# Google Service Account Credentials
GOOGLE_SERVICE_ACCOUNT_EMAIL=dl-gmail-monitor@master-cpa-data.iam.gserviceaccount.com
GOOGLE_DELEGATED_EMAIL=reporting@deudaslibres.com
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----"
GOOGLE_PROJECT_ID=master-cpa-data
GOOGLE_PRIVATE_KEY_ID=514997f2a94de2c7dd5ff3b6c92619b9e42d6a2e
GOOGLE_CLIENT_ID=102450806791203838038

# Polling Configuration
POLL_INTERVAL_SECONDS=60
TIMEZONE=Asia/Manila
RETURN_FULL_BODY=true
MODE=combined
PORT=10000
```

## Deployment Steps

### 1. Render Deployment

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set the environment variables listed above
4. Deploy the application

### 2. Required Setup

- Domain-wide delegation must be configured for `deudaslibres.com`
- Gmail API must be enabled in the Google Cloud project
- Service account must have proper permissions

## Features

- Monitors Gmail for cancellation-related emails
- Sends formatted notifications to Slack
- Prevents duplicate notifications using database tracking
- Health check endpoint available at `/health`
- Automatic polling every 60 seconds

## Testing

Run the test script locally to verify configuration:

```bash
python test_new_configuration.py
```

## Security Notes

- Never commit sensitive credentials to version control
- Use environment variables for all sensitive data
- Regularly rotate service account keys
- Monitor API usage and access logs

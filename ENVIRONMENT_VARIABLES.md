# Environment Variables Documentation

This document lists all required environment variables for the Gmail to Slack notification service.

## Required Environment Variables

### Slack Configuration
| Variable | Description | Example |
|----------|-------------|---------|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL | `https://hooks.slack.com/services/T.../B.../...` |
| `SLACK_CHANNEL` | Target Slack channel (with #) | `#alerts` |
| `SLACK_USERNAME` | Bot username in Slack | `Gmail Monitor` |

### Gmail Configuration
| Variable | Description | Example |
|----------|-------------|---------|
| `GMAIL_QUERY` | Gmail search query | `to:email@domain.com (subject:"Alert") after:2025/09/01` |

### Google Service Account Credentials
| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_SERVICE_ACCOUNT_EMAIL` | Service account email | `bot@project.iam.gserviceaccount.com` |
| `GOOGLE_DELEGATED_EMAIL` | Email to impersonate | `monitoring@company.com` |
| `GOOGLE_PRIVATE_KEY` | Service account private key | `-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----` |
| `GOOGLE_PROJECT_ID` | Google Cloud project ID | `my-project-123` |
| `GOOGLE_PRIVATE_KEY_ID` | Private key ID | `abc123def456...` |
| `GOOGLE_CLIENT_ID` | OAuth client ID | `123456789.apps.googleusercontent.com` |

### Application Configuration
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `POLL_INTERVAL_SECONDS` | Polling interval in seconds | `60` | `60` |
| `TIMEZONE` | Timezone for timestamps | `UTC` | `America/New_York` |
| `RETURN_FULL_BODY` | Include full email body | `true` | `true` |
| `MODE` | Application mode | `combined` | `server`, `worker`, `combined` |
| `PORT` | Server port | `10000` | `10000` |

## Setup Instructions

### 1. Copy the template
```bash
cp config.env.example config.env
```

### 2. Fill in your values
Edit `config.env` with your actual values:

```env
# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK/URL
SLACK_CHANNEL=#your-channel
SLACK_USERNAME=Gmail Monitor

# Gmail Configuration  
GMAIL_QUERY=to:your-email@domain.com (subject:"Alert") after:2025/09/01

# Google Service Account (get from Google Cloud Console)
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GOOGLE_DELEGATED_EMAIL=your-email@domain.com
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----"
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_PRIVATE_KEY_ID=your-key-id
GOOGLE_CLIENT_ID=your-client-id
```

### 3. For Render.com Deployment
Set these as environment variables in your Render service dashboard instead of using `config.env`.

## Security Notes

- **Never commit `config.env`** to version control
- Use environment variables in production
- Keep service account credentials secure
- Rotate credentials regularly

## Gmail Query Examples

### Basic Query
```env
GMAIL_QUERY=to:alerts@company.com is:unread
```

### Subject-based Query
```env
GMAIL_QUERY=to:alerts@company.com subject:"URGENT" is:unread
```

### Date Range Query
```env
GMAIL_QUERY=to:alerts@company.com after:2025/09/01 before:2025/12/31
```

### Multiple Subject Query
```env
GMAIL_QUERY=to:alerts@company.com (subject:"Alert" OR subject:"Warning" OR subject:"Error") after:2025/09/01
```

## Timezone Options

Common timezone values:
- `America/New_York` (Eastern Time)
- `America/Chicago` (Central Time)
- `America/Denver` (Mountain Time)
- `America/Los_Angeles` (Pacific Time)
- `UTC` (Coordinated Universal Time)
- `Europe/London` (GMT/BST)
- `Asia/Tokyo` (JST)

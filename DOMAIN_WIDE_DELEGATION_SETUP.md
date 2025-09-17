# 🔐 Domain-Wide Delegation Setup for Gmail API

This guide will help you set up Domain-Wide Delegation so your Service Account can access Gmail on behalf of users in your Google Workspace domain.

## 📋 Prerequisites

- Google Workspace Admin access
- Google Cloud Console access
- Service Account already created

## 🚀 Step-by-Step Setup

### Step 1: Enable Domain-Wide Delegation in Google Cloud Console

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Select your project**: `forth-to-slack`
3. **Navigate to**: **IAM & Admin** → **Service Accounts**
4. **Find your service account**: `forth-to-slack-monitoring@forth-to-slack.iam.gserviceaccount.com`
5. **Click on the service account** → **Details** tab
6. **Click "Show domain-wide delegation"** → **Enable Google Workspace Domain-wide Delegation**
7. **Note the "Client ID"** (this is different from the OAuth client ID)
   - Example: `123456789012345678901`

### Step 2: Configure Domain-Wide Delegation in Google Workspace Admin

1. **Go to [Google Workspace Admin Console](https://admin.google.com/)**
2. **Navigate to**: **Security** → **API Controls**
3. **Click "Domain-wide delegation"**
4. **Click "Add new"**
5. **Enter the Client ID** from Step 1
6. **Add OAuth scopes**: 
   ```
   https://www.googleapis.com/auth/gmail.readonly
   ```
7. **Click "Authorize"**

### Step 3: Update Environment Variables

Add this environment variable to your Render.com deployment:

```env
GOOGLE_DELEGATED_EMAIL=your-email@yourdomain.com
```

**Important**: Replace `your-email@yourdomain.com` with the actual Gmail address you want to monitor.

### Step 4: Test the Setup

1. **Deploy to Render.com** with the updated environment variables
2. **Check the logs** - you should see:
   ```
   Service Account credentials with delegation loaded for your-email@yourdomain.com
   ```
3. **Test the health endpoint**: `https://your-app.onrender.com/health`

## 🔍 Troubleshooting

### Common Issues

**"Precondition check failed"**
- ✅ Ensure Domain-Wide Delegation is properly configured
- ✅ Verify the Client ID matches exactly
- ✅ Check that the OAuth scope is correct

**"Invalid delegated email"**
- ✅ Ensure the email exists in your Google Workspace domain
- ✅ Verify the email format is correct

**"Insufficient permissions"**
- ✅ Ensure the Service Account has the Gmail API enabled
- ✅ Verify Domain-Wide Delegation is authorized

### Verification Steps

1. **Check Service Account Client ID**:
   - Go to Google Cloud Console → IAM & Admin → Service Accounts
   - Click on your service account
   - Note the "Client ID" (not the OAuth client ID)

2. **Verify Domain-Wide Delegation**:
   - Go to Google Workspace Admin → Security → API Controls → Domain-wide delegation
   - Ensure your Client ID is listed with the correct scope

3. **Test Gmail Access**:
   - The app should now be able to access Gmail without the "Precondition check failed" error

## 📝 Environment Variables Summary

```env
# Existing Service Account variables
GOOGLE_SERVICE_ACCOUNT_EMAIL=forth-to-slack-monitoring@forth-to-slack.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----...
GOOGLE_PROJECT_ID=forth-to-slack
GOOGLE_PRIVATE_KEY_ID=90c6139b1f901807f62b169ac879a3358d831d65
GOOGLE_CLIENT_ID=115899325751750890099

# NEW: Delegated email (the Gmail account to monitor)
GOOGLE_DELEGATED_EMAIL=your-email@yourdomain.com
```

## ✅ Success Indicators

- ✅ Service Account credentials load successfully
- ✅ Delegation is applied to the specified email
- ✅ Gmail API calls work without "Precondition check failed" errors
- ✅ Health endpoint shows `"gmail_service": "connected"`

## 🆘 Need Help?

If you encounter issues:

1. **Check the logs** in Render.com dashboard
2. **Verify all environment variables** are set correctly
3. **Ensure Domain-Wide Delegation** is properly configured
4. **Test with a simple Gmail query** first

The key is that Domain-Wide Delegation allows your Service Account to impersonate users in your Google Workspace domain, which is required for Gmail API access.

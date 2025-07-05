 # Pill Reminder App

A Python application that sends daily pill reminders via WhatsApp using Green API. The app sends reminders at 8:00 PM Israel time and processes incoming messages from the recipient.

## Features

- ⏰ **Daily Reminders**: Automatically sends pill reminders at 8:00 PM Israel time
- 💬 **Message Processing**: Handles incoming messages and responds appropriately
- 🤖 **AI-Powered Responses**: Optional OpenAI integration for intelligent message processing
- 🎭 **AI Reminder Messages**: Personalized Hebrew reminders with humor and sarcasm
- 📊 **Message History**: Tracks all interactions and provides statistics
- 🗄️ **Database Storage**: SQLite database with Railway persistent volumes
- 🚀 **Auto-Start**: Automatically starts when deployed (no manual intervention needed)
- 🌍 **Timezone Support**: Properly handles Israel timezone
- 🔧 **Easy Configuration**: Simple environment-based configuration

## Prerequisites

1. **Green API Account**: Sign up at [green-api.com](https://green-api.com/)
2. **WhatsApp Instance**: Create a WhatsApp instance in your Green API dashboard
3. **Python 3.7+**: Make sure you have Python installed

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   - Copy `env_example.txt` to `.env`
   - Fill in your Green API credentials and recipient phone number

   ```bash
   # On Windows
   copy env_example.txt .env
   
   # On Linux/Mac
   cp env_example.txt .env
   ```

4. **Edit `.env` file**:
   ```
   GREEN_API_TOKEN=your_green_api_token_here
   GREEN_API_INSTANCE_ID=your_instance_id_here
   RECIPIENT_PHONE=972501234567
   ```

## Configuration

### Green API Setup

1. Go to [green-api.com](https://green-api.com/) and create an account
2. Create a new WhatsApp instance
3. Get your API credentials from the dashboard
4. Make sure your WhatsApp instance is authorized and connected

### Phone Number Format

- Use country code without the `+` symbol
- Example: `972501234567` for an Israeli number
- Make sure the number is registered on WhatsApp

### Webhook Setup (Optional but Recommended)

Webhooks provide real-time notifications instead of polling the API every 5 seconds. This is more efficient and provides faster response times.

#### Option 1: Using a Public Domain

1. **Deploy your app to a public server** (Railway, Heroku, DigitalOcean, etc.)
2. **Set environment variables**:
   ```
   WEBHOOK_ENABLED=true
   WEBHOOK_URL=https://your-domain.com
   WEBHOOK_TOKEN=your_secret_token_here
   ```
3. **The app will automatically set up the webhook** when it starts

#### Option 2: Using ngrok for Local Development

1. **Install ngrok**: Download from [ngrok.com](https://ngrok.com/)
2. **Start your Flask app**:
   ```bash
   python app.py
   ```
3. **Start ngrok** in a new terminal:
   ```bash
   ngrok http 5000
   ```
4. **Copy the ngrok URL** (e.g., `https://abc123.ngrok.io`)
5. **Set environment variables**:
   ```
   WEBHOOK_ENABLED=true
   WEBHOOK_URL=https://abc123.ngrok.io
   WEBHOOK_TOKEN=your_secret_token_here
   ```
6. **Restart your app**

#### Webhook Management

The app provides several endpoints for managing webhooks:

- **Check webhook status**: `GET /api/webhook/status`
- **Set up webhook**: `POST /api/webhook/setup`
- **Disable webhook**: `POST /api/webhook/disable`

#### Testing Webhooks

Use the included test script to verify your webhook is working:

```bash
python test_webhook.py https://your-domain.com/webhook
```

This will send test notifications to your webhook endpoint.

#### Webhook vs Polling

| Feature | Webhooks | Polling |
|---------|----------|---------|
| **Response Time** | Real-time | Up to 5 seconds |
| **Efficiency** | High | Lower |
| **Setup** | Requires public URL | Simple |
| **Reliability** | Depends on network | More reliable |
| **Cost** | Lower API usage | Higher API usage |

**Recommendation**: Use webhooks for production deployments, polling for development/testing.

### AI-Powered Message Processing (Optional)

The app supports OpenAI integration for intelligent message processing. When enabled, the AI can:

- **Understand natural language**: Respond to messages like "I took my medicine" or "I forgot today"
- **Provide personalized responses**: Give encouraging and supportive messages
- **Handle complex queries**: Answer questions about medication management
- **Multi-language support**: Respond in the same language as the user's message

#### Setup AI Processing

1. **Get an OpenAI API key**:
   - Sign up at [platform.openai.com](https://platform.openai.com/)
   - Create an API key in your account settings

2. **Configure environment variables**:
   ```
   OPENAI_ENABLED=true
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-3.5-turbo
   ```

3. **Restart your app**

#### AI vs Template Responses

| Feature | AI Processing | Template Responses |
|---------|---------------|-------------------|
| **Intelligence** | High - understands context | Basic - keyword matching |
| **Personalization** | High - varied responses | Low - fixed templates |
| **Language Support** | Multi-language | English only |
| **Cost** | API usage fees | Free |
| **Reliability** | Depends on OpenAI | Always available |
| **Setup** | Requires API key | No setup needed |

**Recommendation**: Use AI for production with fallback to templates, or templates for development/testing.

#### AI Response Examples

**User**: "לקחתי את הגלולה"
**AI**: "מעולה! את שומרת על עצמך. המשכי ככה! 💪"

**User**: "שכחתי לקחת אתמול"
**AI**: "אל דאגה! קחי אותה בהקדם האפשרי. הבריאות שלך חשובה! אל תתעצבי - כולנו שוכחות לפעמים! 🏥"

**User**: "באיזו שעה אני צריכה לקחת?"
**AI**: "התזכורת היומית שלך מוגדרת ל-8:00 בערב. נסי לקחת בערך באותה שעה לעקביות! ⏰"

### AI Reminder Messages

The app generates **personalized Hebrew reminder messages** using AI for birth control pills:

- **🎭 Funny & Sarcastic**: Messages have humor and sarcasm (not formal)
- **👩 Female-Targeted**: Specifically designed for female recipients
- **🇮🇱 Hebrew Language**: All messages are in Hebrew
- **😊 Emoji-Rich**: Uses appropriate emojis for engagement
- **🔄 Daily Variety**: Different messages each day (not repetitive)
- **💊 Birth Control Specific**: Uses Hebrew terms כדור/גלולה

#### Example AI Reminders:
- "היי יפה! 🕗 8:00 - זמן לכדור! אל תשכחי שאת לא רוצה להיות בהריון 😅💊"
- "טאק טאק! 🚪 מי שם? הגלולה שלך! היא מחכה כבר 5 דקות... ⏰💊"
- "היי! 🎯 זוכרת מה צריך לעשות עכשיו? כן, בדיוק - הכדור! 💊✨"

#### Setup AI Reminders:
1. **Enable OpenAI**: Set `OPENAI_ENABLED=true` and add your API key
2. **Automatic**: AI reminders are automatically enabled when OpenAI is available
3. **Test**: Use "Test AI Reminder" button in the web interface

## Railway Deployment Options

The app supports two deployment approaches on Railway:

### Option 1: Single Service with Railway Cron (Recommended)

**Advantages:**
- ✅ Simple setup
- ✅ Shared database
- ✅ Lower cost
- ✅ Railway-managed scheduling

**Setup:**
1. Deploy your app to Railway using `railway.json`
2. In Railway dashboard → Settings → Cron Jobs
3. Add: Schedule `0 17 * * *` (5 PM UTC = 8 PM Israel)
4. Command: `curl -X POST https://your-app-url.railway.app/api/send-reminder`

### Option 2: Two Services with Shared Database (Advanced)

**Advantages:**
- ✅ Service separation
- ✅ Independent scaling
- ✅ Better resource isolation
- ✅ Shared database via HTTP API

**Setup:**
1. **Deploy Main App Service:**
   - Use `railway.json` configuration (default)
   - This handles web interface and message processing
   - Contains the shared database

2. **Deploy Reminder Service:**
   - Use same `railway.json` but with `SERVICE_TYPE=reminder` environment variable
   - This tells Railway to run `reminder_service.py` instead of the main app
   - Communicates with main app via HTTP API

3. **Configure Environment Variables:**
   - In the reminder service, set `SERVICE_TYPE=reminder` and `MAIN_APP_URL=https://your-main-app-url.railway.app`
   - Copy all other environment variables to both services

4. **Set up Railway Cron for Reminder Service:**
   - Schedule: `0 17 * * *` (5 PM UTC = 8 PM Israel)
   - Command: `python reminder_service.py`

### Testing the Setup

1. **Test main app endpoints:**
   ```bash
   curl -X POST https://your-main-app-url.railway.app/api/send-reminder
   curl https://your-main-app-url.railway.app/cron-test
   ```

2. **Test reminder service API calls:**
   ```bash
   curl https://your-main-app-url.railway.app/api/reminders/last-date
   ```

### Service Comparison

| Feature | Single Service | Two Services |
|---------|----------------|--------------|
| **Database** | Shared | Shared via API |
| **Complexity** | Simple | More complex |
| **Resource Usage** | Lower | Higher |
| **Scalability** | Limited | Better |
| **Cost** | Lower | Higher |
| **Reliability** | High | High |
| **Maintenance** | Easy | Moderate |

**Recommendation**: Start with single service, upgrade to two services if needed for scaling.

The app uses **Railway's built-in cron jobs** for reliable reminder scheduling:

### How It Works

- **Automatic Scheduling**: Railway runs the reminder service daily at 8:00 PM Israel time (5:00 PM UTC)
- **Missed Reminder Handling**: Automatically detects and sends missed reminders if the service was down
- **Resource Efficient**: No background scheduler running 24/7
- **Reliable**: Railway's infrastructure handles timing and execution

### Cron Configuration

```json
{
  "cron": "0 17 * * *"  // Daily at 5:00 PM UTC (8:00 PM Israel time)
}
```

### Manual Testing

- **Send Reminder Now**: Test the reminder system immediately
- **Check Missed Reminders**: Check for and send any missed reminders
- **Test AI Reminder**: Test AI message generation without sending

## Data Storage

The app uses **SQLite database** with Railway persistent volumes for reliable data storage:

### Database Features

- **Persistent Storage**: Data survives app restarts and deployments
- **Automatic Cleanup**: Old messages are automatically cleaned up after 90 days
- **Statistics**: Built-in statistics and analytics
- **Backup Support**: Easy backup and restore functionality

### Database Tables

- **messages**: Stores all incoming and outgoing messages
- **reminders**: Tracks scheduled and sent reminders
- **statistics**: Cached statistics for performance

### Database Management

The app provides several API endpoints for database management:

- **View statistics**: `GET /api/database/stats`
- **Clean up old messages**: `POST /api/database/cleanup`

### Migration from File Storage

If you're upgrading from the previous file-based storage:

```bash
python migrate_to_db.py
```

This will migrate your existing `message_history.json` file to the database.

## Usage

### Automatic Startup

The app **automatically starts** when deployed to Railway or when the module is loaded. No manual intervention is required!

- ✅ **Message processing** starts automatically
- ✅ **Railway cron jobs** handle reminder scheduling automatically
- ✅ **Database** is initialized automatically
- ✅ **Webhooks** are configured automatically (if enabled)

### Manual Control

You can still manually control the app through the web interface:

- **Start/Restart**: Manually start or restart the app
- **Stop**: Stop the app temporarily
- **Send Reminder Now**: Send a reminder immediately
- **Check Missed Reminders**: Check and send any missed reminders
- **Test AI Reminder**: Test AI message generation
- **Database Management**: View stats and cleanup old messages

### Local Development

For local development, you can still run:

```bash
python app.py
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Network Connection Errors

**Error**: `HTTPConnectionPool(host='localhost', port=5000): Max retries exceeded`

**Cause**: The reminder service is trying to connect to `localhost:5000` but the main app isn't running there.

**Solution**:
1. **Check MAIN_APP_URL environment variable**:
   ```bash
   echo $MAIN_APP_URL
   ```
   It should be set to your main app's public URL (e.g., `https://your-app.railway.app`)

2. **Set the correct URL**:
   ```bash
   export MAIN_APP_URL=https://your-main-app-url.railway.app
   ```

3. **Test the connection**:
   ```bash
   python test_connection.py
   ```

#### 2. Datetime Timezone Errors

**Error**: `can't subtract offset-naive and offset-aware datetimes`

**Cause**: The app is trying to compare datetime objects with different timezone information.

**Solution**: This has been fixed in the latest version. The app now properly handles timezone-aware datetime objects.

#### 3. Reminder Service Not Sending Reminders

**Symptoms**: No reminders are being sent, or reminders are sent at wrong times.

**Debugging Steps**:
1. **Check Railway cron job**:
   - Go to Railway dashboard → Your reminder service → Settings → Cron Jobs
   - Verify the cron job is configured: `0 17 * * *` (5 PM UTC = 8 PM Israel)
   - Test with "Run Now" button

2. **Check environment variables**:
   ```bash
   # In Railway dashboard, verify these are set:
   MAIN_APP_URL=https://your-main-app-url.railway.app
   SERVICE_TYPE=reminder
   GREEN_API_TOKEN=your_token
   GREEN_API_INSTANCE_ID=your_instance_id
   RECIPIENT_PHONE=your_phone_number
   ```

3. **Test reminder service manually**:
   ```bash
   python reminder_service.py
   ```

4. **Check logs**:
   - Look for connection errors
   - Verify Green API is working
   - Check if main app is accessible

#### 4. Main App Not Responding

**Symptoms**: Web interface not loading, API endpoints returning errors.

**Debugging Steps**:
1. **Check if main app is running**:
   ```bash
   curl https://your-main-app-url.railway.app/health
   ```

2. **Check Railway deployment**:
   - Go to Railway dashboard → Your main app service
   - Verify deployment status is "Deployed"
   - Check logs for startup errors

3. **Test main app endpoints**:
   ```bash
   curl https://your-main-app-url.railway.app/api/status
   curl https://your-main-app-url.railway.app/api/reminders/last-date
   ```

#### 5. WhatsApp Messages Not Sending

**Symptoms**: Reminders are processed but not delivered via WhatsApp.

**Debugging Steps**:
1. **Check Green API credentials**:
   - Verify `GREEN_API_TOKEN` and `GREEN_API_INSTANCE_ID` are correct
   - Check Green API dashboard for instance status

2. **Test Green API directly**:
   ```bash
   python test_ai.py
   ```

3. **Check recipient phone number**:
   - Format: country code without `+` (e.g., `972501234567`)
   - Verify the number is registered on WhatsApp
   - Test with a different number temporarily

#### 6. Database Issues

**Symptoms**: Data not persisting, statistics not updating.

**Debugging Steps**:
1. **Check Railway volume**:
   - Verify `/data` volume is mounted
   - Check database file exists: `/data/reminder.db`

2. **Test database endpoints**:
   ```bash
   curl https://your-main-app-url.railway.app/api/database/stats
   ```

3. **Check database permissions**:
   - Ensure the app has write permissions to `/data` directory

### Debug Tools

#### Connection Test Script

Use the included test script to debug connection issues:

```bash
# Set your main app URL
export MAIN_APP_URL=https://your-main-app-url.railway.app

# Run the test
python test_connection.py
```

This will test:
- Connection to main app endpoints
- Timezone handling
- Environment variable configuration

#### Manual Testing

Test individual components:

```bash
# Test main app
curl -X POST https://your-main-app-url.railway.app/api/send-reminder

# Test reminder service
python reminder_service.py

# Test Green API
python test_ai.py
```

### Getting Help

If you're still experiencing issues:

1. **Check the logs** in Railway dashboard
2. **Run the debug tools** mentioned above
3. **Verify environment variables** are set correctly
4. **Test with a simple setup** first (single service deployment)

### Available Commands
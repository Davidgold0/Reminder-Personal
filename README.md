 # Pill Reminder App

A Python application that sends daily pill reminders via WhatsApp using Green API. The app sends reminders at 8:00 PM Israel time and processes incoming messages from the recipient.

## Features

- ⏰ **Daily Reminders**: Automatically sends pill reminders at 8:00 PM Israel time
- 💬 **Message Processing**: Handles incoming messages and responds appropriately
- 🤖 **AI-Powered Responses**: Optional OpenAI integration for intelligent message processing
- 📊 **Message History**: Tracks all interactions and provides statistics
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

**User**: "I took my pill just now"
**AI**: "Excellent! You're staying on top of your health. Keep up the great work! 💪"

**User**: "I forgot to take it yesterday"
**AI**: "No worries! Please take it as soon as possible. Your health is the priority. Don't beat yourself up - we all forget sometimes! 🏥"

**User**: "What time should I take my medicine?"
**AI**: "Your daily reminder is set for 8:00 PM Israel time. Try to take it around that time for consistency! ⏰"

## Usage

### Starting the App

```bash
python main.py
```

### Available Commands

- `start` - Start the reminder app (sends daily reminders and processes messages)
- `
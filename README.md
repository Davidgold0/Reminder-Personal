 # Pill Reminder App

A Python application that sends daily pill reminders via WhatsApp using Green API. The app sends reminders at 8:00 PM Israel time and processes incoming messages from the recipient.

## Features

- ⏰ **Daily Reminders**: Automatically sends pill reminders at 8:00 PM Israel time
- 💬 **Message Processing**: Handles incoming messages and responds appropriately
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

## Usage

### Starting the App

```bash
python main.py
```

### Available Commands

- `start` - Start the reminder app (sends daily reminders and processes messages)
- `test` - Send a test reminder immediately
- `status` - Show current app status and statistics
- `help` - Show available commands
- `quit` - Exit the app

### Message Commands

When the recipient receives a reminder, they can respond with:

- `taken`, `yes`, `done`, `ok`, `✅` - Confirm they took the pill
- `missed`, `no`, `forgot`, `❌` - Indicate they missed the pill
- `help`, `commands`, `?` - Get help with available commands

## File Structure

```
Reminder/
├── main.py                 # Main application entry point
├── config.py              # Configuration management
├── green_api_client.py    # Green API integration
├── message_processor.py   # Message processing logic
├── reminder_scheduler.py  # Scheduling and reminders
├── requirements.txt       # Python dependencies
├── env_example.txt        # Environment variables template
├── README.md             # This file
└── message_history.json  # Message history (created automatically)
```

## How It Works

1. **Scheduler**: Runs daily at 8:00 PM Israel time to send pill reminders
2. **Message Processing**: Continuously monitors for incoming messages
3. **Response System**: Automatically responds to user messages based on keywords
4. **History Tracking**: Saves all interactions to `message_history.json`

## Troubleshooting

### Common Issues

1. **Green API Connection Error**:
   - Check your API credentials in `.env`
   - Ensure your WhatsApp instance is authorized
   - Verify your instance is online in the Green API dashboard

2. **Messages Not Sending**:
   - Verify the recipient phone number format
   - Check if the number is registered on WhatsApp
   - Ensure your Green API instance has sufficient credits

3. **Timezone Issues**:
   - The app uses `Asia/Jerusalem` timezone
   - Make sure your system clock is correct

### Getting Help

- Check the Green API documentation: [docs.green-api.com](https://docs.green-api.com/)
- Verify your configuration with the `status` command
- Check the console output for error messages

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- Your Green API credentials provide access to your WhatsApp instance
- The app stores message history locally in `message_history.json`

## License

This project is open source. Feel free to modify and distribute as needed.

## Support

For issues related to:
- **Green API**: Contact Green API support
- **This App**: Check the troubleshooting section above
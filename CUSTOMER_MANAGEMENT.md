# Customer Management System

## Overview

The reminder app now supports multiple recipients through a customer management system. Instead of using a single `RECIPIENT_PHONE` from the environment variables, the app now stores customer phone numbers in the database.

## Features

### Database Table: `customers`

The system uses a new database table with the following structure:

```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT NOT NULL UNIQUE,
    name TEXT,
    reminder_time TEXT DEFAULT '20:00',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints

#### GET `/api/customers`
- Get all customers (active by default)
- Query parameter: `active_only=true/false`

#### POST `/api/customers`
- Add a new customer
- Body: `{"phone_number": "972501234567", "name": "Customer Name", "reminder_time": "20:00"}`

#### PUT `/api/customers/<customer_id>`
- Update a customer
- Body: `{"name": "New Name", "is_active": true, "reminder_time": "21:00"}`

#### DELETE `/api/customers/<customer_id>`
- Soft delete a customer (sets `is_active` to false)

#### GET `/api/customers/active-phones`
- Get all active phone numbers for sending reminders

#### GET `/api/customers/by-time/<reminder_time>`
- Get all active customers with a specific reminder time
- Example: `/api/customers/by-time/20:00`

#### GET `/api/customers/reminder-times`
- Get all unique reminder times from active customers

### Web Interface

The home page now includes a customer management section where you can:

1. **Add new customers** with phone number, optional name, and reminder time
2. **View all customers** with their status and reminder time
3. **Delete customers** (soft delete)
4. **See active recipients** and **reminder times** in the reminder schedule section

### Phone Number Format

- Use international format without the `+` symbol
- Example: `972501234567` (Israel number)
- Must be 10-15 digits
- Spaces, dashes, and parentheses are automatically removed

### Reminder System Changes

- Reminders are now sent to **customers at their scheduled times**
- Each customer can have their own reminder time (default: 20:00)
- The system checks all reminder times and sends to customers at the appropriate time
- The system tracks success/failure for each customer
- If no active customers exist, reminders will not be sent
- The old `RECIPIENT_PHONE` environment variable is now optional

## Migration from Single Recipient

If you were previously using a single `RECIPIENT_PHONE`:

1. Add your existing phone number as a customer through the web interface
2. The system will continue working as before
3. You can now add additional customers as needed

## Environment Variables

The following environment variables are now optional:
- `RECIPIENT_PHONE` - No longer required, but can be used as a fallback

Required environment variables remain the same:
- `GREEN_API_TOKEN`
- `GREEN_API_INSTANCE_ID`

## Testing

Run the test script to verify the customer management system:

```bash
python test_customer_system.py
```

## Usage Examples

### Adding a Customer via API

```bash
curl -X POST http://localhost:5000/api/customers \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "972501234567", "name": "John Doe", "reminder_time": "20:00"}'
```

### Getting Active Phone Numbers

```bash
curl http://localhost:5000/api/customers/active-phones
```

### Adding Multiple Customers

1. Open the web interface at `http://localhost:5000`
2. Go to the "Customer Management" section
3. Add each customer with their phone number, name, and reminder time
4. Each customer will receive daily reminders at their scheduled time

## Confirmation Tracking

The system now tracks whether customers confirm taking their pills:

### How It Works

1. **Reminder Sent**: When a reminder is sent, a record is created in `daily_reminders` table with `confirmed = False`
2. **Customer Response**: When customer sends a message, AI analyzes if they confirmed taking the pill
3. **Confirmation Update**: If confirmed, the record is updated with `confirmed = True`

### API Endpoints

#### GET `/api/confirmations/stats`
- Get confirmation statistics for the last 30 days
- Query parameter: `days_back` (default: 30)

#### GET `/api/confirmations/pending`
- Get pending confirmations (not yet confirmed)
- Query parameter: `days_back` (default: 7)

#### GET `/api/confirmations/customer/<customer_id>`
- Get confirmation history for a specific customer
- Query parameter: `days_back` (default: 30)

#### GET `/api/confirmations/date/<date>`
- Get all confirmations for a specific date (YYYY-MM-DD format)

### Web Interface

The home page now includes a "Confirmation Tracking" section showing:
- Confirmation statistics (total, confirmed, pending, confirmation rate)
- List of pending confirmations
- Real-time updates when confirmations are processed 
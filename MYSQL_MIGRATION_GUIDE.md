# MySQL Migration for Railway Deployment Guide

## Overview
This project has been migrated from SQLite to MySQL to support Railway's cloud deployment platform. This guide covers the migration process and deployment steps.

## What Changed

### 1. Database Layer
- **Before**: SQLite with local file storage (`/data/reminder.db`)
- **After**: MySQL with Railway's managed database service
- **Files Updated**: `database.py`, `requirements.txt`, `config.py`

### 2. Dependencies
- **Added**: `mysql-connector-python==8.1.0`
- **Removed**: No SQLite dependencies (built into Python)

### 3. Configuration
- **Added**: MySQL connection parameters and Railway DATABASE_URL support
- **Environment Variables**: See `env_example.txt` for full list

### 4. SQL Syntax Updates
- **Parameter Placeholders**: `?` → `%s`
- **Auto-increment**: `INTEGER PRIMARY KEY AUTOINCREMENT` → `INT AUTO_INCREMENT PRIMARY KEY`
- **Data Types**: `TEXT` → `VARCHAR(255)` or `TEXT`, `BOOLEAN` → `TINYINT(1)`
- **Timestamps**: Updated to use MySQL `TIMESTAMP` and `NOW()` functions

## Railway Deployment Setup

### Step 1: Create Railway Project
1. Go to [Railway](https://railway.app)
2. Create new project from GitHub repository
3. Connect your `Reminder-Personal` repository

### Step 2: Add MySQL Service
1. In Railway dashboard, click "New Service"
2. Select "Database" → "MySQL"
3. Railway will automatically create a MySQL instance
4. The `DATABASE_URL` environment variable will be automatically provided

### Step 3: Configure Environment Variables
Set these environment variables in Railway (under Variables tab):

#### Required Variables
```bash
GREEN_API_TOKEN=your_green_api_token_here
GREEN_API_INSTANCE_ID=your_green_api_instance_id_here
RECIPIENT_PHONE=972501234567
USE_MYSQL=true
```

#### Optional Variables
```bash
# OpenAI Integration (if desired)
OPENAI_ENABLED=true
OPENAI_API_KEY=your_openai_api_key_here

# Webhook (if using external webhooks)
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://your-webhook-endpoint.com
```

#### Database Variables (Automatically Set by Railway)
```bash
DATABASE_URL=mysql://user:password@host:port/database
```
*Note: Railway automatically provides DATABASE_URL when you add MySQL service*

### Step 4: Deploy
1. Railway will automatically deploy when you push changes
2. Check deployment logs for any issues
3. Tables will be created automatically on first run

## Local Development Setup

### Option 1: Use Local MySQL
```bash
# Install MySQL locally
brew install mysql  # macOS
# or use Docker
docker run -d -p 3306:3306 --name mysql-reminder -e MYSQL_ROOT_PASSWORD=root mysql:8

# Set environment variables
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_DATABASE=reminder_db
export MYSQL_USER=root
export MYSQL_PASSWORD=root
export USE_MYSQL=true
```

### Option 2: Use Railway MySQL for Development
```bash
# Get DATABASE_URL from Railway dashboard
export DATABASE_URL="mysql://user:password@host:port/database"
export USE_MYSQL=true
```

## Testing the Migration

Run the migration test script:
```bash
python test_mysql_migration.py
```

This will test:
- Configuration loading
- MySQL connection
- Table creation
- Basic database operations

## Rollback Plan

If you need to rollback to SQLite:
1. Set environment variable: `USE_MYSQL=false`
2. Restore original database.py: `cp database_sqlite_original.py database.py`
3. Remove mysql-connector-python from requirements.txt

## Migration Verification

After deployment, verify these work:
- [ ] Application starts without errors
- [ ] Database tables are created
- [ ] Messages can be saved and retrieved
- [ ] Reminder scheduling works
- [ ] Customer management functions
- [ ] Escalation system operates correctly

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes (Railway) | - | Railway MySQL connection string |
| `USE_MYSQL` | Yes | true | Enable MySQL instead of SQLite |
| `GREEN_API_TOKEN` | Yes | - | Green API authentication token |
| `GREEN_API_INSTANCE_ID` | Yes | - | Green API instance ID |
| `RECIPIENT_PHONE` | No | - | Default recipient phone number |
| `OPENAI_ENABLED` | No | false | Enable AI message processing |
| `WEBHOOK_ENABLED` | No | false | Enable webhook notifications |

## Troubleshooting

### Common Issues

1. **Connection Error**: Check DATABASE_URL format and MySQL service status
2. **Authentication Failed**: Verify Railway MySQL credentials
3. **Table Creation Failed**: Check MySQL user permissions
4. **Import Error**: Ensure mysql-connector-python is installed

### Railway-Specific Issues

1. **Build Failed**: Check requirements.txt includes mysql-connector-python
2. **Service Won't Start**: Verify DATABASE_URL is set by Railway
3. **Connection Timeout**: Check Railway MySQL service is running

### Debug Commands

```bash
# Test database connection
python -c "from database import Database; db = Database(); print('Connected!')"

# Check tables
python -c "
from database import Database
db = Database()
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('SHOW TABLES')
    print('Tables:', cursor.fetchall())
"
```

## Performance Considerations

- MySQL connection pooling is configured in the Database class
- Connections use SSL for security (Railway requirement)
- Automatic table creation on initialization
- Proper transaction handling with commit/rollback

## Security Notes

- All connections use SSL/TLS encryption
- Railway manages database credentials securely
- No database credentials stored in code
- Environment variables used for all sensitive data
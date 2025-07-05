# 2-Service Railway Deployment Guide

This guide explains how to deploy your pill reminder app as two separate Railway services with shared database access.

## Architecture Overview

```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│   Main App      │◄──────────────►│  Reminder       │
│   Service       │                │  Service        │
│                 │                │                 │
│ • Web Interface │                │ • Cron Job      │
│ • Message Proc  │                │ • AI Messages   │
│ • Database      │                │ • WhatsApp API  │
│ • API Endpoints │                │                 │
└─────────────────┘                └─────────────────┘
```

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Git Repository**: Your code should be in a Git repo (GitHub, GitLab, etc.)
3. **Green API Setup**: WhatsApp instance configured
4. **Environment Variables**: All required variables ready

## Step 1: Deploy Main App Service

### 1.1 Create Railway Project
1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### 1.2 Configure Main App Service
1. Railway will auto-detect it's a Python app
2. The `railway.json` file will be used automatically
3. Set environment variables:
   ```
   GREEN_API_TOKEN=your_token
   GREEN_API_INSTANCE_ID=your_instance_id
   RECIPIENT_PHONE=972501234567
   OPENAI_ENABLED=true
   OPENAI_API_KEY=your_openai_key
   TIMEZONE=Asia/Jerusalem
   WEBHOOK_ENABLED=true
   WEBHOOK_URL=https://your-main-app-url.railway.app
   ```

### 1.3 Deploy and Get URL
1. Click "Deploy"
2. Wait for deployment to complete
3. Copy the generated URL (e.g., `https://your-app-name.railway.app`)

## Step 2: Deploy Reminder Service

### 2.1 Create Second Service
1. In the same Railway project, click "New Service"
2. Select "GitHub Repo" again
3. Choose the **same repository** as the main app

### 2.2 Configure Reminder Service
1. Railway will use the same repo but different configuration
2. **Important**: Rename the service to "reminder-service" for clarity
3. Set environment variables (same as main app + two new ones):
   ```
   GREEN_API_TOKEN=your_token
   GREEN_API_INSTANCE_ID=your_instance_id
   RECIPIENT_PHONE=972501234567
   OPENAI_ENABLED=true
   OPENAI_API_KEY=your_openai_key
   TIMEZONE=Asia/Jerusalem
   MAIN_APP_URL=https://your-main-app-url.railway.app
   SERVICE_TYPE=reminder
   ```

### 2.3 Configure Environment Variable
1. Go to the reminder service settings
2. In "Variables" section, add:
   ```
   SERVICE_TYPE=reminder
   ```
3. This tells Railway to run the reminder service instead of the main app

### 2.4 Deploy Reminder Service
1. Click "Deploy"
2. Wait for deployment to complete

## Step 3: Configure Railway Cron

### 3.1 Set Up Cron Job
1. Go to the **reminder service** (not main app)
2. Click "Settings" tab
3. Scroll down to "Cron Jobs"
4. Add new cron job:
   - **Schedule**: `0 17 * * *` (5 PM UTC = 8 PM Israel time)
   - **Command**: `python reminder_service.py`

### 3.2 Test Cron Setup
1. Click "Run Now" to test the cron job
2. Check logs to see if it runs successfully
3. Verify the reminder service can connect to main app

## Step 4: Testing

### 4.1 Test Main App
```bash
# Test health endpoint
curl https://your-main-app-url.railway.app/health

# Test reminder endpoint
curl -X POST https://your-main-app-url.railway.app/api/send-reminder

# Test reminder API endpoints
curl https://your-main-app-url.railway.app/api/reminders/last-date
```

### 4.2 Test Reminder Service
```bash
# Test reminder service directly
curl -X POST https://your-reminder-service-url.railway.app/api/send-reminder
```

### 4.3 Test Locally (Optional)
```bash
# Start main app locally
python app.py

# In another terminal, test reminder service
python test_reminder_service.py http://localhost:5000
```

## Step 5: Monitoring

### 5.1 Check Logs
- **Main App**: Check for web requests and message processing
- **Reminder Service**: Check for cron job execution and API calls

### 5.2 Monitor Database
- Use the main app's web interface to view message history
- Check `/api/database/stats` endpoint for database statistics

### 5.3 Set Up Alerts
- Configure Railway notifications for deployment failures
- Monitor cron job execution logs

## Troubleshooting

### Common Issues

#### 1. Reminder Service Can't Connect to Main App
**Symptoms**: Network errors in reminder service logs
**Solution**: 
- Check `MAIN_APP_URL` environment variable
- Ensure main app is running and accessible
- Test with `curl` from reminder service

#### 2. Database Access Issues
**Symptoms**: API errors when saving/marking reminders
**Solution**:
- Verify main app database endpoints are working
- Check main app logs for database errors
- Ensure both services have same environment variables

#### 3. Cron Job Not Running
**Symptoms**: No reminder service logs at scheduled time
**Solution**:
- Check cron job configuration in Railway dashboard
- Verify timezone settings (Railway uses UTC)
- Test cron job manually with "Run Now"

#### 4. Duplicate Reminders
**Symptoms**: Multiple reminders sent at same time
**Solution**:
- Check if both services are running cron jobs
- Ensure only reminder service has cron configured
- Verify missed reminder detection logic

### Debug Commands

```bash
# Check main app status
curl https://your-main-app-url.railway.app/api/status

# Test reminder service API calls
curl https://your-main-app-url.railway.app/api/reminders/last-date

# Check database stats
curl https://your-main-app-url.railway.app/api/database/stats

# Test AI reminder generation
curl -X POST https://your-main-app-url.railway.app/api/test-ai-reminder
```

## Cost Optimization

### Railway Pricing
- **Main App**: ~$5-10/month (web service + database)
- **Reminder Service**: ~$5/month (minimal usage)
- **Total**: ~$10-15/month

### Optimization Tips
1. **Use single service** for development/testing
2. **Scale down** reminder service when not needed
3. **Monitor usage** in Railway dashboard
4. **Consider single service** if cost is a concern

## Migration from Single Service

If you're migrating from a single service setup:

1. **Backup data**: Export database if needed
2. **Deploy main app**: Use existing configuration
3. **Deploy reminder service**: Follow steps above
4. **Update cron**: Move from main app to reminder service
5. **Test thoroughly**: Ensure everything works
6. **Remove old cron**: Delete cron job from main app

## Support

For issues with this setup:
1. Check Railway documentation
2. Review logs in Railway dashboard
3. Test locally with `test_reminder_service.py`
4. Verify environment variables are correct 
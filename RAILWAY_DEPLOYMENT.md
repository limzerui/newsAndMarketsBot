# Deploying Financial News Bot on Railway

This guide provides step-by-step instructions to deploy your Financial News Bot on Railway, a free cloud platform for hosting applications.

## Why Railway?

- Free tier for small applications
- Easy deployment process
- Automatic scaling
- Built-in monitoring
- Automatic HTTPS

## Prerequisites

1. A [Railway account](https://railway.app/)
2. Your bot code in a GitHub repository
3. Your environment variables ready (API keys, tokens, etc.)

## Step 1: Install Railway CLI (Optional)

If you prefer using the command line:

```bash
npm i -g @railway/cli
```

## Step 2: Deploy via Web Interface

### Option 1: Deploy from GitHub

1. Log in to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Select your GitHub repository
5. Configure the deployment:
   - Set the build command: `pip install -r requirements.txt`
   - Set the start command: `python simple_solution.py`

### Option 2: Deploy via CLI

1. Login to Railway:
   ```bash
   railway login
   ```
2. Initialize your project:
   ```bash
   cd /path/to/TelegramBot2
   railway init
   ```
3. Deploy your project:
   ```bash
   railway up
   ```

## Step 3: Configure Environment Variables

### Via Web Interface

1. Go to your project in the Railway dashboard
2. Click on the "Variables" tab
3. Add the following variables:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELEGRAM_BOT_TOKEN`
   - `TELETHON_SESSION_STRING`
   - `OPENAI_API_KEY`
   - `TARGET_CHANNEL` (optional, default is 'marketfeed')

### Via CLI

```bash
railway variables set \
  TELEGRAM_API_ID=your_api_id \
  TELEGRAM_API_HASH=your_api_hash \
  TELEGRAM_BOT_TOKEN=your_bot_token \
  TELETHON_SESSION_STRING=your_session_string \
  OPENAI_API_KEY=your_openai_key \
  TARGET_CHANNEL=channel_name
```

## Step 4: Deploy Your Bot

If you're using the CLI, you can deploy with:

```bash
railway up
```

If you're using the web interface, the deployment should start automatically after you configure your environment variables.

## Step 5: Monitor Your Bot

1. Go to your project in the Railway dashboard
2. Click on the "Deployments" tab to see the logs
3. Check that your bot is running correctly

### Viewing Logs

```bash
railway logs
```

## Step 6: Manage Your Deployment

### Restart the bot

```bash
railway service restart
```

### Update the bot

If you make changes to your code and push to GitHub, Railway will automatically redeploy your bot.

## Step 7: Keep Your Bot Running

Railway's free tier has limitations regarding uptime and usage. If you need more reliability:

1. Consider upgrading to a paid plan
2. Set up a monitoring service like UptimeRobot to ping your bot regularly

## Troubleshooting

- **Bot not responding**: Check the logs for errors.
- **Deployment failing**: Verify your environment variables.
- **Session errors**: Your session string might be invalid, generate a new one.

## Advanced Configuration

### Custom Domain (Paid feature)

1. Go to the "Settings" tab in your project
2. Click "Custom Domain"
3. Follow the instructions to add a custom domain

### Persistent Storage (Paid feature)

1. Add a volume to your project
2. Configure it to store your subscribers.json file

## Security Considerations

- Never commit your `.env` file or API keys to GitHub
- Keep your session string private
- Regularly rotate your API keys

For more help, refer to the [Railway documentation](https://docs.railway.app/) 
# Financial News Bot

A Telegram bot that monitors financial news channels, summarizes the content using AI, and sends periodic summaries to subscribers.

## Features

- **Channel Monitoring**: Monitors financial news channels on Telegram (default: "marketfeed")
- **AI Summaries**: Generates concise summaries using OpenAI's GPT models
- **Stock Impact Analysis**: Identifies potentially impacted stocks and market sectors
- **Sentiment Analysis**: Determines if the news has bullish, bearish, or neutral sentiment
- **Markdown Formatting**: Properly formatted messages with bold text and bullet points
- **Subscriber System**: Users can subscribe/unsubscribe to receive updates
- **Automatic Notifications**: Notifies subscribers when the bot starts up

## Prerequisites

- Python 3.8+
- Telegram API credentials (API ID and API Hash) from [my.telegram.org](https://my.telegram.org/apps)
- Telegram Bot Token from [@BotFather](https://t.me/botfather)
- OpenAI API Key from [OpenAI Platform](https://platform.openai.com/account/api-keys)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd TelegramBot2
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following variables:
   ```
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELETHON_SESSION_STRING=your_session_string
   OPENAI_API_KEY=your_openai_key
   TARGET_CHANNEL=channel_name  # default is 'marketfeed'
   ```

## Step-by-Step Setup

### 1. Create a Telegram Application

1. Go to [my.telegram.org](https://my.telegram.org/apps) and log in
2. Create a new application to get your API ID and API Hash
3. Add these to your `.env` file as `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`

### 2. Create a Telegram Bot

1. Talk to [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow the instructions to create a new bot
3. Copy the provided token to your `.env` file as `TELEGRAM_BOT_TOKEN`

### 3. Generate a Session String

The session string allows the bot to connect to Telegram as a user to monitor channels:

```bash
python3 session_generator.py
```

Follow the prompts to authenticate and generate a session string, then add it to your `.env` file as `TELETHON_SESSION_STRING`.

### 4. Get an OpenAI API Key

1. Create an account or log in at [OpenAI](https://platform.openai.com/)
2. Navigate to the [API Keys section](https://platform.openai.com/account/api-keys)
3. Generate a new key and add it to your `.env` file as `OPENAI_API_KEY`

## Usage

### Running the Bot

To run the bot in normal mode (5-hour interval between summaries):

```bash
python3 simple_solution.py
```

To run in test mode with shorter intervals (5 minutes):

```bash
python3 simple_solution.py --test
```

To enable debug logging:

```bash
python3 simple_solution.py --debug
```

To automatically add yourself as a subscriber when starting the bot:

```bash
python3 simple_solution.py --admin_id YOUR_TELEGRAM_ID
```

### Bot Commands

Once the bot is running, users can interact with it using these commands:

- `/start` - Subscribe to financial news summaries
- `/stop` - Unsubscribe from updates
- `/help` - Show help message and available commands
- `/status` - Show bot status and subscriber count
- `/test` - Generate and send a test summary immediately
- `/subscribe_me` - Alternative command to subscribe

## Deploying on a Free Server

### Option 1: Railway

Railway offers a free tier for hosting applications:

1. Sign up at [Railway](https://railway.app/)
2. Install the Railway CLI:
   ```bash
   npm i -g @railway/cli
   ```
3. Login to Railway:
   ```bash
   railway login
   ```
4. Initialize your project:
   ```bash
   railway init
   ```
5. Add environment variables:
   ```bash
   railway vars set TELEGRAM_API_ID=your_api_id TELEGRAM_API_HASH=your_api_hash TELEGRAM_BOT_TOKEN=your_bot_token TELETHON_SESSION_STRING=your_session_string OPENAI_API_KEY=your_openai_key TARGET_CHANNEL=channel_name
   ```
6. Deploy your project:
   ```bash
   railway up
   ```

### Option 2: Render

Render also offers free hosting:

1. Create an account at [Render](https://render.com/)
2. Create a new Web Service and connect your GitHub repository
3. Set the build command: `pip install -r requirements.txt`
4. Set the start command: `python simple_solution.py`
5. Add all environment variables from your `.env` file
6. Deploy the service

### Option 3: Google Cloud Run

Google Cloud offers a free tier for Cloud Run:

1. Create a Google Cloud account
2. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
3. Build your Docker container:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/financial-news-bot
   ```
4. Deploy to Cloud Run:
   ```bash
   gcloud run deploy --image gcr.io/YOUR_PROJECT_ID/financial-news-bot --platform managed
   ```
5. Set environment variables in the Google Cloud Console

## Troubleshooting

- **Connection Issues**: If the bot can't connect to Telegram, verify your API credentials and session string.
- **No Summaries Generated**: Check your OpenAI API key and ensure the target channel is accessible.
- **Messages Not Formatted**: The bot uses Markdown formatting with `parse_mode='md'`. Make sure your client supports markdown.
- **Not Receiving Messages**: Verify that you've subscribed with `/start` or `/subscribe_me` and check your bot's subscribers list.

## License

This project is licensed under the MIT License.

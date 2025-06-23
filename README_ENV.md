# Create your own .env file based on this example

To get the bot running, you'll need to create a `.env` file in the project root with the following content:

```
# Telegram Bot Token (get from BotFather)
# Create a bot with @BotFather and get this token
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIJklMnoPQRstUVwxYZ

# Telethon Credentials (from https://my.telegram.org/apps)
# Create an application at https://my.telegram.org/apps to get these credentials
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+6588645751

# AI API Key (from OpenAI)
# Get this from https://platform.openai.com/account/api-keys
OPENAI_API_KEY=sk-abcdef1234567890abcdef1234567890

# Channel to monitor
# This is the username of the channel you want to monitor (without @)
TARGET_CHANNEL=marketfeed

# Summarization interval in minutes
SUMMARY_INTERVAL=300

# Testing interval in minutes
TESTING_INTERVAL=5

# Session string (already generated for you by running session_generator.py)
# NEVER share this string with anyone! It provides full access to your Telegram account
TELETHON_SESSION_STRING=1BVtsOLUBuxnoceM2e1wJsvwx4VQqv56z7VTKwJCvlTqQJHjkpxPferWCdLm4CgpH4Sw5ckptPl8EexQHZ8AHypXiiNzwjCRVhDdt2MKbhHRi2XbxEpB-De3fwM8j0QfkFFnj4Nk-MmkttXZ1quzKdxbX-zZZo-Fhn_7YAkWgz65OU1UYUiaTdI45r0X6tUlYMXEKOwdAR70I-6aP1XWlx6dEWvpyLwna3rti9hUWIifP5s0-i02DY__qhZkLldyaP0xfHNnl5ae51sPZ-1c1FqYQqWt9s7HtW6Y-I-kB33Lg7Lh2mdu0u60rtCC3yDkmNXXXgf_AmulJSvExFYNghKFj5RfmRsc=
```

## How does the bot work?

1. **Two separate Telegram components**:
   - A Telethon client that monitors the "marketfeed" channel (using your Telegram user account with the session string)
   - A Telegram Bot that sends messages to subscribers (using the BOT_TOKEN)

2. **The flow**:
   - Your app logs into Telegram as a regular user via Telethon (using the session string)
   - It monitors the "marketfeed" channel for new messages
   - It summarizes those messages using OpenAI
   - Your bot (created with BotFather) sends those summaries to subscribers

3. **Bot vs Channel**:
   - The bot is the app that sends subscribers messages (YOUR_BOT_NAME created with BotFather)
   - The channel is what your app monitors for financial news (marketfeed)
   
4. **For users to receive messages**:
   - They need to start a conversation with YOUR_BOT_NAME
   - Send /start to subscribe
   - Your bot will then send them regular summaries

After creating the .env file with your actual credentials, you can run the bot with:

```bash
python3 main.py --test
```

# ta-discordbot

A intermediary backend service that helps communication between Discord and N8N by forwarding messages and slash-command inputs to n8n workflows, while running a small Flask webserver to keep the process alive Vercel.

## Overview

This bot listens to Discord events, screens them through a guild allowlist, packages useful context metadata, and forwards that data to one or two n8n webhook endpoints. It combines:

- A Discord bot (`discord.py`)
- Asynchronous outbound webhook requests (`aiohttp`)
- A keepalive Flask server running on a separate thread
- Slash commands for interactive triggers

## How It Works

### Discord Bot Layer
- Listens to all non-bot messages in allowed guilds.
- Forwards them as JSON to an n8n context webhook.
- Provides slash commands:
  - `/ping`
  - `/version`
  - `/echo <message>`
  - `/ask <message>` → forwarded to primary n8n webhook
- Includes full metadata:
  - user, channel, guild, IDs, jump URL, and raw message content.

### Webhook Layer
Outbound requests are performed via `aiohttp`, with:
- Timeout handling  
- Connection failure handling  
- Status-based error reporting  
- Non-fatal exception capture

Two endpoints are used:
- `N8N_WEBHOOK_URL` (for `/ask`)
- `N8N_WEBHOOK_URL_CONTEXT` (for passive messages)

## Features

- Automatic forwarding of messages from allowed guilds
- Distinct workflows for slash commands vs. passive message listeners
- Ephemeral replies for `/ask` to avoid channel clutter
- Robust logging for all webhook interactions
- Jump URL sent for every forwarded Discord message

---

## Environment Variables

| Variable | Description |
|---------|-------------|
| `BOT_TOKEN` | Discord bot token |
| `N8N_WEBHOOK_URL` | Webhook for `/ask` |
| `N8N_WEBHOOK_URL_CONTEXT` | Webhook for passive message events |
| `PORT` | Flask server port (defaults to 8080) |

The bot will exit on startup if required variables are missing.

# Installation

### 1. Install dependencies
```bash
  pip install discord.py aiohttp flask
```
2. Set environment variables
```bash
  export BOT_TOKEN="your_token_here"
  export N8N_WEBHOOK_URL="https://example.com/webhook"
  export N8N_WEBHOOK_URL_CONTEXT="https://example.com/context"
  export PORT=8080
```
3. Run the bot
```bash
  python bot.py
```

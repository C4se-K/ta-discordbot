import discord
from discord.ext import commands
import aiohttp
import os
import threading
from flask import Flask
import asyncio


BOT_TOKEN = os.environ.get('BOT_TOKEN')
N8N_URL = os.environ.get('N8N_WEBHOOK_URL')
N8N_URL_C = os.environ.get('N8N_WEBHOOK_URL_CONTEXT')
ALLOWED_GUILD_IDS = [1360032501103333476, 1367322720853032970]

if not BOT_TOKEN:
    print("Error: DISCORD_BOT_TOKEN environment variable not set.")
    exit()
if not N8N_URL:
    print("Error: N8N_WEBHOOK_URL environment variable not set.")
    exit()


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

flask_app = Flask(__name__)



async def send_to_webhook(payload: dict):
    """
    Sends a data payload to the configured N8N webhook URL.

    Args:
        payload: A dictionary containing the data to send.
    
    Returns:
        A tuple (bool, str) indicating success and a message.
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(N8N_URL_C, json=payload, timeout=15) as response:
                if response.status == 200:
                    response_text = await response.text()
                    print(f"Successfully sent to webhook. Response: {response_text}")
                    return True, "Payload delivered successfully."
                else:
                    error_text = await response.text()
                    print(f"Webhook Error: {response.status} - {error_text}")
                    return False, f'Failed to send message. Service returned status: {response.status}.'
        except asyncio.TimeoutError:
            print("Webhook request timed out.")
            return False, 'The request to the service timed out.'
        except aiohttp.ClientConnectorError as e:
            print(f"Webhook connection error: {e}")
            return False, f'Could not connect to the service: {e}'
        except Exception as e:
            print(f"An unexpected error occurred while sending to webhook: {e}")
            return False, f'An unexpected error occurred: {e}'


@flask_app.route('/')
def home():
    return "Discord bot is alive and running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if not message.guild or message.guild.id not in ALLOWED_GUILD_IDS:
        return

    payload = {
        "source": "on_message_listener",
        "content": message.content,
        "user_name": message.author.name,
        "user_id": str(message.author.id),
        "channel_name": message.channel.name if hasattr(message.channel, 'name') else "Unknown Channel",
        "channel_id": str(message.channel.id),
        "guild_name": message.guild.name,
        "guild_id": str(message.guild.id),
        "message_id": str(message.id),
        "message_url": message.jump_url
    }

    asyncio.create_task(send_to_webhook(payload))


@bot.tree.command(name="ping", description="Replies with Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="version", description="Replies with current version")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("ver. 1.1")

@bot.tree.command(name="echo", description="Echoes back your message.")
async def echo_slash(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(f'echo: {message}')

@bot.tree.command(name="ask", description="Sends your question/message to the n8n workflow.")
async def ask_slash(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)

    if interaction.guild_id not in ALLOWED_GUILD_IDS and ALLOWED_GUILD_IDS:
        await interaction.followup.send('Sorry, this command is not enabled for this server.', ephemeral=True)
        return

    payload = {
        "content": message,
        "user_name": interaction.user.name,
        "user_id": str(interaction.user.id),
        "channel_name": interaction.channel.name if hasattr(interaction.channel, 'name') else "DM",
        "channel_id": str(interaction.channel_id),
        "guild_name": interaction.guild.name if interaction.guild else "DM",
        "guild_id": str(interaction.guild_id) if interaction.guild_id else "DM"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(N8N_URL, json=payload, timeout=15) as response:
                if response.status == 200:
                    n8n_response_text = await response.text()
                    print(f"N8N Response: {n8n_response_text}")
                    await interaction.followup.send('Your message has been received and is being processed! (This might take 10-15 seconds)', ephemeral=True)
                else:
                    error_text = await response.text()
                    print(f"N8N Error: {response.status} - {error_text}")
                    await interaction.followup.send(f'Failed to send message to the service. Error code: {response.status}. Please try again later.', ephemeral=True)
        except asyncio.TimeoutError:
            print("N8N request timed out.")
            await interaction.followup.send('The request to the service timed out. Please try again later.', ephemeral=True)
        except aiohttp.ClientConnectorError as e:
            print(f"N8N connection error: {e}")
            await interaction.followup.send(f'Could not connect to the service. Please try again later. Error: {e}', ephemeral=True)
        except Exception as e:
            print(f"An unexpected error occurred while sending to N8N: {e}")
            await interaction.followup.send(f'An unexpected error occurred. Please inform the bot administrator. Error: {e}', ephemeral=True)



if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()


    async def main():
        async with bot:
            await bot.start(BOT_TOKEN)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutting down by user interrupt...")
    finally:
        print("Bot has shut down.")

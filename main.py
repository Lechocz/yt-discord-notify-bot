from dotenv import load_dotenv
load_dotenv()

import os
import discord
from discord.ext import tasks
from googleapiclient.discovery import build
from flask import Flask
from threading import Thread

# Načti proměnné z .env
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

last_live_video_id = None
CHECK_INTERVAL = 60  # v sekundách

# 🔁 TASK LOOP
@tasks.loop(seconds=CHECK_INTERVAL)
async def check_live_stream():
    global last_live_video_id
    print("Kontroluji YouTube live stream...")

    try:
        request = youtube.search().list(
            part='snippet',
            channelId=YOUTUBE_CHANNEL_ID,
            type='video',
            eventType='live',
            maxResults=1
        )
        response = request.execute()

        print("YouTube API odpověď:", response)

        if response['items']:
            live_video = response['items'][0]
            video_id = live_video['id']['videoId']
            title = live_video['snippet']['title']
            url = f'https://www.youtube.com/watch?v={video_id}'

            print(f"Živý stream nalezen: {title} ({video_id})")

            if video_id != last_live_video_id:
                print('📣 Posílám zprávu na Discord...')
                channel = bot.get_channel(DISCORD_CHANNEL_ID)
                if channel:
                    await channel.send(
                        f'@everyone 🔴 **Live stream právě začal!**\n📺 **{title}**\n▶️ {url}',
                        allowed_mentions=discord.AllowedMentions(everyone=True)
                    )
                    last_live_video_id = video_id
                else:
                    print("⚠️ Kanál nebyl nalezen!")
        else:
            print("Momentálně není žádný živý stream.")
            last_live_video_id = None

    except Exception as e:
        print(f"❌ Chyba při kontrole live streamu: {e}")

@bot.event
async def on_ready():
    print(f"✅ Bot je připojen jako {bot.user}")
    print(f"Servery, kde je bot přítomen: {[guild.name for guild in bot.guilds]}")
    check_live_stream.start()  # 💥 Toto spouští loop

# 🌐 Keep Replit alive
app = Flask('')

@app.route('/')
def home():
    return "Bot je online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

keep_alive()
bot.run(DISCORD_TOKEN)

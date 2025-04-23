import os, json, asyncio, logging, requests
from collections import defaultdict

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN   = os.getenv("DISCORD_TOKEN")
DIFY_K  = os.getenv("DIFY_API_KEY")
DIFY_URL= os.getenv("DIFY_API_URL", "https://api.dify.ai/v1/chat-messages")

if not all([TOKEN, DIFY_K]):
    raise SystemExit("Ontbrekende .env‑variabelen")

# Dify helper

_convo = defaultdict(lambda: None)          # conversation_id per user

def ask_dify(text: str, uid: str) -> str:
    """Synchroon → eenvoudige blocking‑call naar Dify"""
    payload = {
        "query": text,
        "inputs": {"_": ""},                # minimaal één key
        "response_mode": "blocking",
        "user": uid,
    }
    if _convo[uid]:
        payload["conversation_id"] = _convo[uid]

    r = requests.post(
        DIFY_URL,
        headers={"Authorization": f"Bearer {DIFY_K}", "Content-Type": "application/json"},
        json=payload, timeout=30
    )
    if r.ok:
        data = r.json()
        _convo[uid] = data.get("conversation_id")
        return data.get("answer") or data.get("text") or "⚠️ Geen antwoord."
    return f"⚠️ Dify {r.status_code}: {r.text[:200]}"

# Discord bot

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"✅  Ingelogd als {bot.user}")

@bot.command(help="!chat <vraag>  of @bot <vraag>")
async def chat(ctx: commands.Context, *, vraag: str):
    async with ctx.typing():
        reply = await asyncio.to_thread(ask_dify, vraag, str(ctx.author.id))
    await ctx.reply(reply, mention_author=False)

@bot.event
async def on_message(msg: discord.Message):
    if msg.author == bot.user:
        return
    if bot.user.mentioned_in(msg):
        vraag = msg.clean_content.replace(f"@{bot.user.display_name}", "").strip()
        if vraag:
            async with msg.channel.typing():
                reply = await asyncio.to_thread(ask_dify, vraag, str(msg.author.id))
            await msg.channel.send(reply)
    await bot.process_commands(msg)        # laat !chat werken


# Start

if __name__ == "__main__":
    logging.getLogger("discord").setLevel(logging.WARNING)  # still some silence
    bot.run(TOKEN)

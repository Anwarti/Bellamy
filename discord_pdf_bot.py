import os
import asyncio
import tempfile
import shutil
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from PyPDF2 import PdfReader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate


# Initial setup

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY omgevingsvariabele ontbreekt!")
if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN omgevingsvariabele ontbreekt!")

# Configure Google GenAI
import google.generativeai as genai  # noqa: E402

genai.configure(api_key=GOOGLE_API_KEY)

# Intents (message content is privileged, must be enabled in the portal)
intents = discord.Intents.default()
intents.message_content = True  # required for prefix commands

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Keep conversational chains per channel in memory
_conversation_chains: dict[int, ConversationalRetrievalChain] = {}

# Helper functions

def _pdfs_to_text(filepaths: list[Path]) -> str:
    text: str = ""
    for path in filepaths:
        with path.open("rb") as fp:
            reader = PdfReader(fp)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text
    return text


def _split_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    return splitter.split_text(text)


async def _download_attachment(att: discord.Attachment) -> Path:
    """Download an attachment asynchronously and return the local Path."""
    suffix = Path(att.filename).suffix or ".bin"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()

    async with aiohttp.ClientSession() as session:
        async with session.get(att.url) as resp:
            resp.raise_for_status()
            with Path(tmp.name).open("wb") as wf:
                wf.write(await resp.read())
    return Path(tmp.name)


def _faiss_path(channel_id: int) -> Path:
    return Path(f"faiss_index_{channel_id}")


def _build_vector_store(text_chunks: list[str], channel_id: int) -> FAISS:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    store = FAISS.from_texts(text_chunks, embedding=embeddings)
    store.save_local(_faiss_path(channel_id))
    return store


def _load_vector_store(channel_id: int):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    return FAISS.load_local(_faiss_path(channel_id), embeddings, allow_dangerous_deserialization=True)


def _make_chain(channel_id: int) -> ConversationalRetrievalChain:
    llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash-001", temperature=0.7)
    vector_store = _load_vector_store(channel_id)

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    prompt = PromptTemplate(
        template="""
    Je bent een behulpzame AI‑assistent die een natuurlijk gesprek voert over de geüploade PDF‑documenten.
    Gebruik de context uit de vectorstore, beheer de gespreksgeschiedenis en geef uitgebreide antwoorden.
    Stimuleer vervolgvragen door af te sluiten met iets als: "Is er nog iets anders waar je meer over wilt weten?"

    Gespreksgeschiedenis:
    {chat_history}

    Context:
    {context}

    Vraag:
    {question}

    Geef een uitgebreid en accuraat antwoord:
    """,
        input_variables=["chat_history", "context", "question"],
    )

    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        verbose=False,
    )


# Bot Commands

@bot.event
async def on_ready():
    print(f"\u2705  Bot online als {bot.user} (id={bot.user.id})")


@bot.command(name="processpdf", help="Upload deze command met PDF‑bijlagen om ze te verwerken")
async def processpdf(ctx: commands.Context):
    if not ctx.message.attachments:
        await ctx.reply("Voeg minstens één PDF‑bestand toe aan dezelfde boodschap.")
        return

    pdf_paths: list[Path] = []
    for attachment in ctx.message.attachments:
        if attachment.filename.lower().endswith(".pdf"):
            try:
                path = await _download_attachment(attachment)
                pdf_paths.append(path)
            except Exception as exc:
                await ctx.reply(f"Kon {attachment.filename} niet downloaden: {exc}")

    if not pdf_paths:
        await ctx.reply("Geen geldige PDF‑bestanden gevonden.")
        return

    await ctx.reply("⏳ PDF‑bestanden worden verwerkt, even geduld…")

    loop = asyncio.get_running_loop()
    raw_text = await loop.run_in_executor(None, _pdfs_to_text, pdf_paths)
    text_chunks = await loop.run_in_executor(None, _split_text, raw_text)
    await loop.run_in_executor(None, _build_vector_store, text_chunks, ctx.channel.id)

    _conversation_chains[ctx.channel.id] = _make_chain(ctx.channel.id)
    for p in pdf_paths:  # cleanup temp files
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass

    await ctx.reply("✅ PDF‑kennisbank is klaar voor gebruik! Stel je vragen met **!ask**.")


@bot.command(name="ask", help="Stel een vraag over de eerder geüploade PDF‑bestanden")
async def ask(ctx: commands.Context, *, vraag: str):
    chain = _conversation_chains.get(ctx.channel.id)
    if chain is None:
        await ctx.reply("Gebruik eerst !processpdf om PDF‑bestanden te verwerken.")
        return

    loop = asyncio.get_running_loop()
    async with ctx.typing():          # ⬅️ hier vervangen
        try:
            result = await loop.run_in_executor(None, chain, {"question": vraag})
        except Exception as exc:
            await ctx.reply(f"❌ Er ging iets mis: {exc}")
            return

    antwoord = result.get("answer", "[Geen antwoord gegenereerd]")
    await ctx.reply(antwoord)



@bot.command(name="reset", help="Wis de FAISS‑index en gespreksgeschiedenis voor dit kanaal")
async def reset(ctx: commands.Context):
    _conversation_chains.pop(ctx.channel.id, None)
    try:
        shutil.rmtree(_faiss_path(ctx.channel.id))
    except FileNotFoundError:
        pass
    await ctx.reply("🗑️ Kennisbank en chatgeschiedenis zijn gewist voor dit kanaal.")


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)

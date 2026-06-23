import asyncio
import json
import logging
import os
import re

from aiogram import Bot
from dotenv import load_dotenv
from pymax import Client
from pymax.types import FileAttachment, Message, PhotoAttachment, VideoAttachment

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

MAX_PHONE = os.getenv("MAX_PHONE")
MAX_CHAT_ID = int(os.getenv("MAX_CHAT_ID", "0"))
TG_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = int(os.getenv("TG_CHAT_ID", "0"))
MODE = os.getenv("MODE", "forward").lower()  # forward | notify

bot = Bot(token=TG_TOKEN)
client = Client(phone=MAX_PHONE, work_dir="cache", session_name="session.db")

_NAMES_FILE = os.path.join(os.path.dirname(__file__), "names.json")
try:
    with open(_NAMES_FILE, encoding="utf-8") as _f:
        _NAME_MAP: dict[str, str] = {k.lower(): v for k, v in json.load(_f).items()}
except FileNotFoundError:
    _NAME_MAP = {}


def _replace_names(text: str) -> str:
    if not _NAME_MAP:
        return text
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(k) for k in _NAME_MAP) + r")\b",
        re.IGNORECASE,
    )
    return pattern.sub(lambda m: _NAME_MAP[m.group(0).lower()], text)


def _user_display_name(user) -> str | None:
    if not user:
        return None
    for n in user.names or []:
        parts = [n.first_name, n.last_name]
        full = " ".join(p for p in parts if p)
        if full:
            return full
        if n.name:
            return n.name
    if user.phone:
        return f"+{user.phone}"
    if user.link:
        return user.link.split("/")[-1]
    return None


async def _sender_name(sender_id: int) -> str:
    user = client.get_cached_user(sender_id)
    if user is None:
        try:
            user = await client.get_user(sender_id)
        except Exception:
            pass
    return _user_display_name(user) or str(sender_id)


@client.on_start()
async def on_start(c: Client) -> None:
    my_id = c.me.contact.id if c.me else "?"
    logger.info("MAX connected, my id=%s, watching chat %s", my_id, MAX_CHAT_ID)


@client.on_message()
async def on_max_message(message: Message, c: Client) -> None:
    if message.chat_id != MAX_CHAT_ID:
        return

    my_id = c.me.contact.id if c.me else None
    if my_id and message.sender == my_id:
        return

    sender = await _sender_name(message.sender) if message.sender else "Неизвестный"
    content = ""

    if MODE == "notify":
        text = f"📨 Новое сообщение в MAX от <b>{sender}</b>"
    else:
        photos = [a for a in message.attaches if isinstance(a, PhotoAttachment)]
        videos = [a for a in message.attaches if isinstance(a, VideoAttachment)]
        files = [a for a in message.attaches if isinstance(a, FileAttachment)]

        if message.text:
            content = _replace_names(message.text)
        elif photos:
            content = "[фото]"
        elif videos:
            name = getattr(videos[0], "file_name", None) or "видео"
            content = f"[{name}]"
        elif files:
            name = getattr(files[0], "file_name", None) or "файл"
            content = f"[{name}]"
        else:
            return

        text = f"📨 <b>{sender}</b>: {content}"

    try:
        await bot.send_message(TG_CHAT_ID, text, parse_mode="HTML")
        logger.info("Notified TG: %s: %s", sender, content[:50])
    except Exception as e:
        logger.error("Failed to send TG notification: %s", e)


async def main() -> None:
    await asyncio.gather(
        client.start(),
        _dummy_polling(),
    )


async def _dummy_polling() -> None:
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())

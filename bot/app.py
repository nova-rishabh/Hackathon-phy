"""Telegram adapter (python-telegram-bot 22, long polling). All logic lives in bot/core.py."""
import io
import logging
import os
import sys

from telegram import Message, Update
from telegram.constants import ChatAction, ChatType
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bot import core
from bot.texts import L, with_footer

log = logging.getLogger("rollwatch.bot")
TG_MAX = 4000


async def _send(msg: Message, replies: list[core.Reply]) -> None:
    for r in replies:
        if r.kind == "text":
            for i in range(0, max(len(r.text), 1), TG_MAX):
                await msg.reply_text(r.text[i:i + TG_MAX])
        elif r.kind == "photo":
            await msg.reply_photo(photo=io.BytesIO(r.data))
        elif r.kind == "voice":
            await msg.reply_voice(voice=io.BytesIO(r.data))
        elif r.kind == "audio":  # MP3 when ffmpeg is missing
            await msg.reply_audio(audio=io.BytesIO(r.data), filename="rollwatch.mp3")


async def _photo_bytes(msg: Message) -> bytes | None:
    if msg.photo:
        f = await msg.photo[-1].get_file()
    elif msg.document and (msg.document.mime_type or "").startswith("image/"):
        f = await msg.document.get_file()
    else:
        return None
    return bytes(await f.download_as_bytearray())


def _api(ctx: ContextTypes.DEFAULT_TYPE) -> core.Api:
    api = ctx.application.bot_data.get("api")
    if api is None:
        api = ctx.application.bot_data["api"] = core.Api()
    return api


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    lang = (update.effective_user.language_code or "en")[:2] if update.effective_user else "en"
    lang = lang if lang in ("hi", "pa") else "en"
    await update.effective_message.reply_text(with_footer(L["start"][lang], lang))


async def check(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/check <text>, or /check as a reply to a forwarded text/screenshot (S11, works in groups)."""
    msg = update.effective_message
    text = " ".join(ctx.args or []).strip()
    target = msg.reply_to_message
    image = None
    if not text and target is not None:
        text = (target.text or target.caption or "").strip()
        image = await _photo_bytes(target)
    if not text and image is None:
        image = await _photo_bytes(msg)  # photo sent with caption "/check"
    lang = core.lang_of(text or msg.text)
    if not text and image is None:
        await msg.reply_text(with_footer(L["check_usage"][lang], lang))
        return
    await msg.chat.send_action(ChatAction.UPLOAD_PHOTO)
    await _send(msg, await core.handle_claim(_api(ctx), text=text or None, image=image, lang=lang if text else None))


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg.chat.type != ChatType.PRIVATE:
        return  # in groups the bot only answers /check
    await msg.chat.send_action(ChatAction.TYPING)
    if msg.forward_origin is not None:  # a forward is a claim to check
        await _send(msg, await core.handle_claim(_api(ctx), text=msg.text))
        return
    await _send(msg, await core.handle_text(_api(ctx), msg.text or ""))


async def on_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    caption = (msg.caption or "").strip()
    if msg.chat.type != ChatType.PRIVATE and not caption.startswith("/check"):
        return
    image = await _photo_bytes(msg)
    if image is None:
        return
    await msg.chat.send_action(ChatAction.UPLOAD_PHOTO)
    text = caption.removeprefix("/check").strip() or None
    await _send(msg, await core.handle_claim(_api(ctx), text=text, image=image))


async def on_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg.chat.type != ChatType.PRIVATE:
        return
    f = await (msg.voice or msg.audio).get_file()
    await msg.chat.send_action(ChatAction.RECORD_VOICE)
    await _send(msg, await core.handle_voice(_api(ctx), bytes(await f.download_as_bytearray())))


async def on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("handler error", exc_info=ctx.error)
    try:
        await _api(ctx).report_error(str(ctx.error), {"update_type": type(update).__name__})
    except Exception:
        pass
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(with_footer(L["api_down"]["en"], "en"))


async def _periodic_heartbeat(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await _api(ctx).heartbeat(state="healthy", details={"polling": True})
    except Exception:
        pass


def build(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(MessageHandler((filters.PHOTO | filters.Document.IMAGE), on_photo))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, on_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)
    if app.job_queue is not None:
        app.job_queue.run_repeating(_periodic_heartbeat, interval=30, first=5)
    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        sys.exit("TELEGRAM_BOT_TOKEN is not set. Export it (from @BotFather) and run `python -m bot` again.")
    if not os.environ.get("ELEVENLABS_API_KEY"):
        log.warning("ELEVENLABS_API_KEY not set: voice notes get a text reply only (cached TTS still used).")
    log.info("RollWatch bot polling; API_BASE=%s", core.API_BASE)
    build(token).run_polling(allowed_updates=Update.ALL_TYPES)

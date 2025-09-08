# debug_867.py
import os, json
from pyrogram import Client
from dotenv import load_dotenv
load_dotenv()

API_ID   = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
SESSION  = os.getenv("TG_SESSION", "pyro_session")
CHANNEL  = os.getenv("TG_CHANNEL", "kuda_namylilis")
TARGET_ID = 867

with Client(SESSION, api_id=API_ID, api_hash=API_HASH) as app:
    m = app.get_messages(CHANNEL, TARGET_ID)
    def yesno(x): return bool(x)

    info = {
        "id": m.id,
        "date": m.date.isoformat() if m.date else None,
        "has_media": yesno(m.media),
        "media_group_id": m.media_group_id,
        "has_caption": bool(m.caption),
        "caption": m.caption or "",
        "has_text": bool(m.text),
        "reply_to_message_id": m.reply_to_message_id,
    }

    # сосед справа (часто там текст)
    try:
        next_m = app.get_messages(CHANNEL, TARGET_ID + 1)
        info["next_id"] = next_m.id
        info["next_has_text"] = bool(next_m.text)
        info["next_reply_to"] = next_m.reply_to_message_id
    except Exception:
        info["next_id"] = None

    # если альбом — соберём состав
    if m.media_group_id:
        group = app.get_media_group(CHANNEL, TARGET_ID)
        info["album_len"] = len(group)
        info["album_any_caption"] = any(x.caption for x in group)
        info["album_ids"] = [x.id for x in group]
    print(json.dumps(info, ensure_ascii=False, indent=2))

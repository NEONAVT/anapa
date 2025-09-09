import os, json, pathlib, time, sys
from pyrogram import Client
from pyrogram.errors import FloodWait
from dotenv import load_dotenv

load_dotenv()

API_ID    = int(os.getenv("TG_API_ID", "0"))
API_HASH  = os.getenv("TG_API_HASH", "")
SESSION   = os.getenv("TG_SESSION", "pyro_session")
CHANNEL   = os.getenv("TG_CHANNEL", "")
OUT       = os.getenv("TG_OUT", "posts.json")
MEDIA_DIR = os.getenv("TG_MEDIA_DIR", "media")
LIMIT     = int(os.getenv("TG_LIMIT", "50"))  # сколько постов собрать

if not API_ID or not API_HASH or not CHANNEL:
    raise SystemExit("TG_API_ID / TG_API_HASH / TG_CHANNEL не заданы")

pathlib.Path(MEDIA_DIR).mkdir(parents=True, exist_ok=True)

def progress(current, total):
    if total:
        print(f"{current * 100 / total:.1f}% ({current}/{total})", end="\r")

def ext_from_mime(mime: str | None, default: str) -> str:
    if not mime: return default
    tail = mime.split("/")[-1].lower()
    return {"jpeg":"jpg","x-msvideo":"avi"}.get(tail, tail)

def filename_for(msg) -> str:
    if msg.document:
        return f"{msg.id}_{msg.document.file_name}" if msg.document.file_name else f"{msg.id}.{ext_from_mime(msg.document.mime_type,'bin')}"
    if msg.photo:       return f"{msg.id}.jpg"
    if msg.video:       return f"{msg.id}.mp4"
    if msg.animation:   return f"{msg.id}.mp4"
    if msg.audio:       return f"{msg.id}.{ext_from_mime(msg.audio.mime_type, 'mp3')}"
    if msg.voice:       return f"{msg.id}.ogg"
    if msg.video_note:  return f"{msg.id}.mp4"
    if msg.sticker:     return f"{msg.id}.webp"
    return f"{msg.id}.bin"

posts = []

with Client(SESSION, api_id=API_ID, api_hash=API_HASH) as app:
    offset_id = 0
    collected = 0
    groups = {}

    while True:
        batch = list(app.get_chat_history(CHANNEL, limit=200, offset_id=offset_id))
        if not batch:
            break

        for msg in batch:  # от новых к старым
            if collected >= LIMIT:
                break

            # одиночное медиа с caption
            if msg.media and msg.caption and not msg.media_group_id:
                fname = filename_for(msg)
                dest = os.path.join(MEDIA_DIR, fname)
                try:
                    saved = app.download_media(msg, file_name=dest, progress=progress)
                    media_files = [os.path.basename(saved)] if saved else []
                except FloodWait as e:
                    time.sleep(e.value)
                    saved = app.download_media(msg, file_name=dest, progress=progress)
                    media_files = [os.path.basename(saved)] if saved else []

                posts.append({
                    "id": msg.id,
                    "date": msg.date.isoformat() if msg.date else None,
                    "text": msg.caption,
                    "media": media_files
                })
                collected += 1
                print(f"[{collected}/{LIMIT}] Собрано (single)")  # <--- прогресс
                continue

            # альбом
            if msg.media_group_id and msg.caption:
                gid = msg.media_group_id
                if gid in groups:  # уже обработали
                    continue
                group = app.get_media_group(CHANNEL, msg.id)
                text = ""
                media_files = []
                for x in group:
                    if x.caption and not text:
                        text = x.caption
                    if x.media:
                        fname = filename_for(x)
                        dest = os.path.join(MEDIA_DIR, fname)
                        try:
                            saved = app.download_media(x, file_name=dest, progress=progress)
                            if saved:
                                media_files.append(os.path.basename(saved))
                        except FloodWait as e:
                            time.sleep(e.value)
                            saved = app.download_media(x, file_name=dest, progress=progress)
                            if saved:
                                media_files.append(os.path.basename(saved))
                if text and media_files:
                    posts.append({
                        "id": min(x.id for x in group),
                        "date": group[0].date.isoformat() if group[0].date else None,
                        "text": text,
                        "media": media_files
                    })
                    collected += 1
                    print(f"[{collected}/{LIMIT}] Собрано (album)")  # <--- прогресс
                groups[gid] = True
                continue

        if collected >= LIMIT:
            break
        offset_id = batch[-1].id  # идём глубже в прошлое

posts.sort(key=lambda x: x["id"], reverse=True)  # от свежих к старым

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(posts, f, ensure_ascii=False, indent=2)

print(f"\nИтог: {len(posts)} постов. JSON: {OUT}. Медиа: {MEDIA_DIR}/")

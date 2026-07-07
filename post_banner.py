"""
Auto Banner -> Telegram Poster
--------------------------------
1. Google Drive ke "new_banners" folder mein sabse purani photo dhoondta hai
2. Groq Vision model se banner ka text/detail padhta hai aur title/caption banata hai
3. Telegram channel pe photo + caption post karta hai
4. Photo ko "posted" folder mein move kar deta hai (dobara post na ho)

Environment variables (GitHub Secrets se aayenge):
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHANNEL      (e.g. @MISSION_SSC_CGL1)
- GROQ_API_KEY
- GDRIVE_NEW_FOLDER_ID
- GDRIVE_POSTED_FOLDER_ID
- GDRIVE_SERVICE_ACCOUNT_JSON   (poora JSON content, ek line/base64 string ke roop mein secret mein rakha jayega)
"""

import os
import io
import json
import base64
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# ---------- Config from environment ----------
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL = os.environ["TELEGRAM_CHANNEL"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
NEW_FOLDER_ID = os.environ["GDRIVE_NEW_FOLDER_ID"]
POSTED_FOLDER_ID = os.environ["GDRIVE_POSTED_FOLDER_ID"]
SERVICE_ACCOUNT_JSON = os.environ["GDRIVE_SERVICE_ACCOUNT_JSON"]

GROQ_VISION_MODEL = "qwen/qwen3.6-27b"  # current Groq vision-capable model (July 2026)

SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_drive_service():
    info = json.loads(SERVICE_ACCOUNT_JSON)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def get_oldest_pending_file(drive):
    """new_banners folder mein sabse purani image file dhoondo."""
    query = f"'{NEW_FOLDER_ID}' in parents and trashed = false and mimeType contains 'image/'"
    results = drive.files().list(
        q=query,
        orderBy="createdTime",
        fields="files(id, name, createdTime, mimeType)",
        pageSize=1,
    ).execute()
    files = results.get("files", [])
    return files[0] if files else None


def download_file(drive, file_id):
    request = drive.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buffer.seek(0)
    return buffer.read()


def move_file_to_posted(drive, file_id):
    drive.files().update(
        fileId=file_id,
        addParents=POSTED_FOLDER_ID,
        removeParents=NEW_FOLDER_ID,
        fields="id, parents",
    ).execute()


def analyze_banner_with_groq(image_bytes, mime_type):
    """Banner image bhejo Groq ko, wapas title + caption text milega."""
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt = (
        "Ye ek SSC CGL exam preparation banner hai jo Telegram channel pe post hoga. "
        "Is banner mein jo bhi text/topic/subject likha hai wo dhyan se padho. "
        "Fir ek Telegram post caption banao jaisa manually likha jaata hai: "
        "1) Ek attractive title line (emoji ke saath), "
        "2) Banner mein jo detail hai uska short summary (2-3 lines, Hinglish mein), "
        "3) Aakhri mein ek short call-to-action jaise 'Aage padho aur share karo'. "
        "Sirf final caption text do, koi extra explanation mat do."
    )

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_image}"
                            },
                        },
                    ],
                }
            ],
            "temperature": 0.7,
            "max_completion_tokens": 700,
            "reasoning_effort": "none",  # Qwen models ke liye thinking mode poora band karta hai
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    caption = data["choices"][0]["message"]["content"].strip()

    # Safety net: agar kabhi <think>...</think> aa jaye to usse hata do
    if "<think>" in caption and "</think>" in caption:
        caption = caption.split("</think>", 1)[1].strip()

    return caption


def send_to_telegram(image_bytes, caption, filename):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {"photo": (filename, image_bytes)}
    data = {"chat_id": TELEGRAM_CHANNEL, "caption": caption[:1024]}
    response = requests.post(url, data=data, files=files, timeout=60)
    response.raise_for_status()
    return response.json()


def main():
    drive = get_drive_service()

    pending = get_oldest_pending_file(drive)
    if not pending:
        print("Koi naya banner nahi mila new_banners folder mein. Kuch nahi karna aaj.")
        return

    file_id = pending["id"]
    file_name = pending["name"]
    mime_type = pending.get("mimeType", "image/jpeg")

    print(f"Processing: {file_name}")

    image_bytes = download_file(drive, file_id)
    caption = analyze_banner_with_groq(image_bytes, mime_type)
    print("Generated caption:\n", caption)

    result = send_to_telegram(image_bytes, caption, file_name)
    print("Telegram response:", result.get("ok"))

    move_file_to_posted(drive, file_id)
    print(f"'{file_name}' posted aur 'posted' folder mein move ho gaya.")


if __name__ == "__main__":
    main()

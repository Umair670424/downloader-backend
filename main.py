from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import yt_dlp
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "active", "message": "Downloader API is running smoothly!"}

@app.get("/api/extract")
def extract_video(url: str = Query(..., description="Video URL to extract")):
    try:
        decoded_url = urllib.parse.unquote(url).strip()

        # Check if TikTok URL -> Use TikWM Service for 100% Clean Link
        if "tiktok.com" in decoded_url or "vt.tiktok.com" in decoded_url:
            api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(decoded_url)}"
            res = requests.get(api_url, timeout=10).json()
            
            if res.get("code") == 0 and "data" in res:
                data = res["data"]
                # data['play'] provides no-watermark direct playable MP4
                return {
                    "success": True,
                    "title": data.get("title", "TikTok Video"),
                    "thumbnail": data.get("cover", ""),
                    "download_url": data.get("play"), 
                    "duration": data.get("duration", 0)
                }

        # Fallback to yt-dlp for Instagram, YouTube, etc.
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(decoded_url, download=False)
            download_url = info.get('url')
            if not download_url and 'formats' in info:
                for f in info['formats']:
                    if f.get('vcodec') != 'none' and f.get('url'):
                        download_url = f['url']
                        break

            if not download_url:
                raise HTTPException(status_code=400, detail="Could not extract direct video URL")

            return {
                "success": True,
                "title": info.get('title', 'Downloaded_Video'),
                "thumbnail": info.get('thumbnail', ''),
                "download_url": download_url,
                "duration": info.get('duration', 0)
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

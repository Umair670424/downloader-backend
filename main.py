from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import urllib.parse
import urllib.request
import json
import re
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_youtube_id(url: str):
    # Regex to pull Video ID from shorts, standard link, or shortened link
    patterns = [
        r'v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'shorts/([a-zA-Z0-9_-]{11})'
    ]
    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)
    return None

@app.get("/")
def home():
    return {"status": "active", "message": "Downloader API is running smoothly!"}

@app.get("/api/extract")
def extract_video(url: str = Query(..., description="Video URL to extract")):
    try:
        decoded_url = urllib.parse.unquote(url).strip()

        # 1. TikTok Extractor (TikWM API)
        if "tiktok.com" in decoded_url or "vt.tiktok.com" in decoded_url:
            tikwm_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(decoded_url)}"
            req = urllib.request.Request(tikwm_url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode())

            if res_data.get("code") == 0 and "data" in res_data:
                data = res_data["data"]
                return {
                    "success": True,
                    "title": data.get("title", "TikTok Video"),
                    "thumbnail": data.get("cover", ""),
                    "download_url": data.get("play"),
                    "duration": data.get("duration", 0)
                }

        # 2. YouTube Guaranteed Bypass (No yt-dlp to avoid Bot Block)
        if "youtube.com" in decoded_url or "youtu.be" in decoded_url:
            v_id = get_youtube_id(decoded_url)
            
            # Primary: Invidious Instances
            instances = [
                f"https://invidious.nerdvpn.de/api/v1/videos/{v_id}",
                f"https://inv.tux.pizza/api/v1/videos/{v_id}",
                f"https://vid.puffyan.us/api/v1/videos/{v_id}"
            ]
            
            if v_id:
                for inst in instances:
                    try:
                        req = urllib.request.Request(inst, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=6) as response:
                            res_data = json.loads(response.read().decode())
                            formats = res_data.get("formatStreams", [])
                            if formats:
                                return {
                                    "success": True,
                                    "title": res_data.get("title", "YouTube Video"),
                                    "thumbnail": f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg",
                                    "download_url": formats[-1].get("url"),
                                    "duration": res_data.get("lengthSeconds", 0)
                                }
                    except Exception:
                        continue

            return {
                "success": False,
                "error": "YouTube temporary server busy. Please try another link."
            }

        # 3. Instagram / Other Social Platforms (yt-dlp)
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
        return {
            "success": False,
            "error": str(e)
        }

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

def extract_youtube_id(url: str):
    pattern = r'(?:v=|\/([0-9A-Za-z_-]{11})|youtu\.be\/)'
    match = re.search(pattern, url)
    if match:
        return match.group(1) or match.group(0).replace('v=', '').replace('/', '')
    return None

@app.get("/")
def home():
    return {"status": "active", "message": "Downloader API is running smoothly!"}

@app.get("/api/extract")
def extract_video(url: str = Query(..., description="Video URL to extract")):
    try:
        decoded_url = urllib.parse.unquote(url).strip()

        # 1. TikTok Extractor (TikWM - Free & Stable)
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

        # 2. YouTube Bypass (Using Invidious / Piped API - No Bot Block & No Cookies Required)
        if "youtube.com" in decoded_url or "youtu.be" in decoded_url:
            video_id = extract_youtube_id(decoded_url)
            if video_id:
                # Primary API: Invidious Public Instance
                invidious_instances = [
                    f"https://api.invidious.io/api/v1/videos/{video_id}",
                    f"https://invidious.nerdvpn.de/api/v1/videos/{video_id}",
                    f"https://inv.tux.pizza/api/v1/videos/{video_id}"
                ]
                
                for inst_url in invidious_instances:
                    try:
                        req = urllib.request.Request(inst_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=5) as response:
                            res_data = json.loads(response.read().decode())
                            
                            formats = res_data.get("formatStreams", [])
                            if formats:
                                # Pick best combined video+audio MP4
                                best_stream = formats[-1].get("url")
                                return {
                                    "success": True,
                                    "title": res_data.get("title", "YouTube Video"),
                                    "thumbnail": res_data.get("videoThumbnails", [{}])[0].get("url", ""),
                                    "download_url": best_stream,
                                    "duration": res_data.get("lengthSeconds", 0)
                                }
                    except Exception:
                        continue # If instance fails, try next instance

        # 3. Instagram & Fallback Extractor (yt-dlp with TV/IOS Client Bypass)
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'mweb']
                }
            },
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
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

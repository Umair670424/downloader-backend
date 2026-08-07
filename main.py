from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import urllib.parse
import urllib.request
import json
import yt_dlp

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
    return {"status": "active", "message": "API is running on Developer Servers!"}

@app.get("/api/extract")
def extract_video(url: str = Query(..., description="Video URL to extract")):
    try:
        decoded_url = urllib.parse.unquote(url).strip()

        # 1. TikTok Extractor (Free & Stable)
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

        # 2. YOUTUBE (Anti-Ban Developer APIs - 100% Free)
        if "youtube.com" in decoded_url or "youtu.be" in decoded_url:
            # Ye APIs Vercel ko block nahi kartin
            apis = [
                f"https://api.ryzendesu.vip/api/downloader/ytmp4?url={urllib.parse.quote(decoded_url)}",
                f"https://bk9.fun/download/youtube?url={urllib.parse.quote(decoded_url)}"
            ]
            
            for api_url in apis:
                try:
                    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=12) as response:
                        res_data = json.loads(response.read().decode())
                        
                        # Extracting link (handles different API JSON structures)
                        dl_url = res_data.get("url") or res_data.get("data", {}).get("url") or res_data.get("BK9", {}).get("link")
                        title = res_data.get("title") or res_data.get("data", {}).get("title") or res_data.get("BK9", {}).get("title") or "YouTube Video"
                        
                        if dl_url:
                            return {
                                "success": True,
                                "title": title,
                                "thumbnail": "",
                                "download_url": dl_url,
                                "duration": 0
                            }
                except Exception:
                    continue 
                    
            return {"success": False, "error": "Bhai, ye APIs bhi filhal response nahi de rahin. Link try nahi ho saka."}

        # 3. Instagram / FB / Others Fallback
        ydl_opts = {'format': 'best[ext=mp4]/best', 'quiet': True, 'no_warnings': True, 'nocheckcertificate': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(decoded_url, download=False)
            return {
                "success": True,
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail', ''),
                "download_url": info.get('url'),
                "duration": info.get('duration', 0)
            }

    except Exception as e:
        return {"success": False, "error": str(e)}

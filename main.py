from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import urllib.parse
import urllib.request
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RapidAPI Credentials
RAPIDAPI_KEYS = [
    "7b3ce3bdb2mshbcfe925ba0ce6adp1433fdjsnae6124ee9ded"
]
RAPIDAPI_HOST = "youtube-video-fast-downloader-24-7.p.rapidapi.com"

def extract_youtube_id(url: str):
    regex = r"(?:v=|\/|youtu\.be\/|\/shorts\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

@app.get("/")
def home():
    return {"status": "active", "message": "API Backend is running!"}

@app.get("/api/extract")
def extract_video(url: str = Query(..., description="Video URL to extract")):
    try:
        decoded_url = urllib.parse.unquote(url).strip()

        # ----------------------------------------------------
        # 1. TikTok Extractor
        # ----------------------------------------------------
        if "tiktok.com" in decoded_url or "vt.tiktok.com" in decoded_url:
            tikwm_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(decoded_url)}"
            req = urllib.request.Request(tikwm_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode())
            if res_data.get("code") == 0 and "data" in res_data:
                data = res_data["data"]
                return {
                    "success": True,
                    "platform": "TikTok",
                    "title": data.get("title", "TikTok Video"),
                    "thumbnail": data.get("cover", ""),
                    "download_url": data.get("play"),
                    "duration": data.get("duration", 0)
                }

        # ----------------------------------------------------
        # 2. Instagram Extractor (Multi-Fallback Fix)
        # ----------------------------------------------------
        if "instagram.com" in decoded_url:
            clean_url = decoded_url.split("?")[0]
            
            # API 1: Fast Direct Downloader Engine
            try:
                fast_url = f"https://api.siputzx.my.id/api/d/ig?url={urllib.parse.quote(clean_url)}"
                req = urllib.request.Request(fast_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_data = json.loads(response.read().decode())
                    data = res_data.get("data", [])
                    if isinstance(data, list) and len(data) > 0:
                        dl_url = data[0].get("url")
                        if dl_url:
                            return {
                                "success": True,
                                "platform": "Instagram",
                                "title": "Instagram Video/Reel",
                                "thumbnail": data[0].get("thumbnail", ""),
                                "download_url": dl_url,
                                "duration": 0
                            }
            except Exception:
                pass

            # API 2: Cobalt Instance Backup
            try:
                cobalt_url = "https://api.cobalt.tools/"
                payload = json.dumps({"url": clean_url}).encode('utf-8')
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0'
                }
                req = urllib.request.Request(cobalt_url, data=payload, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_data = json.loads(response.read().decode())
                    if res_data.get("url"):
                        return {
                            "success": True,
                            "platform": "Instagram",
                            "title": "Instagram Video/Reel",
                            "thumbnail": "",
                            "download_url": res_data.get("url"),
                            "duration": 0
                        }
            except Exception:
                pass

            # API 3: Backup Scraper (Ryzendesu)
            try:
                ryzen_url = f"https://api.ryzendesu.vip/api/downloader/igdl?url={urllib.parse.quote(clean_url)}"
                req = urllib.request.Request(ryzen_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_data = json.loads(response.read().decode())
                    if isinstance(res_data, list) and len(res_data) > 0:
                        dl_url = res_data[0].get("url")
                        if dl_url and dl_url.startswith("http"):
                            return {
                                "success": True,
                                "platform": "Instagram",
                                "title": "Instagram Video/Reel",
                                "thumbnail": "",
                                "download_url": dl_url,
                                "duration": 0
                            }
            except Exception:
                pass

            return {"success": False, "error": "Instagram extraction failed. Link might be private or broken."}

        # ----------------------------------------------------
        # 3. YouTube Extractor (RapidAPI Key Support)
        # ----------------------------------------------------
        if "youtube.com" in decoded_url or "youtu.be" in decoded_url:
            video_id = extract_youtube_id(decoded_url)
            if not video_id:
                return {"success": False, "error": "Invalid YouTube URL format."}

            rapid_url = f"https://{RAPIDAPI_HOST}/download_video/{video_id}?quality=18"
            
            for key in RAPIDAPI_KEYS:
                headers = {
                    'x-rapidapi-host': RAPIDAPI_HOST,
                    'x-rapidapi-key': key,
                    'User-Agent': 'Mozilla/5.0'
                }

                try:
                    req = urllib.request.Request(rapid_url, headers=headers)
                    with urllib.request.urlopen(req, timeout=15) as response:
                        res_data = json.loads(response.read().decode())
                        dl_url = res_data.get("file") or res_data.get("download_url") or res_data.get("url")
                        
                        if dl_url:
                            return {
                                "success": True,
                                "platform": "YouTube",
                                "title": res_data.get("title", f"YouTube Video ({res_data.get('quality', '720p')})"),
                                "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                                "download_url": dl_url,
                                "comment": res_data.get("comment", "Link generated successfully!")
                            }
                except urllib.error.HTTPError as e:
                    if e.code in [403, 429]:
                        continue
                    else:
                        break
                except Exception:
                    continue

            return {"success": False, "error": "YouTube extraction failed or limit reached."}

        return {"success": False, "error": "Unsupported platform."}

    except Exception as e:
        return {"success": False, "error": f"Server Error: {str(e)}"}

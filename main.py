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
RAPIDAPI_KEY = "7b3ce3bdb2mshbcfe925ba0ce6adp1433fdjsnae6124ee9ded"
RAPIDAPI_HOST = "youtube-video-fast-downloader-24-7.p.rapidapi.com"

def extract_youtube_id(url: str):
    """YouTube URL se 11 characters ki Video ID alag karne ke liye"""
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
        # 2. Instagram Extractor
        # ----------------------------------------------------
        if "instagram.com" in decoded_url:
            ig_apis = [
                f"https://api.ryzendesu.vip/api/downloader/igdl?url={urllib.parse.quote(decoded_url)}",
                f"https://bk9.fun/download/instagram?url={urllib.parse.quote(decoded_url)}"
            ]
            for api_url in ig_apis:
                try:
                    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=10) as response:
                        res_data = json.loads(response.read().decode())
                        dl_url = None
                        if isinstance(res_data, list) and len(res_data) > 0:
                            dl_url = res_data[0].get("url") or res_data[0].get("download_url")
                        elif isinstance(res_data, dict):
                            dl_url = res_data.get("url") or res_data.get("data", [{}])[0].get("url") if isinstance(res_data.get("data"), list) else res_data.get("BK9", [{}])[0].get("BK9")

                        if dl_url:
                            return {
                                "success": True,
                                "platform": "Instagram",
                                "title": "Instagram Video/Reel",
                                "thumbnail": "",
                                "download_url": dl_url,
                                "duration": 0
                            }
                except Exception:
                    continue

        # ----------------------------------------------------
        # 3. YouTube Extractor (⚡ RapidAPI 24/7 Engine)
        # ----------------------------------------------------
        if "youtube.com" in decoded_url or "youtu.be" in decoded_url:
            video_id = extract_youtube_id(decoded_url)
            
            if not video_id:
                return {"success": False, "error": "Invalid YouTube URL format."}

            # RapidAPI Download Endpoint
            # Agar shorts ho ya normal video, download_video endpoint dono handle kar leta hai
            rapid_url = f"https://{RAPIDAPI_HOST}/download_video/{video_id}?quality=18"
            
            headers = {
                'x-rapidapi-host': RAPIDAPI_HOST,
                'x-rapidapi-key': RAPIDAPI_KEY,
                'User-Agent': 'Mozilla/5.0'
            }

            try:
                req = urllib.request.Request(rapid_url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as response:
                    res_data = json.loads(response.read().decode())
                    
                    # API Documentation ke mutabiq downloadable link "file" key mein hota hai
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
                    else:
                        error_msg = res_data.get("message") or res_data.get("error") or "Download URL missing in response."
                        return {"success": False, "error": error_msg}

            except urllib.error.HTTPError as e:
                error_body = e.read().decode()
                return {"success": False, "error": f"RapidAPI HTTP Error {e.code}: {error_body}"}
            except Exception as e:
                return {"success": False, "error": f"YouTube Processing Error: {str(e)}"}

        return {"success": False, "error": "Unsupported platform."}

    except Exception as e:
        return {"success": False, "error": f"Server Error: {str(e)}"}

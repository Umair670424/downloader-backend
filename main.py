from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import urllib.parse
import urllib.request
import json

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

        # ----------------------------------------------------
        # 1. TikTok Extractor (Free & Fast)
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
        # 2. Instagram Extractor (Anti-Ban APIs)
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
        # 3. YouTube Extractor (Multi-API Fallback Engine)
        # ----------------------------------------------------
        if "youtube.com" in decoded_url or "youtu.be" in decoded_url:
            clean_yt_url = decoded_url.split("?si=")[0]  # Clean tracking tags
            
            # Method A: High-speed Anti-Ban APIs
            yt_apis = [
                f"https://api.ryzendesu.vip/api/downloader/ytmp4?url={urllib.parse.quote(clean_yt_url)}",
                f"https://bk9.fun/download/youtube?url={urllib.parse.quote(clean_yt_url)}"
            ]
            
            for api_url in yt_apis:
                try:
                    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                    with urllib.request.urlopen(req, timeout=10) as response:
                        res_data = json.loads(response.read().decode())
                        
                        dl_url = res_data.get("url") or res_data.get("data", {}).get("url") or res_data.get("BK9", {}).get("link")
                        title = res_data.get("title") or res_data.get("data", {}).get("title") or res_data.get("BK9", {}).get("title") or "YouTube Video"
                        
                        if dl_url:
                            return {
                                "success": True,
                                "platform": "YouTube",
                                "title": title,
                                "thumbnail": "",
                                "download_url": dl_url,
                                "duration": 0
                            }
                except Exception:
                    continue

            # Method B: Updated Cobalt API payload fallback
            try:
                cobalt_url = "https://api.cobalt.tools/"
                payload = json.dumps({"url": clean_yt_url}).encode('utf-8')
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                }
                req = urllib.request.Request(cobalt_url, data=payload, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_data = json.loads(response.read().decode())
                    if res_data.get("url"):
                        return {
                            "success": True,
                            "platform": "YouTube",
                            "title": "YouTube Video",
                            "thumbnail": "",
                            "download_url": res_data.get("url"),
                            "duration": 0
                        }
            except Exception:
                pass

            return {"success": False, "error": "YouTube APIs error, please try again."}

        return {"success": False, "error": "Unsupported platform or link error."}

    except Exception as e:
        return {"success": False, "error": f"Extraction Error: {str(e)}"}

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
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
        # Decode URL if double encoded from Android
        decoded_url = urllib.parse.unquote(url).strip()

        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(decoded_url, download=False)
            
            # Find direct video URL
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

import os
import yt_dlp


def download_audio(url: str, output_dir: str) -> dict:
    """
    Download audio from a URL using yt-dlp and convert it to MP3.

    Returns a dict with:
      - title (str): human-readable title from the source
      - url   (str): original URL
      - file_path (str): path to the downloaded .mp3 file
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        # Download the best available audio stream
        "format": "bestaudio/best",
        # Convert to MP3 via ffmpeg (must be installed: brew install ffmpeg)
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        # Use the video/episode ID as the filename so the path is predictable
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        # Suppress progress bars — we print our own status in the pipeline
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    # Use the actual filepath reported by yt-dlp after post-processing.
    # Constructing it manually from info['id'] is unreliable — for podcast RSS
    # feeds the id can contain URL query parameters, producing an invalid path.
    file_path = info["requested_downloads"][-1]["filepath"]

    return {
        "title": info.get("title", "unknown"),
        "url": url,
        "file_path": file_path,
    }

import re
import json
import logging

import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}

TIKTOK_PATTERNS = [
    r"(https?://)?(www\.)?tiktok\.com/.+",
    r"(https?://)?(www\.)?vm\.tiktok\.com/.+",
    r"(https?://)?(www\.)?vt\.tiktok\.com/.+",
]
URL_RE = re.compile(r"^https?://[^\s<>{}`\"']+$")
MAX_URL_LEN = 2048


def is_tiktok_url(url: str) -> bool:
    url = url.strip()
    if len(url) > MAX_URL_LEN:
        return False
    return any(re.match(p, url) for p in TIKTOK_PATTERNS)


def resolve_redirect(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=15)
        return r.url
    except Exception as e:
        logger.warning("redirect resolve failed: %s", e)
        return url


def _common(d, url):
    formats = d.get("formats") or []
    formats.sort(key=lambda x: (x["has_video"], x["height"]), reverse=True)
    av = [f for f in formats if f["has_video"] and f["has_audio"]]
    audio = [f for f in formats if not f["has_video"] and f["has_audio"]]
    return {
        "ok": True, "title": d.get("title") or "", "uploader": d.get("uploader") or "",
        "duration": d.get("duration") or 0, "thumbnail": d.get("thumbnail") or "",
        "uploader_id": d.get("uploader_id") or "", "view_count": d.get("view_count") or 0,
        "like_count": d.get("like_count") or 0, "comment_count": d.get("comment_count") or 0,
        "webpage_url": d.get("webpage_url") or url, "formats": formats,
        "av_formats": av, "audio_formats": audio,
    }


def try_ytdlp(url: str):
    from yt_dlp import YoutubeDL
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True, "extract_flat": False}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        return None
    formats = []
    for f in info.get("formats", []):
        vcodec = f.get("vcodec"); acodec = f.get("acodec")
        has_video = bool(vcodec and vcodec != "none")
        has_audio = bool(acodec and acodec != "none")
        if not (has_video or has_audio):
            continue
        height = f.get("height") or 0
        filesize = f.get("filesize") or f.get("filesize_approx") or 0
        label = "Audio only" if not has_video else f"{height}p"
        formats.append({"format_id": f.get("format_id"), "ext": f.get("ext"), "label": label,
            "height": height, "width": f.get("width") or 0, "fps": f.get("fps") or 0,
            "filesize": filesize, "has_video": has_video, "has_audio": has_audio, "url": f.get("url")})
    thumb = info.get("thumbnail") or (info.get("thumbnails") or [{}])[-1].get("url", "")
    return _common({"title": info.get("title") or "", "uploader": info.get("uploader") or info.get("channel") or "",
        "duration": info.get("duration") or 0, "thumbnail": thumb, "uploader_id": info.get("uploader_id") or "",
        "view_count": info.get("view_count") or 0, "like_count": info.get("like_count") or 0,
        "comment_count": info.get("comment_count") or 0, "webpage_url": info.get("webpage_url") or url,
        "formats": formats}, url)


def try_tikwm(url: str):
    try:
        r = requests.post("https://www.tikwm.com/api/", data={"url": url, "hd": 1}, headers=HEADERS, timeout=25)
        data = r.json()
    except Exception as e:
        logger.warning("tikwm failed: %s", e)
        return None
    if not data or data.get("code") != 0 or not data.get("data"):
        return None
    d = data["data"]
    play = d.get("play") or ""; hdplay = d.get("hdplay") or ""; music = d.get("music") or ""
    cover = d.get("cover") or d.get("origin_cover") or ""
    width = d.get("width") or 0; height = d.get("height") or 0; duration = d.get("duration") or 0
    is_slideshow = (duration == 0) or (play and play == music)
    formats = []; seen = set()
    def add(fid, ext, label, h, w, size, hv, ha, u):
        if not u or u in seen: return
        seen.add(u)
        formats.append({"format_id": fid, "ext": ext, "label": label, "height": h, "width": w,
            "fps": 0, "filesize": size, "has_video": hv, "has_audio": ha, "url": u})
    if is_slideshow:
        if music: add("music", "mp3", "Audio (slideshow)", 0, 0, d.get("music_size") or 0, False, True, music)
    else:
        if play: add("play", "mp4", f"{height}p" if height else "SD", height, width, d.get("size") or 0, True, True, play)
        if hdplay: add("hdplay", "mp4", f"{height}p HD" if height else "HD", height, width, d.get("hd_size") or 0, True, True, hdplay)
        if music: add("music", "mp3", "Audio only", 0, 0, d.get("music_size") or 0, False, True, music)
    if not formats: return None
    author = d.get("author") or {}
    return _common({"title": d.get("title") or "", "uploader": author.get("nickname") or author.get("name") or "",
        "duration": duration, "thumbnail": cover, "uploader_id": author.get("unique_id") or "",
        "view_count": d.get("play_count") or 0, "like_count": d.get("digg_count") or 0,
        "comment_count": d.get("comment_count") or 0, "webpage_url": url, "formats": formats}, url)


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def fetch_info(request):
    if request.method == "OPTIONS":
        r = HttpResponse()
        r["Access-Control-Allow-Origin"] = "*"
        r["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        r["Access-Control-Allow-Headers"] = "Content-Type"
        return r
    try:
        body = request.body.decode("utf-8") or "{}"
        if len(body) > 4096:
            return JsonResponse({"ok": False, "error": "Request too large."}, status=413)
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)
    url = (data.get("url") or "").strip()
    if not url:
        return JsonResponse({"ok": False, "error": "Please provide a TikTok URL."}, status=400)
    if not url.startswith("http"):
        url = "https://" + url
    if not URL_RE.match(url) or not is_tiktok_url(url):
        return JsonResponse({"ok": False, "error": "This URL does not look like a TikTok link."}, status=400)
    if any(h in url for h in ("vt.tiktok.com", "vm.tiktok.com")):
        url = resolve_redirect(url)
    try:
        result = try_tikwm(url)
        if result and result.get("formats"):
            return JsonResponse(result)
    except Exception as e:
        logger.warning("tikwm failed: %s", e)
    try:
        result = try_ytdlp(url)
        if result and result.get("formats"):
            return JsonResponse(result)
    except Exception as e:
        logger.warning("yt-dlp failed: %s", e)
    return JsonResponse({"ok": False, "error": "Could not fetch this video. Try another TikTok link."}, status=502)


def index(request):
    resp = render(request, "downloader/index.html")
    resp["X-Content-Type-Options"] = "nosniff"
    resp["X-Frame-Options"] = "SAMEORIGIN"
    resp["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return resp

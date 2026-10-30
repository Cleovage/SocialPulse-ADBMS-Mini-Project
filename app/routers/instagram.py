from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from app.database import Database, serialize_doc
from app.services.instagram_service import InstagramService

router = APIRouter(prefix="/api/instagram", tags=["Instagram Live"])
logger = logging.getLogger("socialpulse.instagram")


class ApiKeyConfigPayload(BaseModel):
    api_key: Optional[str] = None


@router.get("/profile/{username}")
async def get_instagram_profile(
    username: str,
    force_refresh: bool = Query(False, description="Bypass cache and force live re-fetch")
):
    """
    Look up a real Instagram profile with multi-tier fallback:
    Tier 1: MongoDB Cache (24h TTL)
    Tier 2: RapidAPI (if key configured)
    Tier 3: Direct Public Crawler Scraper (zero config)
    Tier 4: Synthetic Fallback (influencers database)
    """
    clean_user = username.strip().lstrip("@")
    if not clean_user:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": "Username cannot be empty",
                "detail": "Username cannot be empty",
                "suggest_synthetic": True
            }
        )

    result = await InstagramService.lookup_profile(
        username=clean_user,
        force_refresh=force_refresh
    )

    if result.get("status") == "error":
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": result.get("message", "Profile not found"),
                "detail": result.get("message", "Profile not found"),
                "suggest_synthetic": result.get("suggest_synthetic", True)
            }
        )

    return result


@router.get("/cached")
async def get_cached_profiles(
    limit: int = Query(20, ge=1, le=100, description="Max number of cached profiles to return")
):
    """
    Retrieve recently searched and cached Instagram profiles from MongoDB (instagram_profiles),
    sorted by cached_at descending.
    """
    db = Database.db
    cursor = db["instagram_profiles"].find().sort("cached_at", -1).limit(limit)
    cached_list = list(cursor)
    return {
        "total": len(cached_list),
        "profiles": serialize_doc(cached_list)
    }


@router.get("/config")
async def get_instagram_config():
    """
    Return Instagram data source configuration status, masked API key, and active scraper mode.
    """
    return InstagramService.get_config()


@router.post("/config")
async def update_instagram_config(payload: ApiKeyConfigPayload):
    """
    Update runtime RapidAPI key for Instagram scraping.
    """
    InstagramService.set_api_key(payload.api_key)
    cfg = InstagramService.get_config()
    return {
        "status": "updated",
        "has_api_key": cfg["has_api_key"],
        "active_mode": cfg["active_mode"]
    }


@router.get("/proxy-image")
async def proxy_image(url: str = Query(..., description="External image URL to proxy")):
    """
    Proxy image endpoint to bypass CORS and Referrer restrictions for Instagram CDN images.
    """
    import httpx
    from fastapi.responses import Response

    if not url.startswith("http://") and not url.startswith("https://"):
        return JSONResponse(status_code=400, content={"error": "Invalid URL"})

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "image/jpeg")
                return Response(
                    content=resp.content,
                    media_type=content_type,
                    headers={"Cache-Control": "public, max-age=86400"}
                )
            else:
                return JSONResponse(status_code=resp.status_code, content={"error": "Remote image fetch failed"})
    except Exception as e:
        logger.warning(f"Failed to proxy image {url[:80]}: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to proxy image"})

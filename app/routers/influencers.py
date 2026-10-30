from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from typing import Optional, List
from datetime import datetime, timezone
from app.database import Database, serialize_doc
from app.models.influencer import InfluencerCreate
import logging

router = APIRouter(prefix="/api/influencers", tags=["Influencers"])
logger = logging.getLogger("socialpulse.influencers")

@router.get("")
async def get_influencers(
    search: Optional[str] = None,
    niche: Optional[str] = None,
    platform: Optional[str] = None,
    tier: Optional[str] = None,
    min_followers: Optional[int] = None,
    max_followers: Optional[int] = None,
    min_er: Optional[float] = None,
    min_credibility: Optional[int] = None,
    sort_by: str = "metrics.followers_count",
    sort_order: int = -1,
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Search and filter influencers using compound MongoDB queries.
    Demonstrates B-Tree Compound index scan on {niche: 1, 'metrics.followers_count': -1}
    """
    db = Database.db
    query = {}

    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"handle": {"$regex": search, "$options": "i"}},
            {"bio": {"$regex": search, "$options": "i"}}
        ]

    if niche and niche != "All":
        query["niche"] = niche

    if platform and platform != "All":
        query["platform_primary"] = platform

    if tier and tier != "All":
        query["tier"] = tier

    follower_filter = {}
    if min_followers is not None:
        follower_filter["$gte"] = min_followers
    if max_followers is not None:
        follower_filter["$lte"] = max_followers
    if follower_filter:
        query["metrics.followers_count"] = follower_filter

    if min_er is not None:
        query["metrics.engagement_rate"] = {"$gte": min_er}

    if min_credibility is not None:
        query["metrics.credibility_score"] = {"$gte": min_credibility}

    total_count = db["influencers"].count_documents(query)
    cursor = db["influencers"].find(query).sort(sort_by, sort_order).skip(skip).limit(limit)
    influencers = list(cursor)

    return {
        "total": total_count,
        "limit": limit,
        "skip": skip,
        "data": serialize_doc(influencers)
    }

@router.get("/compare")
async def compare_influencers(handles: str = Query(..., description="Comma separated handles, e.g. @elena_ai_tech,@chen_codes")):
    """
    Head-to-head comparison between 2 or more influencers.
    Returns metrics, audience demographics, and recent post engagement side-by-side.
    """
    db = Database.db
    handle_list = [h.strip() for h in handles.split(",") if h.strip()]
    if len(handle_list) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 handles to compare.")

    influencers = list(db["influencers"].find({"handle": {"$in": handle_list}}))
    if not influencers:
        raise HTTPException(status_code=404, detail="No matching influencers found.")

    # Fetch recent average metrics from posts for each influencer
    comparison_data = []
    for inf in influencers:
        recent_posts = list(
            db["posts"].find({"influencer_handle": inf["handle"]})
            .sort("published_at", -1)
            .limit(10)
        )
        total_likes = sum(p["metrics"]["likes"] for p in recent_posts)
        total_comments = sum(p["metrics"]["comments"] for p in recent_posts)
        avg_likes = total_likes // max(1, len(recent_posts))
        avg_comments = total_comments // max(1, len(recent_posts))

        comparison_data.append({
            "influencer": serialize_doc(inf),
            "recent_posts_sample": len(recent_posts),
            "computed_recent_avg_likes": avg_likes,
            "computed_recent_avg_comments": avg_comments
        })

    return {
        "compared_count": len(comparison_data),
        "comparison": comparison_data
    }

@router.get("/{handle_or_id}")
async def get_influencer_detail(handle_or_id: str):
    """
    Get deep profile breakdown for an influencer:
    Includes audience demographics, rates, collaboration network, and recent 10 posts.
    """
    db = Database.db
    query = {}
    if ObjectId.is_valid(handle_or_id):
        query["$or"] = [{"_id": ObjectId(handle_or_id)}, {"handle": handle_or_id}]
    else:
        query["handle"] = handle_or_id

    inf = db["influencers"].find_one(query)
    if not inf:
        raise HTTPException(status_code=404, detail="Influencer not found.")

    # Fetch recent posts
    posts = list(
        db["posts"].find({"influencer_handle": inf["handle"]})
        .sort("published_at", -1)
        .limit(12)
    )

    # Fetch post type breakdown aggregation
    post_type_agg = list(db["posts"].aggregate([
        {"$match": {"influencer_handle": inf["handle"]}},
        {"$group": {"_id": "$post_type", "count": {"$sum": 1}, "avg_likes": {"$avg": "$metrics.likes"}}}
    ]))

    return {
        "influencer": serialize_doc(inf),
        "recent_posts": serialize_doc(posts),
        "content_breakdown": serialize_doc(post_type_agg)
    }

from pymongo.errors import DuplicateKeyError

@router.post("")
async def create_influencer(payload: InfluencerCreate):
    """
    Insert a new influencer document. Enforces unique index constraint on handle.
    """
    db = Database.db
    doc = payload.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)

    # Ensure location_geo matches 2dsphere index requirements
    if doc.get("location_geo") is None:
        if "location" in doc and doc["location"] and doc["location"].get("coordinates"):
            doc["location_geo"] = doc["location"]["coordinates"]
        else:
            doc["location_geo"] = {
                "type": "Point",
                "coordinates": [-122.4194, 37.7749]
            }
    
    # Check if handle already exists
    existing = db["influencers"].find_one({"handle": doc["handle"]})
    if existing:
        raise HTTPException(status_code=400, detail=f"Influencer handle '{doc['handle']}' already exists.")

    try:
        result = db["influencers"].insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_doc(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail=f"Influencer handle '{doc['handle']}' already exists.")

@router.delete("/{handle_or_id}")
async def delete_influencer(handle_or_id: str):
    """
    Delete an influencer and cascadingly remove or dissociate their posts.
    """
    db = Database.db
    query = {"_id": ObjectId(handle_or_id)} if ObjectId.is_valid(handle_or_id) else {"handle": handle_or_id}
    
    inf = db["influencers"].find_one(query)
    if not inf:
        raise HTTPException(status_code=404, detail="Influencer not found.")

    db["influencers"].delete_one({"_id": inf["_id"]})
    deleted_posts = db["posts"].delete_many({"influencer_handle": inf["handle"]})

    return {
        "message": f"Successfully deleted influencer {inf['handle']}",
        "cascaded_posts_deleted": deleted_posts.deleted_count
    }

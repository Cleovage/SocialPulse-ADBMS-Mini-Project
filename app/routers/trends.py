from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import Database, serialize_doc
import logging

router = APIRouter(prefix="/api/trends", tags=["Trends & Topics"])
logger = logging.getLogger("socialpulse.trends")

@router.get("")
async def get_trends(
    category: Optional[str] = None,
    lifecycle_status: Optional[str] = None,
    sort_by: str = "velocity_score",
    sort_order: int = -1,
    limit: int = Query(25, ge=1, le=100)
):
    """
    List trending topics and hashtags sorted by velocity or viral index.
    Demonstrates compound index on {category: 1, velocity_score: -1}
    """
    db = Database.db
    query = {}
    if category and category != "All":
        query["category"] = category
    if lifecycle_status and lifecycle_status != "All":
        query["lifecycle_status"] = lifecycle_status

    trends = list(db["trends"].find(query).sort(sort_by, sort_order).limit(limit))
    return {
        "count": len(trends),
        "data": serialize_doc(trends)
    }

@router.get("/{hashtag}")
async def get_trend_detail(hashtag: str):
    """
    Deep-dive into a specific trend:
    - Hourly volume progression over 24h
    - Platform share distribution
    - Top associated posts matching the hashtag (utilizing Multikey index on posts.hashtags)
    """
    db = Database.db
    clean_tag = hashtag if hashtag.startswith("#") else f"#{hashtag}"

    trend = db["trends"].find_one({"hashtag": clean_tag})
    if not trend:
        # Fallback search without #
        trend = db["trends"].find_one({"hashtag": {"$regex": f"^{hashtag}$", "$options": "i"}})
        if not trend:
            raise HTTPException(status_code=404, detail="Trend not found.")

    # Fetch top posts with this hashtag using multikey index
    posts = list(
        db["posts"].find({"hashtags": trend["hashtag"]})
        .sort("metrics.viral_score", -1)
        .limit(8)
    )

    return {
        "trend": serialize_doc(trend),
        "viral_posts": serialize_doc(posts)
    }

@router.get("/analytics/category-velocity")
async def get_category_velocity_stats():
    """
    Aggregation pipeline grouping trends by category to compute average velocity and viral index.
    """
    db = Database.db
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "avg_velocity": {"$avg": "$velocity_score"},
                "avg_viral_index": {"$avg": "$viral_index"},
                "total_volume": {"$sum": "$volume_24h"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"avg_velocity": -1}}
    ]
    results = list(db["trends"].aggregate(pipeline))
    return {
        "categories": [
            {
                "category": r["_id"],
                "avg_velocity": round(r["avg_velocity"], 1),
                "avg_viral_index": round(r["avg_viral_index"], 1),
                "total_volume": r["total_volume"],
                "trends_count": r["count"]
            }
            for r in results
        ]
    }

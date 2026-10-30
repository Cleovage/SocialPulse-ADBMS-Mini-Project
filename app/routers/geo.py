from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.database import Database, serialize_doc
import logging

router = APIRouter(prefix="/api/geo", tags=["Geospatial Analytics ($geoNear)"])
logger = logging.getLogger("socialpulse.geo")

GLOBAL_HUBS = [
    {"city": "San Francisco", "country": "USA", "lng": -122.4194, "lat": 37.7749},
    {"city": "New York", "country": "USA", "lng": -74.0060, "lat": 40.7128},
    {"city": "London", "country": "UK", "lng": -0.1278, "lat": 51.5074},
    {"city": "Tokyo", "country": "Japan", "lng": 139.6917, "lat": 35.6895},
    {"city": "Mumbai", "country": "India", "lng": 72.8777, "lat": 19.0760},
    {"city": "Berlin", "country": "Germany", "lng": 13.4050, "lat": 52.5200},
    {"city": "Paris", "country": "France", "lng": 2.3522, "lat": 48.8566},
    {"city": "Dubai", "country": "UAE", "lng": 55.2708, "lat": 25.2048},
    {"city": "Singapore", "country": "Singapore", "lng": 103.8198, "lat": 1.3521},
    {"city": "Sydney", "country": "Australia", "lng": 151.2093, "lat": -33.8688}
]

@router.get("/hubs")
async def get_tracked_hubs():
    """Returns list of global creator cities with coordinates"""
    return GLOBAL_HUBS

@router.get("/near")
async def get_posts_near_location(
    lng: float = Query(..., ge=-180.0, le=180.0, description="Longitude between -180 and 180, e.g. -122.4194"),
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude between -90 and 90, e.g. 37.7749"),
    max_distance_km: float = Query(500.0, gt=0.0, le=20000.0, description="Max radius in kilometers (> 0)"),
    limit: int = Query(15, ge=1, le=50)
):
    """
    Demonstrates MongoDB $geoNear Aggregation Stage & 2dsphere index:
    Calculates spherical distance from coordinates and returns closest social posts.
    """
    db = Database.db
    max_distance_meters = max_distance_km * 1000

    pipeline = [
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "distanceField": "distance_meters",
                "maxDistance": max_distance_meters,
                "spherical": True
            }
        },
        {
            "$project": {
                "influencer_handle": 1,
                "platform": 1,
                "content": 1,
                "hashtags": 1,
                "metrics": 1,
                "sentiment": 1,
                "location": 1,
                "distance_km": {"$round": [{"$divide": ["$distance_meters", 1000]}, 2]}
            }
        },
        {"$limit": limit}
    ]

    try:
        results = list(db["posts"].aggregate(pipeline))
        return {
            "query_center": {"longitude": lng, "latitude": lat},
            "radius_km": max_distance_km,
            "total_found": len(results),
            "posts": serialize_doc(results)
        }
    except Exception as e:
        logger.error(f"Geo query failed: {e}")
        raise HTTPException(status_code=400, detail=f"Geo aggregation error: {str(e)}")

@router.get("/influencer-clusters")
async def get_influencer_geographic_clusters():
    """
    Groups influencers by city and country to display map pins with creator counts and average ER.
    """
    db = Database.db
    pipeline = [
        {
            "$group": {
                "_id": {
                    "city": "$location.city",
                    "country": "$location.country"
                },
                "coordinates": {"$first": "$location_geo.coordinates"},
                "creators_count": {"$sum": 1},
                "total_followers": {"$sum": "$metrics.followers_count"},
                "avg_engagement_rate": {"$avg": "$metrics.engagement_rate"},
                "top_handles": {"$push": "$handle"}
            }
        },
        {"$sort": {"creators_count": -1}}
    ]
    clusters = list(db["influencers"].aggregate(pipeline))
    formatted = [
        {
            "city": c["_id"]["city"],
            "country": c["_id"]["country"],
            "coordinates": c.get("coordinates") or [0.0, 0.0],
            "creators_count": c["creators_count"],
            "total_followers": c["total_followers"],
            "avg_engagement_rate": round(c["avg_engagement_rate"], 2),
            "top_handles": c["top_handles"][:3]
        }
        for c in clusters
        if c.get("_id") and c["_id"].get("city")
    ]
    return formatted

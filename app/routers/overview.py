from fastapi import APIRouter
from app.database import Database, serialize_doc
import logging

router = APIRouter(prefix="/api/overview", tags=["Overview Dashboard"])
logger = logging.getLogger("socialpulse.overview")

@router.get("/stats")
async def get_overview_stats():
    """
    Returns aggregated KPIs for the high-level platform dashboard:
    Total influencers, total posts, active trends, avg engagement rate,
    breakdown by platform, breakdown by niche, and top 5 viral posts.
    """
    db = Database.db
    
    # 1. Total counts
    total_influencers = db["influencers"].count_documents({})
    total_posts = db["posts"].count_documents({})
    total_trends = db["trends"].count_documents({})
    total_campaigns = db["campaigns"].count_documents({})

    # 2. Aggregation for average engagement rate & credibility score
    inf_avg_pipeline = [
        {
            "$group": {
                "_id": None,
                "avg_engagement_rate": {"$avg": "$metrics.engagement_rate"},
                "avg_credibility_score": {"$avg": "$metrics.credibility_score"},
                "total_audience_reach": {"$sum": "$metrics.followers_count"}
            }
        }
    ]
    inf_agg = list(db["influencers"].aggregate(inf_avg_pipeline))
    avg_er = round(inf_agg[0]["avg_engagement_rate"], 2) if inf_agg else 0.0
    avg_cred = round(inf_agg[0]["avg_credibility_score"], 1) if inf_agg else 0.0
    total_reach = inf_agg[0]["total_audience_reach"] if inf_agg else 0

    # 3. Platform Distribution Aggregation
    platform_pipeline = [
        {
            "$group": {
                "_id": "$platform_primary",
                "count": {"$sum": 1},
                "total_followers": {"$sum": "$metrics.followers_count"}
            }
        },
        {"$sort": {"count": -1}}
    ]
    platform_stats = list(db["influencers"].aggregate(platform_pipeline))

    # 4. Niche Distribution Aggregation
    niche_pipeline = [
        {
            "$group": {
                "_id": "$niche",
                "count": {"$sum": 1},
                "avg_er": {"$avg": "$metrics.engagement_rate"}
            }
        },
        {"$sort": {"count": -1}}
    ]
    niche_stats = [
        {
            "niche": item["_id"],
            "count": item["count"],
            "avg_er": round(item["avg_er"], 2)
        }
        for item in db["influencers"].aggregate(niche_pipeline)
    ]

    # 5. Top 5 Viral Posts (Leveraging compound index on metrics.viral_score)
    top_posts = list(
        db["posts"].find({}, {
            "influencer_handle": 1,
            "platform": 1,
            "content": 1,
            "metrics": 1,
            "sentiment": 1,
            "published_at": 1
        })
        .sort("metrics.viral_score", -1)
        .limit(5)
    )

    # 6. Top 5 Surging Trends
    top_trends = list(
        db["trends"].find({}, {
            "hashtag": 1,
            "topic": 1,
            "category": 1,
            "velocity_score": 1,
            "viral_index": 1,
            "volume_24h": 1,
            "lifecycle_status": 1
        })
        .sort("velocity_score", -1)
        .limit(5)
    )

    return {
        "kpis": {
            "total_influencers": total_influencers,
            "total_posts": total_posts,
            "total_trends": total_trends,
            "total_campaigns": total_campaigns,
            "avg_engagement_rate": avg_er,
            "avg_credibility_score": avg_cred,
            "total_audience_reach": total_reach
        },
        "platform_breakdown": serialize_doc(platform_stats),
        "niche_breakdown": niche_stats,
        "top_viral_posts": serialize_doc(top_posts),
        "top_surging_trends": serialize_doc(top_trends)
    }

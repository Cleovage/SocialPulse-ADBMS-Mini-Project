from fastapi import APIRouter, HTTPException, Query, Body
from bson import ObjectId
import time
from app.database import Database, serialize_doc
from app.seed_data import seed_database
import logging

router = APIRouter(prefix="/api/adbms-lab", tags=["ADBMS Aggregations & Query Lab"])
logger = logging.getLogger("socialpulse.adbms_lab")

@router.get("/pipelines/bucketing")
async def pipeline_influencer_bucketing():
    """
    ADBMS Pipeline 1: Data Bucketing & Tier Aggregation ($bucketAuto)
    Categorizes influencers into dynamic follower tiers, computing averages for ER, credibility, and rates.
    """
    db = Database.db
    pipeline = [
        {
            "$bucket": {
                "groupBy": "$metrics.followers_count",
                "boundaries": [0, 10000, 100000, 500000, 1000000, 10000000],
                "default": "Other",
                "output": {
                    "count": {"$sum": 1},
                    "avg_engagement_rate": {"$avg": "$metrics.engagement_rate"},
                    "avg_credibility_score": {"$avg": "$metrics.credibility_score"},
                    "avg_post_rate_usd": {"$avg": "$collaboration_rates.post_rate_usd"},
                    "handles": {"$push": "$handle"}
                }
            }
        }
    ]

    tier_labels = {
        0: "Nano (1K - 10K)",
        10000: "Micro (10K - 100K)",
        100000: "Mid-Tier (100K - 500K)",
        500000: "Macro (500K - 1M)",
        1000000: "Mega (1M+)"
    }

    start_time = time.perf_counter()
    raw_results = list(db["influencers"].aggregate(pipeline))
    exec_ms = round((time.perf_counter() - start_time) * 1000, 2)

    formatted = []
    for r in raw_results:
        boundary = r["_id"]
        label = tier_labels.get(boundary, f"Range: {boundary}+")
        formatted.append({
            "tier_label": label,
            "boundary_min": boundary,
            "creator_count": r["count"],
            "avg_engagement_rate": round(r["avg_engagement_rate"], 2),
            "avg_credibility": round(r["avg_credibility_score"], 1),
            "avg_post_rate_usd": round(r["avg_post_rate_usd"], 2),
            "sample_creators": r["handles"][:4]
        })

    return {
        "title": "Pipeline 1: Follower Bucketing Tier Analysis ($bucket)",
        "execution_time_ms": exec_ms,
        "stages_used": ["$bucket", "$sum", "$avg", "$push"],
        "pipeline_code": pipeline,
        "results": formatted
    }

@router.get("/pipelines/facet-multidimensional")
async def pipeline_facet_multidimensional():
    """
    ADBMS Pipeline 2: Multi-Dimensional Analytics via $facet
    Executes multiple independent analytical sub-pipelines in a single database round-trip:
    - Facet A: Top 5 Viral Hashtags
    - Facet B: Top Positive Sentiment Content
    - Facet C: Content Type Breakdown
    """
    db = Database.db
    pipeline = [
        {
            "$facet": {
                "top_viral_tags": [
                    {"$unwind": "$hashtags"},
                    {
                        "$group": {
                            "_id": "$hashtags",
                            "frequency": {"$sum": 1},
                            "avg_viral_score": {"$avg": "$metrics.viral_score"},
                            "total_likes": {"$sum": "$metrics.likes"}
                        }
                    },
                    {"$sort": {"avg_viral_score": -1}},
                    {"$limit": 5}
                ],
                "top_positive_content": [
                    {"$match": {"sentiment.label": "Positive"}},
                    {"$sort": {"sentiment.score": -1, "metrics.likes": -1}},
                    {"$limit": 5},
                    {
                        "$project": {
                            "influencer_handle": 1,
                            "platform": 1,
                            "content": 1,
                            "sentiment_score": "$sentiment.score",
                            "viral_score": "$metrics.viral_score"
                        }
                    }
                ],
                "content_format_performance": [
                    {
                        "$group": {
                            "_id": "$post_type",
                            "total_posts": {"$sum": 1},
                            "avg_likes": {"$avg": "$metrics.likes"},
                            "avg_comments": {"$avg": "$metrics.comments"},
                            "avg_shares": {"$avg": "$metrics.shares"}
                        }
                    },
                    {"$sort": {"avg_likes": -1}}
                ]
            }
        }
    ]

    start_time = time.perf_counter()
    raw_results = list(db["posts"].aggregate(pipeline))
    exec_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "title": "Pipeline 2: Multi-Dimensional Faceted Aggregation ($facet, $unwind, $group)",
        "execution_time_ms": exec_ms,
        "stages_used": ["$facet", "$unwind", "$match", "$group", "$sort", "$project"],
        "pipeline_code": pipeline,
        "results": serialize_doc(raw_results[0]) if raw_results else {}
    }

@router.get("/pipelines/graph-lookup")
async def pipeline_graph_lookup(
    start_handle: str = Query("@elena_ai_tech", description="Root creator handle to traverse network from"),
    max_depth: int = Query(2, ge=1, le=4, description="Max traversal depth in social graph")
):
    """
    ADBMS Pipeline 3: Recursive Graph Traversal ($graphLookup)
    Discovers the interconnected social network of influencers traversing 'network.collaborates_with'
    up to N levels deep.
    """
    db = Database.db
    pipeline = [
        {"$match": {"handle": start_handle}},
        {
            "$graphLookup": {
                "from": "influencers",
                "startWith": "$network.collaborates_with",
                "connectFromField": "network.collaborates_with",
                "connectToField": "handle",
                "as": "collaboration_network",
                "maxDepth": max_depth,
                "depthField": "hops"
            }
        },
        {
            "$project": {
                "handle": 1,
                "name": 1,
                "niche": 1,
                "platform_primary": 1,
                "followers": "$metrics.followers_count",
                "direct_collaborators": "$network.collaborates_with",
                "network_size": {"$size": "$collaboration_network"},
                "collaboration_network": {
                    "$map": {
                        "input": "$collaboration_network",
                        "as": "node",
                        "in": {
                            "handle": "$$node.handle",
                            "name": "$$node.name",
                            "niche": "$$node.niche",
                            "platform": "$$node.platform_primary",
                            "followers": "$$node.metrics.followers_count",
                            "hops": "$$node.hops"
                        }
                    }
                }
            }
        }
    ]

    start_time = time.perf_counter()
    raw_results = list(db["influencers"].aggregate(pipeline))
    exec_ms = round((time.perf_counter() - start_time) * 1000, 2)

    if not raw_results:
        raise HTTPException(status_code=404, detail=f"Creator {start_handle} not found.")

    node_data = raw_results[0]
    return {
        "title": f"Pipeline 3: Recursive Social Collaboration Network ($graphLookup) - Depth {max_depth}",
        "execution_time_ms": exec_ms,
        "stages_used": ["$match", "$graphLookup", "$project", "$map"],
        "pipeline_code": pipeline,
        "results": serialize_doc(node_data)
    }

@router.get("/pipelines/relational-lookup")
async def pipeline_relational_lookup():
    """
    ADBMS Pipeline 4: Cross-Collection Relational Join ($lookup)
    Joins 'campaigns' with 'influencers' on handle, computing audience overlap and ROI efficiency.
    """
    db = Database.db
    pipeline = [
        {"$match": {"status": "Active"}},
        {"$unwind": "$assigned_influencers"},
        {
            "$lookup": {
                "from": "influencers",
                "localField": "assigned_influencers.handle",
                "foreignField": "handle",
                "as": "creator_profile"
            }
        },
        {"$unwind": "$creator_profile"},
        {
            "$group": {
                "_id": {
                    "campaign_id": "$_id",
                    "brand_name": "$brand_name",
                    "campaign_title": "$campaign_title",
                    "total_budget": "$total_budget",
                    "spent_budget": "$spent_budget",
                    "calculated_roi": "$performance_kpis.calculated_roi"
                },
                "total_collaborators": {"$sum": 1},
                "total_combined_followers": {"$sum": "$creator_profile.metrics.followers_count"},
                "avg_creator_er": {"$avg": "$creator_profile.metrics.engagement_rate"},
                "avg_creator_credibility": {"$avg": "$creator_profile.metrics.credibility_score"},
                "collaborators": {
                    "$push": {
                        "handle": "$creator_profile.handle",
                        "followers": "$creator_profile.metrics.followers_count",
                        "agreed_fee": "$assigned_influencers.agreed_fee"
                    }
                }
            }
        },
        {"$sort": {"_id.calculated_roi": -1}}
    ]

    start_time = time.perf_counter()
    raw_results = list(db["campaigns"].aggregate(pipeline))
    exec_ms = round((time.perf_counter() - start_time) * 1000, 2)

    formatted = [
        {
            "brand": r["_id"]["brand_name"],
            "title": r["_id"]["campaign_title"],
            "total_budget": r["_id"]["total_budget"],
            "spent_budget": r["_id"]["spent_budget"],
            "calculated_roi": r["_id"]["calculated_roi"],
            "total_collaborators": r["total_collaborators"],
            "total_combined_reach": r["total_combined_followers"],
            "avg_engagement_rate": round(r["avg_creator_er"], 2),
            "avg_credibility": round(r["avg_creator_credibility"], 1),
            "creators": r["collaborators"]
        }
        for r in raw_results
    ]

    return {
        "title": "Pipeline 4: Cross-Collection Relational Join ($lookup & $unwind)",
        "execution_time_ms": exec_ms,
        "stages_used": ["$match", "$unwind", "$lookup", "$group", "$sort"],
        "pipeline_code": pipeline,
        "results": formatted
    }

@router.get("/benchmarks/explain-plan")
async def benchmark_explain_plan(
    platform: str = "YouTube",
    min_likes: int = 50000
):
    """
    ADBMS Query Optimization & Explain Plan Lab:
    Executes real MongoDB explain('executionStats') on:
    1. Query WITH compound B-tree index (idx_platform_likes_date_compound) -> IXSCAN
    2. Query WITHOUT index (forced Collection Scan using hint({$natural: 1})) -> COLLSCAN
    Returns side-by-side performance metrics: execution time, docs scanned vs returned, winning stages!
    """
    db = Database.db
    posts_col = db["posts"]

    filter_query = {
        "platform": platform,
        "metrics.likes": {"$gte": min_likes}
    }

    # 1. Indexed execution explain
    indexed_explain = posts_col.find(filter_query).sort([("metrics.likes", -1)]).explain()["executionStats"]

    # 2. Unindexed / Forced collection scan execution explain
    unindexed_explain = posts_col.find(filter_query).hint([("$natural", 1)]).explain()["executionStats"]

    # Extract indexed stats
    idx_time = indexed_explain.get("executionTimeMillis", 0)
    idx_docs_examined = indexed_explain.get("totalDocsExamined", 0)
    idx_keys_examined = indexed_explain.get("totalKeysExamined", 0)
    idx_returned = indexed_explain.get("nReturned", 0)
    idx_stage = indexed_explain.get("executionStages", {}).get("stage", "IXSCAN/FETCH")

    # Extract unindexed stats
    coll_time = unindexed_explain.get("executionTimeMillis", 0)
    coll_docs_examined = unindexed_explain.get("totalDocsExamined", 0)
    coll_returned = unindexed_explain.get("nReturned", 0)
    coll_stage = unindexed_explain.get("executionStages", {}).get("stage", "COLLSCAN")

    # Calculate optimization gains
    docs_saved = max(0, coll_docs_examined - idx_docs_examined)
    efficiency_gain_pct = round((docs_saved / max(1, coll_docs_examined)) * 100, 2) if coll_docs_examined > 0 else 0

    return {
        "benchmark_summary": {
            "query_predicate": filter_query,
            "indexed_run": {
                "execution_stage": idx_stage,
                "index_used": "idx_platform_likes_date_compound",
                "execution_time_ms": idx_time,
                "docs_examined": idx_docs_examined,
                "keys_examined": idx_keys_examined,
                "docs_returned": idx_returned
            },
            "unindexed_run": {
                "execution_stage": coll_stage,
                "index_used": "None (Full Collection Scan - COLLSCAN)",
                "execution_time_ms": coll_time,
                "docs_examined": coll_docs_examined,
                "keys_examined": 0,
                "docs_returned": coll_returned
            },
            "adbms_performance_gain": {
                "unnecessary_docs_scanned_avoided": docs_saved,
                "scan_reduction_pct": f"{efficiency_gain_pct}%",
                "speedup_verdict": "B-Tree Compound index avoids scanning the entire collection, jumping directly to matching index nodes."
            }
        },
        "raw_explain_indexed": indexed_explain,
        "raw_explain_unindexed": unindexed_explain
    }

@router.get("/database-stats")
async def get_database_stats():
    """
    Returns live MongoDB database statistics and active collection indexes.
    """
    db = Database.db
    collections = db.list_collection_names()
    
    col_details = []
    for col_name in ["influencers", "posts", "trends", "campaigns", "live_trend_events"]:
        if col_name in collections:
            col = db[col_name]
            count = col.count_documents({})
            indexes = col.index_information()
            formatted_indexes = []
            for name, info in indexes.items():
                formatted_indexes.append({
                    "name": name,
                    "key": info.get("key"),
                    "unique": info.get("unique", False),
                    "expireAfterSeconds": info.get("expireAfterSeconds", None),
                    "partialFilterExpression": info.get("partialFilterExpression", None)
                })

            col_details.append({
                "collection": col_name,
                "document_count": count,
                "index_count": len(indexes),
                "indexes": formatted_indexes
            })

    return {
        "database_name": db.name,
        "collections": col_details
    }

@router.post("/reseed")
async def trigger_reseed():
    """Reset and re-populate MongoDB with fresh synthetic benchmark data"""
    res = seed_database(force=True)
    return {
        "message": "Database successfully reseeded!",
        "details": res
    }

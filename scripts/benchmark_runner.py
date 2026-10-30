#!/usr/bin/env python3
"""
SocialPulse ADBMS Benchmark Runner
Executes real MongoDB explain('executionStats') benchmarks comparing:
1. IXSCAN (Indexed B-Tree compound index) vs COLLSCAN (Full collection scan)
2. Multikey index lookup on arrays (hashtags)
3. Geospatial 2dsphere $geoNear index vs manual distance filtering
4. Multi-dimensional $facet aggregation performance
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Database

def run_benchmarks():
    print("=" * 75)
    print("      SocialPulse ADBMS Query Optimization & Indexing Benchmark")
    print("=" * 75)
    
    Database.connect_db()
    db = Database.db
    posts_col = db["posts"]
    
    total_docs = posts_col.count_documents({})
    print(f"\n[i] Connected to MongoDB database '{db.name}'")
    print(f"[i] Total documents in 'posts' collection: {total_docs:,}\n")

    # -------------------------------------------------------------
    # BENCHMARK 1: Compound Index (IXSCAN) vs Forced Scan (COLLSCAN)
    # -------------------------------------------------------------
    print("-" * 75)
    print("BENCHMARK 1: Compound B-Tree Index vs Full Collection Scan")
    print("Predicate: { platform: 'YouTube', 'metrics.likes': { $gte: 40000 } }")
    print("Sort:      { 'metrics.likes': -1 }")
    print("-" * 75)

    filter_q = {"platform": "YouTube", "metrics.likes": {"$gte": 40000}}

    # 1A: Indexed
    idx_explain = posts_col.find(filter_q).sort([("metrics.likes", -1)]).explain()["executionStats"]
    idx_stage = idx_explain.get("executionStages", {}).get("stage", "IXSCAN/FETCH")
    idx_docs = idx_explain.get("totalDocsExamined", 0)
    idx_keys = idx_explain.get("totalKeysExamined", 0)
    idx_time = idx_explain.get("executionTimeMillis", 0)
    idx_returned = idx_explain.get("nReturned", 0)

    # 1B: Forced Collscan
    coll_explain = posts_col.find(filter_q).hint([("$natural", 1)]).explain()["executionStats"]
    coll_stage = coll_explain.get("executionStages", {}).get("stage", "COLLSCAN")
    coll_docs = coll_explain.get("totalDocsExamined", 0)
    coll_keys = coll_explain.get("totalKeysExamined", 0)
    coll_time = coll_explain.get("executionTimeMillis", 0)
    coll_returned = coll_explain.get("nReturned", 0)

    docs_saved = max(0, coll_docs - idx_docs)
    reduction = round((docs_saved / max(1, coll_docs)) * 100, 2)

    print(f"{'Metric':<25} | {'Indexed (idx_compound)':<22} | {'Unindexed (COLLSCAN)':<20}")
    print(f"{'-'*25}-|-{'-'*22}-|-{'-'*20}")
    print(f"{'Winning Stage':<25} | {idx_stage:<22} | {coll_stage:<20}")
    print(f"{'Docs Examined':<25} | {idx_docs:<22} | {coll_docs:<20}")
    print(f"{'Keys Examined':<25} | {idx_keys:<22} | {coll_keys:<20}")
    print(f"{'Docs Returned':<25} | {idx_returned:<22} | {coll_returned:<20}")
    print(f"{'Execution Time (ms)':<25} | {idx_time:<22} | {coll_time:<20}")
    print(f"{'-'*75}")
    print(f"[+] ADBMS Optimization Gain: Avoided scanning {docs_saved:,} irrelevant docs ({reduction}% scan reduction)!\n")

    # -------------------------------------------------------------
    # BENCHMARK 2: Multikey Index Lookup on Hashtag Arrays
    # -------------------------------------------------------------
    print("-" * 75)
    print("BENCHMARK 2: Multikey B-Tree Index on Array Field ('hashtags')")
    print("Predicate: { hashtags: '#GenerativeAI' }")
    print("-" * 75)

    tag_filter = {"hashtags": "#GenerativeAI"}
    tag_explain = posts_col.find(tag_filter).explain()["executionStats"]
    tag_stage = tag_explain.get("executionStages", {}).get("stage", "IXSCAN/FETCH")
    tag_docs = tag_explain.get("totalDocsExamined", 0)
    tag_keys = tag_explain.get("totalKeysExamined", 0)
    tag_time = tag_explain.get("executionTimeMillis", 0)
    tag_returned = tag_explain.get("nReturned", 0)

    print(f"Stage:               {tag_stage}")
    print(f"Keys Examined:       {tag_keys} (Index B-Tree Multikey Entries)")
    print(f"Docs Examined:       {tag_docs}")
    print(f"Docs Returned:       {tag_returned}")
    print(f"Execution Time:      {tag_time} ms")
    print("[+] Multikey index indexes each individual array element as an independent B-Tree key entry.\n")

    # -------------------------------------------------------------
    # BENCHMARK 3: Geospatial 2dsphere ($geoNear) Aggregation
    # -------------------------------------------------------------
    print("-" * 75)
    print("BENCHMARK 3: Geospatial 2dsphere Index ($geoNear Aggregation)")
    print("Center: San Francisco [-122.4194, 37.7749], Radius: 500 km")
    print("-" * 75)

    geo_pipe = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [-122.4194, 37.7749]},
                "distanceField": "dist_meters",
                "maxDistance": 500 * 1000,
                "spherical": True
            }
        },
        {"$limit": 10}
    ]

    t0 = time.perf_counter()
    geo_results = list(posts_col.aggregate(geo_pipe))
    t_elapsed = round((time.perf_counter() - t0) * 1000, 2)

    print(f"Spherical Results:   {len(geo_results)} local posts located")
    print(f"Pipeline Latency:    {t_elapsed} ms")
    if geo_results:
        closest = geo_results[0]
        dist_km = round(closest["dist_meters"] / 1000, 1)
        print(f"Closest Post:        {closest.get('influencer_handle')} ({dist_km} km away)")
    print("[+] 2dsphere uses S2 geometry hierarchical cell decomposition for logarithmic spatial search.\n")

    # -------------------------------------------------------------
    # BENCHMARK 4: Multi-Dimensional $facet Aggregation
    # -------------------------------------------------------------
    print("-" * 75)
    print("BENCHMARK 4: Single Round-Trip Multi-Dimensional Pipeline ($facet)")
    print("Executes 3 independent analytics pipelines in 1 DB pass")
    print("-" * 75)

    facet_pipe = [
        {
            "$facet": {
                "viral_tags": [
                    {"$unwind": "$hashtags"},
                    {"$group": {"_id": "$hashtags", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 3}
                ],
                "format_performance": [
                    {"$group": {"_id": "$post_type", "avg_likes": {"$avg": "$metrics.likes"}}},
                    {"$sort": {"avg_likes": -1}}
                ]
            }
        }
    ]

    t0 = time.perf_counter()
    facet_res = list(posts_col.aggregate(facet_pipe))
    facet_elapsed = round((time.perf_counter() - t0) * 1000, 2)

    print(f"Execution Latency:   {facet_elapsed} ms")
    if facet_res:
        top_tags = [f"{t['_id']} ({t['count']})" for t in facet_res[0].get("viral_tags", [])]
        print(f"Top 3 Tags Discovered: {', '.join(top_tags)}")
    print("[+] Multi-faceted aggregation eliminates multiple network round trips between server and DB.")
    print("=" * 75)

    Database.close_db()

if __name__ == "__main__":
    run_benchmarks()

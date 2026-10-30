"""
SocialPulse Comprehensive End-to-End Test Suite
Validates all backend API endpoints, ADBMS indexing concepts, MongoDB aggregation pipelines,
geospatial queries, ACID transaction simulations, and edge case validations.
"""
import sys
import os
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from app.database import Database

client = TestClient(app)

def test_database_indexes():
    """Verify that all required ADBMS indexes exist and match specifications"""
    db = Database.db
    assert db is not None, "Database connection failed"

    # 1. Influencers indexes
    inf_indexes = db["influencers"].index_information()
    assert "idx_handle_unique" in inf_indexes
    assert inf_indexes["idx_handle_unique"].get("unique") is True
    assert "idx_niche_followers_compound" in inf_indexes
    assert "idx_platform_tier_compound" in inf_indexes
    assert "idx_influencer_geo_2dsphere" in inf_indexes
    assert "idx_collabs_multikey" in inf_indexes
    assert "idx_credibility" in inf_indexes

    # 2. Posts indexes
    posts_indexes = db["posts"].index_information()
    assert "idx_platform_likes_date_compound" in posts_indexes
    assert "idx_influencer_posts_compound" in posts_indexes
    assert "idx_hashtags_multikey" in posts_indexes
    assert "idx_posts_geo_2dsphere" in posts_indexes
    assert "idx_partial_high_viral_posts" in posts_indexes
    assert posts_indexes["idx_partial_high_viral_posts"].get("partialFilterExpression") == {"metrics.viral_score": {"$gte": 75}}

    # 3. Trends indexes
    trends_indexes = db["trends"].index_information()
    assert "idx_trend_hashtag_unique" in trends_indexes
    assert trends_indexes["idx_trend_hashtag_unique"].get("unique") is True
    assert "idx_category_velocity_compound" in trends_indexes

    # 4. TTL Index on live_trend_events
    events_indexes = db["live_trend_events"].index_information()
    assert "idx_ttl_event_24h" in events_indexes
    assert events_indexes["idx_ttl_event_24h"].get("expireAfterSeconds") == 86400
    print("[PASS] test_database_indexes: All ADBMS indexes verified.")

def test_overview_stats():
    """Verify Overview KPI aggregation endpoint"""
    res = client.get("/api/overview/stats")
    assert res.status_code == 200
    data = res.json()
    kpis = data["kpis"]
    assert kpis["total_influencers"] >= 40
    assert kpis["total_posts"] >= 1000
    assert kpis["total_trends"] >= 8
    assert kpis["avg_engagement_rate"] > 0
    assert len(data["platform_breakdown"]) > 0
    assert len(data["niche_breakdown"]) > 0
    assert len(data["top_viral_posts"]) == 5
    assert len(data["top_surging_trends"]) == 5
    print("[PASS] test_overview_stats: Overview KPIs verified.")

def test_influencers_crud_and_duplicate_handling():
    """Verify influencer search, compound filter, detail, creation, duplicate prevention, and deletion"""
    # 1. Search and compound filtering
    res = client.get("/api/influencers?niche=Tech%20%26%20AI&min_er=4.0&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    for inf in data["data"]:
        assert inf["niche"] == "Tech & AI"
        assert inf["metrics"]["engagement_rate"] >= 4.0

    # 2. Detail profile
    res = client.get("/api/influencers/@elena_ai_tech")
    assert res.status_code == 200
    detail = res.json()
    assert detail["influencer"]["handle"] == "@elena_ai_tech"
    assert len(detail["recent_posts"]) > 0
    assert len(detail["content_breakdown"]) > 0

    # 3. Head-to-Head Compare
    res = client.get("/api/influencers/compare?handles=@elena_ai_tech,@chen_codes")
    assert res.status_code == 200
    comp = res.json()
    assert comp["compared_count"] == 2

    # 4. Create new influencer with valid payload
    unique_handle = f"@test_creator_{int(datetime.now(timezone.utc).timestamp())}"
    new_creator_payload = {
        "handle": unique_handle,
        "name": "Alex Test Creator",
        "bio": "Testing ADBMS MongoDB schemas",
        "niche": "Tech & AI",
        "platform_primary": "YouTube",
        "tier": "Mid-Tier (100K-500K)",
        "metrics": {
            "followers_count": 250000,
            "following_count": 400,
            "total_posts": 80,
            "engagement_rate": 5.8,
            "avg_likes": 12000,
            "avg_comments": 800,
            "credibility_score": 94,
            "fake_followers_pct": 3.2
        },
        "audience_demographics": {
            "gender": {"male": 60.0, "female": 38.0, "other": 2.0},
            "age_brackets": {"18-24": 35.0, "25-34": 45.0, "35-44": 15.0, "45+": 5.0},
            "top_countries": [{"country": "US", "pct": 45.0}]
        },
        "collaboration_rates": {
            "post_rate_usd": 2500.0,
            "reel_video_rate_usd": 4500.0
        },
        "location": {
            "city": "San Francisco",
            "country": "USA"
        },
        "location_geo": {
            "type": "Point",
            "coordinates": [-122.4194, 37.7749]
        }
    }
    create_res = client.post("/api/influencers", json=new_creator_payload)
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["handle"] == unique_handle

    # 5. Duplicate handle prevention (Unique index constraint test)
    dup_res = client.post("/api/influencers", json=new_creator_payload)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 6. Delete created creator (cascade cleanup)
    del_res = client.delete(f"/api/influencers/{unique_handle}")
    assert del_res.status_code == 200
    assert "Successfully deleted" in del_res.json()["message"]

    print("[PASS] test_influencers_crud_and_duplicate_handling: Verified.")

def test_trends_and_multikey_matching_posts():
    """Verify trends listing, velocity stats, and multikey hashtag post lookup"""
    # 1. List trends
    res = client.get("/api/trends")
    assert res.status_code == 200
    trends = res.json()["data"]
    assert len(trends) >= 8

    # 2. Category velocity analytics pipeline
    cat_res = client.get("/api/trends/analytics/category-velocity")
    assert cat_res.status_code == 200
    categories = cat_res.json()["categories"]
    assert len(categories) > 0

    # 3. Trend Detail & Multikey Hashtag Matching Posts
    # This was previously returning 0 posts due to mismatched seeded hashtags.
    detail_res = client.get("/api/trends/%23GenerativeAI")
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert data["trend"]["hashtag"] == "#GenerativeAI"
    viral_posts = data["viral_posts"]
    assert len(viral_posts) > 0, "Multikey index query on #GenerativeAI returned 0 posts!"
    for p in viral_posts:
        assert "#GenerativeAI" in p["hashtags"], f"Post does not contain searched hashtag: {p['hashtags']}"

    print(f"[PASS] test_trends_and_multikey_matching_posts: Verified with {len(viral_posts)} matching posts for #GenerativeAI.")

def test_campaigns_and_acid_transactions():
    """Verify campaigns list, matchmaker algorithm, and ACID transaction commit & rollback simulation"""
    # 1. List campaigns
    res = client.get("/api/campaigns")
    assert res.status_code == 200
    campaigns = res.json()["data"]
    assert len(campaigns) >= 5
    camp = campaigns[0]
    camp_id = camp["id"]

    # 2. Algorithmic Matchmaker
    match_res = client.get("/api/campaigns/matchmaker?niche=Tech%20%26%20AI&max_budget_per_creator=20000&min_credibility=90")
    assert match_res.status_code == 200
    matches = match_res.json()["matches"]
    assert len(matches) > 0

    # 3. ACID Transaction: Commit simulation
    tx_commit_payload = {
        "campaign_id": camp_id,
        "influencer_handle": "@elena_ai_tech",
        "fee": 500.0,
        "simulate_rollback": False
    }
    tx_res = client.post("/api/campaigns/allocate-budget-transaction", json=tx_commit_payload)
    assert tx_res.status_code == 200
    assert tx_res.json()["status"] == "committed"

    # 4. ACID Transaction: Rollback simulation
    tx_rollback_payload = {
        "campaign_id": camp_id,
        "influencer_handle": "@chen_codes",
        "fee": 500.0,
        "simulate_rollback": True
    }
    tx_roll_res = client.post("/api/campaigns/allocate-budget-transaction", json=tx_rollback_payload)
    assert tx_roll_res.status_code == 200
    assert tx_roll_res.json()["status"] == "aborted"

    # 5. Budget Headroom Exhaustion Edge Case
    tx_exceed_payload = {
        "campaign_id": camp_id,
        "influencer_handle": "@elena_ai_tech",
        "fee": 999999999.0,
        "simulate_rollback": False
    }
    tx_exceed_res = client.post("/api/campaigns/allocate-budget-transaction", json=tx_exceed_payload)
    assert tx_exceed_res.status_code == 400
    assert "Insufficient campaign budget" in tx_exceed_res.json()["detail"]

    print("[PASS] test_campaigns_and_acid_transactions: Verified.")

def test_geospatial_queries_and_clustering():
    """Verify $geoNear proximity queries, boundary validation, and regional influencer clustering"""
    # 1. Global creator hubs
    hubs_res = client.get("/api/geo/hubs")
    assert hubs_res.status_code == 200
    assert len(hubs_res.json()) >= 10

    # 2. $geoNear proximity search
    near_res = client.get("/api/geo/near?lng=-122.4194&lat=37.7749&max_distance_km=500&limit=15")
    assert near_res.status_code == 200
    near_data = near_res.json()
    assert near_data["total_found"] > 0
    assert len(near_data["posts"]) > 0
    for p in near_data["posts"]:
        assert "distance_km" in p
        assert p["distance_km"] <= 500.0

    # 3. Boundary validation: out-of-range coordinates must return 400/422, not 500
    invalid_geo_res = client.get("/api/geo/near?lng=200&lat=95")
    assert invalid_geo_res.status_code in [400, 422], f"Expected 400 or 422, got {invalid_geo_res.status_code}"

    # 4. Regional Influencer Clusters
    # Previously broken: returned 46 clusters with creators_count 1 due to jitter in _id
    clusters_res = client.get("/api/geo/influencer-clusters")
    assert clusters_res.status_code == 200
    clusters = clusters_res.json()
    assert len(clusters) > 0
    assert len(clusters) < 46, f"Expected city-grouped clusters (< 46), got {len(clusters)}"
    top_cluster = clusters[0]
    assert top_cluster["creators_count"] > 1, f"Top cluster should aggregate multiple creators, got {top_cluster['creators_count']}"
    assert "avg_engagement_rate" in top_cluster
    assert len(top_cluster["top_handles"]) > 0

    # 5. CARTO Basemap API Key config endpoints
    cfg_get = client.get("/api/geo/config")
    assert cfg_get.status_code == 200
    assert "carto_api_key" in cfg_get.json()

    cfg_post = client.post("/api/geo/config", json={"api_key": "test_carto_key_999"})
    assert cfg_post.status_code == 200
    assert cfg_post.json()["carto_api_key"] == "test_carto_key_999"

    # Reset back to default key
    client.post("/api/geo/config", json={"api_key": "cb1_4ezo_1_7d64896af4f435381c3f8b1a"})

    print(f"[PASS] test_geospatial_queries_and_clustering: Verified {len(clusters)} city clusters (top cluster has {top_cluster['creators_count']} creators in {top_cluster['city']}) and CARTO config.")

def test_adbms_lab_pipelines_and_explain_benchmark():
    """Verify all 4 ADBMS aggregation pipelines, explain benchmark, and index storage catalogs"""
    # 1. Pipeline 1: $bucket
    p1 = client.get("/api/adbms-lab/pipelines/bucketing")
    assert p1.status_code == 200
    assert len(p1.json()["results"]) > 0

    # 2. Pipeline 2: $facet
    p2 = client.get("/api/adbms-lab/pipelines/facet-multidimensional")
    assert p2.status_code == 200
    facet_res = p2.json()["results"]
    assert "top_viral_tags" in facet_res
    assert "top_positive_content" in facet_res
    assert "content_format_performance" in facet_res

    # 3. Pipeline 3: $graphLookup (recursive graph traversal)
    p3 = client.get("/api/adbms-lab/pipelines/graph-lookup?start_handle=@elena_ai_tech&max_depth=2")
    assert p3.status_code == 200
    graph_res = p3.json()["results"]
    assert graph_res["network_size"] > 0
    assert len(graph_res["collaboration_network"]) > 0

    # 4. Pipeline 4: $lookup (relational cross-collection join)
    p4 = client.get("/api/adbms-lab/pipelines/relational-lookup")
    assert p4.status_code == 200
    assert len(p4.json()["results"]) > 0

    # 5. Explain Plan Benchmark (IXSCAN vs COLLSCAN)
    explain_res = client.get("/api/adbms-lab/benchmarks/explain-plan?platform=YouTube&min_likes=40000")
    assert explain_res.status_code == 200
    summary = explain_res.json()["benchmark_summary"]
    idx = summary["indexed_run"]
    coll = summary["unindexed_run"]
    assert idx["execution_stage"] in ["IXSCAN", "FETCH"]
    assert coll["execution_stage"] == "COLLSCAN"
    assert coll["docs_examined"] > idx["docs_examined"]

    # 6. Database Storage & Index Inspector
    db_stats = client.get("/api/adbms-lab/database-stats")
    assert db_stats.status_code == 200
    collections = db_stats.json()["collections"]
    assert len(collections) >= 5

    print("[PASS] test_adbms_lab_pipelines_and_explain_benchmark: Verified.")

def test_static_spa_files():
    """Verify static frontend files and SPA entrypoints"""
    res = client.get("/")
    assert res.status_code == 200
    assert "SocialPulse" in res.text
    assert "modal-influencer-detail" in res.text
    assert "modal-detail-content" in res.text

    css_res = client.get("/css/style.css")
    assert css_res.status_code == 200

    js_app = client.get("/js/app.js")
    assert js_app.status_code == 200
    assert "modal-chart-radar" in js_app.text
    assert "renderCreatorDemographicsRadar" in js_app.text

    js_charts = client.get("/js/charts.js")
    assert js_charts.status_code == 200
    assert "renderCreatorDemographicsRadar" in js_charts.text

    js_lab = client.get("/js/adbms_lab.js")
    assert js_lab.status_code == 200
    assert "graph" in js_lab.text

    print("[PASS] test_static_spa_files: All static frontend files verified.")

def test_instagram_live_and_proxy():
    """Verify Instagram live search, caching, proxy-image endpoint, and ER computation"""
    # 1. Instagram Config Endpoint
    cfg_res = client.get("/api/instagram/config")
    assert cfg_res.status_code == 200
    cfg = cfg_res.json()
    assert "active_mode" in cfg
    assert "has_api_key" in cfg

    # 2. Instagram Cached Profiles Endpoint
    cached_res = client.get("/api/instagram/cached?limit=5")
    assert cached_res.status_code == 200
    assert "profiles" in cached_res.json()

    # 3. Instagram Profile Lookup (cristiano or synthetic fallback)
    profile_res = client.get("/api/instagram/profile/cristiano")
    assert profile_res.status_code in [200, 404]
    if profile_res.status_code == 200:
        p_data = profile_res.json()
        assert p_data["username"] == "cristiano"
        assert "metrics" in p_data
        assert "engagement_rate" in p_data["metrics"]
        assert "recent_posts" in p_data
        # Ensure post likes and comments are non-null
        for p in p_data.get("recent_posts", []):
            assert p.get("likes") is not None
            assert p.get("comments") is not None

    # 4. Proxy-image endpoint with invalid URL returns 400
    bad_img_res = client.get("/api/instagram/proxy-image?url=ftp://invalid")
    assert bad_img_res.status_code == 400

    print("[PASS] test_instagram_live_and_proxy: Verified live lookup, proxy, and post metrics.")

def run_all_tests():
    print("=" * 70)
    print("      SocialPulse Automated ADBMS Verification Suite")
    print("=" * 70)
    test_database_indexes()
    test_overview_stats()
    test_influencers_crud_and_duplicate_handling()
    test_trends_and_multikey_matching_posts()
    test_campaigns_and_acid_transactions()
    test_geospatial_queries_and_clustering()
    test_adbms_lab_pipelines_and_explain_benchmark()
    test_static_spa_files()
    test_instagram_live_and_proxy()
    print("=" * 70)
    print("  ALL 9 ADVANCED TEST MODULES PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()

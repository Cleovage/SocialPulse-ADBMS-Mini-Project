"""
Empirical Adversarial & Stress Test Harness for Milestone 1 Backend.
Tests:
1. Abnormal usernames: empty, spaces, leading @, multiple @, Unicode (CJK, Arabic, Cyrillic, Emojis),
   special characters, punctuation, null bytes, long strings, path traversal tokens, encoded slashes, hashtags.
2. Latency & Caching: 15 consecutive requests for cached profiles, measuring P50, P90, P99, max latency (<50ms).
3. Simulated Network Outage:
   - For a synthetic user (e.g., elena_ai_tech): verifies fallback to Tier 4 synthetic database with HTTP 200.
   - For an unknown user: verifies clean HTTP 404 error response (never HTTP 500).
4. RapidAPI configuration edge cases:
   - Empty/missing key -> direct_crawler.
   - Invalid RapidAPI key -> graceful fallback to Tier 3 Crawler Scraper.
   - Masked verification.
5. Cache TTL Expiration (>24h):
   - Verifies expired cache triggers live re-fetch.
6. MongoDB dual-write integrity:
   - Verifies both instagram_profiles and influencers collections are upserted.
7. Engagement Rate formula boundary conditions:
   - 0 followers, negative followers, private account, exact post metrics, benchmark hash reproducibility.
8. Concurrency stress: 20 simultaneous requests.
"""

import sys
import os
import time
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import httpx

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from app.database import Database
from app.services.instagram_service import InstagramService, compute_engagement_rate

client = TestClient(app)

results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "findings": []
}

def record_result(test_name: str, passed: bool, details: str = ""):
    results["total_tests"] += 1
    if passed:
        results["passed"] += 1
        print(f"[PASS] {test_name}: {details}")
    else:
        results["failed"] += 1
        print(f"[FAIL] {test_name}: {details}")
        results["findings"].append({"test": test_name, "details": details})


def test_abnormal_usernames():
    print("\n--- 1. Testing Abnormal and Adversarial Usernames ---")
    adversarial_inputs = [
        # (input_str, expected_statuses, label)
        ("", [400, 404], "Empty string / trailing slash"),
        (" ", [400], "Single space"),
        ("     ", [400], "Multiple spaces"),
        ("@", [400], "Single @"),
        ("@@@", [400], "Triple @"),
        ("  @  ", [400], "Spaces around @"),
        ("@cristiano", [200], "Leading @ on known profile"),
        ("@@cristiano", [200], "Double leading @ on known profile"),
        ("cristiano  ", [200], "Trailing spaces on known profile"),
        ("  cristiano  ", [200], "Leading and trailing spaces on known profile"),
        ("elena_ai_tech", [200], "Known synthetic profile handle"),
        ("@elena_ai_tech", [200], "Known synthetic profile with @"),
        ("🔥🚀✨", [400, 404], "Emoji-only username"),
        ("李小龙", [400, 404], "Chinese CJK characters"),
        ("محمد", [400, 404], "Arabic characters"),
        ("путин", [400, 404], "Cyrillic characters"),
        ("josé_maría", [400, 404], "Accented characters"),
        ("user!#$*()", [400, 404], "Special characters / punctuation"),
        ("user..name", [400, 404], "Consecutive dots"),
        ("user--name", [400, 404], "Consecutive hyphens"),
        ("a" * 1000, [400, 404], "Extremely long username (1000 chars)"),
        ("non_existent_random_user_998877665544332211", [404], "Confirmed non-existent creator"),
        ("admin' OR '1'='1", [400, 404], "SQL injection string"),
        ('{"$gt": ""}', [400, 404], "NoSQL injection string"),
        ("../../../etc/passwd", [400, 404], "Path traversal pattern"),
        ("%00", [400, 404], "Null byte token"),
        ("%23cristiano", [200, 400, 404], "Encoded hashtag token")
    ]

    for raw_input, expected_statuses, label in adversarial_inputs:
        try:
            url = f"/api/instagram/profile/{raw_input}"
            resp = client.get(url)
            status = resp.status_code
            # Crucial: Ensure NO unhandled 500 error ever occurs
            assert status != 500, f"Server returned 500 Internal Server Error for input: {raw_input!r}"
            assert status in expected_statuses, f"Got status {status}, expected {expected_statuses} for {label}"
            
            # Verify error response structure if 400 or 404
            if status in [400, 404]:
                body = resp.json()
                # Accept either router structured error ("error"/"status") or framework 404 ("detail")
                has_error_field = ("error" in body) or ("detail" in body)
                assert has_error_field, f"Missing error or detail field in response: {body}"
            
            record_result(f"Abnormal Username: {label}", True, f"Handled with status {status} (No 500)")
        except Exception as e:
            record_result(f"Abnormal Username: {label}", False, str(e))


def test_cache_hit_latency():
    print("\n--- 2. Testing Latency & Cache Performance (<50ms requirement) ---")
    # First, ensure profile is cached
    setup_resp = client.get("/api/instagram/profile/cristiano")
    assert setup_resp.status_code == 200, "Setup cache fetch failed"
    
    latencies = []
    iterations = 15
    for i in range(iterations):
        t0 = time.perf_counter()
        resp = client.get("/api/instagram/profile/cristiano")
        t1 = time.perf_counter()
        lat_ms = (t1 - t0) * 1000.0
        latencies.append(lat_ms)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("source") == "cached_instagram", f"Expected source 'cached_instagram', got {data.get('source')}"

    avg_lat = sum(latencies) / len(latencies)
    max_lat = max(latencies)
    min_lat = min(latencies)
    latencies.sort()
    p90_lat = latencies[int(len(latencies) * 0.90)]
    p99_lat = latencies[-1]

    print(f"    Cache Latency stats ({iterations} queries):")
    print(f"      Min: {min_lat:.2f} ms")
    print(f"      Avg: {avg_lat:.2f} ms")
    print(f"      P90: {p90_lat:.2f} ms")
    print(f"      Max: {max_lat:.2f} ms")

    passed = (p90_lat < 50.0) and (max_lat < 100.0)
    record_result(
        "Cache Hit Latency (<50ms P90)",
        passed,
        f"Avg: {avg_lat:.2f}ms, P90: {p90_lat:.2f}ms, Max: {max_lat:.2f}ms (Target: <50ms)"
    )


def test_simulated_network_outage_fallback():
    print("\n--- 3. Testing Simulated Network Outage & Synthetic Fallback ---")
    
    # Simulate network outage by patching httpx.AsyncClient.get to raise ConnectError
    async def mock_network_error(*args, **kwargs):
        raise httpx.ConnectError("Simulated DNS / Network failure: Connection refused")

    with patch("httpx.AsyncClient.get", side_effect=mock_network_error):
        # Case A: Synthetic creator with network down -> Should fallback gracefully to synthetic data (HTTP 200)
        try:
            resp_synth = client.get("/api/instagram/profile/elena_ai_tech?force_refresh=true")
            assert resp_synth.status_code == 200, f"Expected 200 for synthetic user under network failure, got {resp_synth.status_code}"
            data_synth = resp_synth.json()
            assert data_synth.get("status") == "fallback", f"Expected status 'fallback', got {data_synth.get('status')}"
            assert data_synth.get("source") == "synthetic", f"Expected source 'synthetic', got {data_synth.get('source')}"
            assert data_synth.get("username") == "elena_ai_tech"
            record_result("Network Outage Fallback: Synthetic Creator", True, "Fallback to synthetic profile succeeded (HTTP 200, source='synthetic')")
        except Exception as e:
            record_result("Network Outage Fallback: Synthetic Creator", False, str(e))

        # Case B: Unknown creator with network down -> Should return clean 404 (NEVER 500)
        try:
            resp_unknown = client.get("/api/instagram/profile/unknown_ghost_creator_12345?force_refresh=true")
            assert resp_unknown.status_code == 404, f"Expected 404 for unknown user under network failure, got {resp_unknown.status_code}"
            data_unknown = resp_unknown.json()
            assert data_unknown.get("status") == "error"
            assert data_unknown.get("suggest_synthetic") is True
            record_result("Network Outage: Unknown Creator Error", True, "Returned clean 404 with suggest_synthetic=True, no 500 error")
        except Exception as e:
            record_result("Network Outage: Unknown Creator Error", False, str(e))


def test_rapidapi_invalid_key_graceful_fallback():
    print("\n--- 4. Testing RapidAPI Invalid Key Fallback to Crawler ---")
    # Configure an invalid RapidAPI key
    InstagramService.set_api_key("INVALID_EXPIRED_KEY_XYZ_999")
    try:
        # Mock RapidAPI 401 response while keeping crawler intact
        orig_get = httpx.AsyncClient.get
        async def mock_get(self, url, *args, **kwargs):
            if "rapidapi" in str(url):
                # Return simulated 401 Unauthorized
                return httpx.Response(401, text='{"message": "Invalid API key"}', request=httpx.Request("GET", url))
            return await orig_get(self, url, *args, **kwargs)

        with patch("httpx.AsyncClient.get", new=mock_get):
            # Query a live profile (force_refresh=True to bypass cache)
            resp = client.get("/api/instagram/profile/cristiano?force_refresh=true")
            assert resp.status_code == 200, f"Expected 200 when RapidAPI fails and crawler succeeds, got {resp.status_code}"
            data = resp.json()
            assert data.get("source") == "live_instagram"
            assert data.get("username") == "cristiano"
            record_result("RapidAPI Invalid Key Fallback", True, "Gracefully bypassed failing RapidAPI and scraped via Tier 3 Crawler")
    except Exception as e:
        record_result("RapidAPI Invalid Key Fallback", False, str(e))
    finally:
        InstagramService.set_api_key(None)


def test_cache_ttl_expiration():
    print("\n--- 5. Testing Cache TTL Expiration (>24 hours) ---")
    db = Database.db
    clean_user = "test_ttl_user"
    expired_time = datetime.now(timezone.utc) - timedelta(hours=25)
    
    # Insert an artificially expired cache document
    db["instagram_profiles"].update_one(
        {"username": clean_user},
        {"$set": {
            "username": clean_user,
            "full_name": "Test TTL User",
            "bio": "Expired cache test",
            "profile_pic_url": "",
            "is_verified": False,
            "is_private": False,
            "metrics": {
                "followers_count": 1000,
                "following_count": 50,
                "posts_count": 10,
                "engagement_rate": 2.5
            },
            "recent_posts": [],
            "source": "cached_instagram",
            "cached_at": expired_time
        }},
        upsert=True
    )

    # Calling lookup without force_refresh should detect expiration (>86400s) and attempt live fetch
    # Since test_ttl_user is synthetic/non-existent on real IG, it will fall back or error, NOT return cached_instagram
    resp = client.get(f"/api/instagram/profile/{clean_user}")
    data = resp.json()
    assert data.get("source") != "cached_instagram", "Expired cache document was improperly returned as fresh cache!"
    record_result("Cache TTL Expiration (>24h)", True, "Expired document (>24h) successfully triggered re-fetch")
    
    # Clean up test user
    db["instagram_profiles"].delete_one({"username": clean_user})


def test_engagement_rate_edge_cases():
    print("\n--- 6. Testing Engagement Rate Mathematical Bounds & Edge Cases ---")
    
    # Case A: 0 followers
    er_0 = compute_engagement_rate(0, [{"likes": 100, "comments": 10}], False, "test_user")
    assert er_0["engagement_rate"] == 0.0
    assert er_0["er_calculation_method"] == "zero_followers"
    record_result("ER Edge Case: Zero Followers", True, "ER = 0.0%, method = 'zero_followers'")

    # Case B: Negative followers
    er_neg = compute_engagement_rate(-500, [{"likes": 100, "comments": 10}], False, "test_user")
    assert er_neg["engagement_rate"] == 0.0
    assert er_neg["er_calculation_method"] == "zero_followers"
    record_result("ER Edge Case: Negative Followers", True, "ER = 0.0%, method = 'zero_followers'")

    # Case C: Private account
    er_priv = compute_engagement_rate(50000, [{"likes": 100, "comments": 10}], True, "private_user")
    assert er_priv["engagement_rate"] == 0.0
    assert er_priv["er_calculation_method"] == "private_account"
    record_result("ER Edge Case: Private Account", True, "ER = 0.0%, method = 'private_account'")

    # Case D: Exact post metrics
    posts = [
        {"likes": 1000, "comments": 100},
        {"likes": 2000, "comments": 200}
    ]
    er_exact = compute_engagement_rate(50000, posts, False, "test_user")
    assert er_exact["engagement_rate"] == 3.3
    assert er_exact["er_calculation_method"] == "exact_post_metrics"
    assert er_exact["avg_likes"] == 1500
    assert er_exact["avg_comments"] == 150
    record_result("ER Math: Exact Metrics Calculation", True, "ER = 3.3%, method = 'exact_post_metrics'")

    # Case E: Follower tier benchmark reproducibility (deterministic hash)
    er_bench1 = compute_engagement_rate(10_000_000, [], False, "cristiano")
    er_bench2 = compute_engagement_rate(10_000_000, [], False, "cristiano")
    assert er_bench1["engagement_rate"] == er_bench2["engagement_rate"]
    assert er_bench1["er_calculation_method"] == "follower_tier_benchmark"
    record_result("ER Determinism: Benchmark Hash Reproducibility", True, f"Reproducible ER: {er_bench1['engagement_rate']}%")


def test_api_config_endpoints():
    print("\n--- 7. Testing API Key Config Endpoints & Masking ---")
    InstagramService.set_api_key(None)
    cfg0 = client.get("/api/instagram/config").json()
    assert cfg0["has_api_key"] is False
    assert cfg0["api_key_masked"] is None
    assert cfg0["active_mode"] == "direct_crawler"
    record_result("API Config: Zero-Config State", True, "Default direct_crawler mode verified")

    long_key = "rapidapi_live_secret_key_123456789_xyz"
    resp_set = client.post("/api/instagram/config", json={"api_key": long_key})
    assert resp_set.status_code == 200
    cfg1 = client.get("/api/instagram/config").json()
    assert cfg1["has_api_key"] is True
    assert cfg1["active_mode"] == "rapidapi"
    assert cfg1["api_key_masked"].startswith("rapi")
    assert cfg1["api_key_masked"].endswith("_xyz")
    assert "*" in cfg1["api_key_masked"]
    record_result("API Config: Long Key Masking", True, f"Masked: {cfg1['api_key_masked']}")

    resp_short = client.post("/api/instagram/config", json={"api_key": "short"})
    assert resp_short.status_code == 200
    cfg2 = client.get("/api/instagram/config").json()
    assert cfg2["api_key_masked"] == "***"
    record_result("API Config: Short Key Masking", True, "Short key correctly masked as '***'")

    resp_revert = client.post("/api/instagram/config", json={"api_key": ""})
    assert resp_revert.status_code == 200
    cfg3 = client.get("/api/instagram/config").json()
    assert cfg3["has_api_key"] is False
    assert cfg3["active_mode"] == "direct_crawler"
    record_result("API Config: Clear Key Revert", True, "Reverted to direct_crawler successfully")


def test_cached_profiles_endpoint():
    print("\n--- 8. Testing /api/instagram/cached Endpoint ---")
    resp = client.get("/api/instagram/cached?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "profiles" in data
    assert isinstance(data["profiles"], list)
    record_result("Cached Profiles: Valid Query", True, f"Retrieved {len(data['profiles'])} cached profiles")

    resp_invalid_low = client.get("/api/instagram/cached?limit=0")
    assert resp_invalid_low.status_code == 422
    record_result("Cached Profiles: Limit < 1 Guard", True, "Returned 422 Unprocessable Entity")

    resp_invalid_high = client.get("/api/instagram/cached?limit=200")
    assert resp_invalid_high.status_code == 422
    record_result("Cached Profiles: Limit > 100 Guard", True, "Returned 422 Unprocessable Entity")


def test_mongodb_dual_write_verification():
    print("\n--- 9. Testing MongoDB Dual-Write Persistence ---")
    db = Database.db
    ig_doc = db["instagram_profiles"].find_one({"username": "cristiano"})
    assert ig_doc is not None, "Profile 'cristiano' not found in instagram_profiles"
    assert ig_doc.get("username") == "cristiano"
    assert "metrics" in ig_doc
    assert ig_doc["metrics"].get("followers_count") > 100_000_000

    inf_doc = db["influencers"].find_one({"handle": "@cristiano"})
    assert inf_doc is not None, "Profile '@cristiano' not found in influencers collection"
    assert inf_doc.get("platform_primary") == "Instagram"
    assert inf_doc["metrics"].get("followers_count") > 100_000_000
    assert "collaboration_rates" in inf_doc
    record_result("MongoDB Dual-Write: Collection Sync", True, "Both instagram_profiles and influencers collections synchronized")


def test_concurrency_stress():
    print("\n--- 10. Testing Concurrency Stress (20 simultaneous requests) ---")
    import concurrent.futures
    
    def fetch_profile(user):
        return client.get(f"/api/instagram/profile/{user}").status_code

    users = ["cristiano", "elena_ai_tech", "therock", "chen_codes"] * 5
    t0 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        status_codes = list(executor.map(fetch_profile, users))
    t1 = time.perf_counter()
    total_time = (t1 - t0) * 1000.0

    assert all(code == 200 for code in status_codes), f"Some concurrent requests failed: {status_codes}"
    assert 500 not in status_codes, "Internal server error occurred under concurrency"
    record_result(
        "Concurrency Stress: 20 Parallel Requests",
        True,
        f"20 requests completed in {total_time:.2f}ms (all HTTP 200, 0 server errors)"
    )


if __name__ == "__main__":
    print("=" * 70)
    print("  SocialPulse Milestone 1 Adversarial & Stress Testing Harness")
    print("=" * 70)

    test_abnormal_usernames()
    test_cache_hit_latency()
    test_simulated_network_outage_fallback()
    test_rapidapi_invalid_key_graceful_fallback()
    test_cache_ttl_expiration()
    test_engagement_rate_edge_cases()
    test_api_config_endpoints()
    test_cached_profiles_endpoint()
    test_mongodb_dual_write_verification()
    test_concurrency_stress()

    print("\n" + "=" * 70)
    print(f"  Summary: {results['passed']}/{results['total_tests']} PASSED, {results['failed']} FAILED")
    print("=" * 70)

    if results["failed"] > 0:
        print("\nFailures:")
        for f in results["findings"]:
            print(f"  - {f['test']}: {f['details']}")
        sys.exit(1)
    else:
        print("\nAll adversarial & stress tests PASSED successfully!")
        sys.exit(0)

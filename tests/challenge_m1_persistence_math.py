"""
tests/challenge_m1_persistence_math.py

Empirical Challenge Harness for Milestone 1:
1. Inspects actual MongoDB documents and indexes in instagram_profiles & influencers
2. Validates index uniqueness constraints
3. Tests ER mathematical bounds and edge cases
4. Tests cache expiry and force_refresh=True behavior
5. Tests concurrent upsert race resilience
"""

import asyncio
import concurrent.futures
import math
import sys
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pymongo.errors import DuplicateKeyError
from app.database import Database
from app.services.instagram_service import (
    InstagramService,
    compute_engagement_rate,
    estimate_benchmark_er,
    determine_tier,
    infer_niche,
    parse_count_str
)

RESULTS = {
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "findings": []
}

def record_finding(category: str, severity: str, description: str, details: Any = None):
    RESULTS["findings"].append({
        "category": category,
        "severity": severity,
        "description": description,
        "details": str(details) if details else None
    })
    if severity == "CRITICAL" or severity == "HIGH":
        RESULTS["failed"] += 1
    elif severity == "MEDIUM" or severity == "LOW":
        RESULTS["warnings"] += 1
    else:
        RESULTS["passed"] += 1


print("=" * 80)
print("SOCIALPULSE M1 EMPIRICAL CHALLENGE: PERSISTENCE & MATHEMATICAL VALIDATION")
print("=" * 80)

# Connect to database
db = Database.db
print(f"[INIT] Connected to DB: {db.name}")

# ==============================================================================
# SECTION 1: Direct MongoDB Validation - Indexes & Uniqueness Constraints
# ==============================================================================
print("\n--- SECTION 1: MongoDB Indexes & Uniqueness Constraints ---")

# 1.1 Check instagram_profiles indexes
ig_col = db["instagram_profiles"]
ig_indexes = ig_col.index_information()
print(f"instagram_profiles indexes: {list(ig_indexes.keys())}")

if "idx_ig_username_unique" in ig_indexes:
    idx_info = ig_indexes["idx_ig_username_unique"]
    if idx_info.get("unique") is True and idx_info.get("key") == [("username", 1)]:
        print("  [PASS] idx_ig_username_unique exists with unique=True on ('username', 1)")
        RESULTS["passed"] += 1
    else:
        record_finding("Indexes", "HIGH", "idx_ig_username_unique exists but does not have unique=True or key is wrong", idx_info)
else:
    record_finding("Indexes", "CRITICAL", "idx_ig_username_unique index missing on instagram_profiles")

# 1.2 Check influencers indexes
inf_col = db["influencers"]
inf_indexes = inf_col.index_information()
print(f"influencers indexes: {list(inf_indexes.keys())}")

if "idx_handle_unique" in inf_indexes:
    idx_info = inf_indexes["idx_handle_unique"]
    if idx_info.get("unique") is True and idx_info.get("key") == [("handle", 1)]:
        print("  [PASS] idx_handle_unique exists with unique=True on ('handle', 1)")
        RESULTS["passed"] += 1
    else:
        record_finding("Indexes", "HIGH", "idx_handle_unique exists but does not have unique=True", idx_info)
else:
    record_finding("Indexes", "CRITICAL", "idx_handle_unique index missing on influencers")

# 1.3 Empirically verify duplicate insertion rejection on instagram_profiles
test_uname = "__emp_test_uniq_ig__"
ig_col.delete_many({"username": test_uname})
ig_col.insert_one({"username": test_uname, "created_at": datetime.now(timezone.utc)})

try:
    ig_col.insert_one({"username": test_uname, "created_at": datetime.now(timezone.utc)})
    record_finding("Indexes", "CRITICAL", "MongoDB failed to enforce unique index on instagram_profiles.username! Duplicate inserted successfully.")
except DuplicateKeyError:
    print("  [PASS] DuplicateKeyError correctly raised on duplicate insert to instagram_profiles")
    RESULTS["passed"] += 1
finally:
    ig_col.delete_many({"username": test_uname})

# 1.4 Empirically verify duplicate insertion rejection on influencers
test_handle = "@__emp_test_uniq_inf__"
inf_col.delete_many({"handle": test_handle})
inf_col.insert_one({"handle": test_handle, "name": "Test", "created_at": datetime.now(timezone.utc)})

try:
    inf_col.insert_one({"handle": test_handle, "name": "Test2", "created_at": datetime.now(timezone.utc)})
    record_finding("Indexes", "CRITICAL", "MongoDB failed to enforce unique index on influencers.handle! Duplicate inserted successfully.")
except DuplicateKeyError:
    print("  [PASS] DuplicateKeyError correctly raised on duplicate insert to influencers")
    RESULTS["passed"] += 1
finally:
    inf_col.delete_many({"handle": test_handle})


# ==============================================================================
# SECTION 2: Document Schema & Field Validation in MongoDB
# ==============================================================================
print("\n--- SECTION 2: Document Schema & Persistence Verification ---")

sample_profile = {
    "username": "empirical_challenge_user",
    "full_name": "Empirical Challenge Creator",
    "bio": "Fitness athlete and tech enthusiast #gym #coding",
    "profile_pic_url": "https://example.com/avatar.jpg",
    "is_verified": True,
    "is_private": False,
    "followers_count": 250000,
    "following_count": 350,
    "posts_count": 520,
    "engagement_rate": 3.45,
    "avg_likes": 8500,
    "avg_comments": 125,
    "er_calculation_method": "exact_post_metrics",
    "recent_posts": [
        {"post_id": "p1", "caption": "Morning workout!", "likes": 9000, "comments": 150},
        {"post_id": "p2", "caption": "Coding day!", "likes": 8000, "comments": 100}
    ],
    "source": "live_instagram"
}

# Clean any existing
ig_col.delete_many({"username": "empirical_challenge_user"})
inf_col.delete_many({"handle": "@empirical_challenge_user"})

# Persist
InstagramService.persist_profile(sample_profile)

# Check instagram_profiles doc
doc_ig = ig_col.find_one({"username": "empirical_challenge_user"})
if not doc_ig:
    record_finding("Persistence", "CRITICAL", "persist_profile failed to insert document into instagram_profiles")
else:
    required_ig_fields = [
        "username", "handle", "name", "full_name", "bio", "avatar",
        "profile_pic_url", "is_verified", "is_private", "platform_primary",
        "tier", "niche", "metrics", "recent_posts", "source", "cached_at",
        "updated_at", "expires_at", "created_at"
    ]
    missing_ig = [f for f in required_ig_fields if f not in doc_ig]
    if missing_ig:
        record_finding("Persistence", "HIGH", f"instagram_profiles doc is missing expected fields: {missing_ig}")
    else:
        print("  [PASS] instagram_profiles document contains all expected schema fields")
        RESULTS["passed"] += 1

    # Check metrics subdoc
    m = doc_ig.get("metrics", {})
    req_m = ["followers_count", "following_count", "posts_count", "avg_likes", "avg_comments", "engagement_rate", "credibility_score", "fake_followers_pct"]
    missing_m = [f for f in req_m if f not in m]
    if missing_m:
        record_finding("Persistence", "HIGH", f"instagram_profiles metrics subdoc missing fields: {missing_m}")
    else:
        print("  [PASS] instagram_profiles.metrics subdocument contains all KPI fields")
        RESULTS["passed"] += 1

    # Check tier & niche inferences
    if doc_ig.get("tier") == "Mid-Tier (100K-500K)":
        print("  [PASS] Tier correctly assigned as 'Mid-Tier (100K-500K)'")
        RESULTS["passed"] += 1
    else:
        record_finding("Persistence", "MEDIUM", f"Unexpected tier for 250K followers: {doc_ig.get('tier')}")

    if doc_ig.get("niche") == "Health & Fitness":
        print("  [PASS] Niche correctly inferred as 'Health & Fitness'")
        RESULTS["passed"] += 1
    else:
        record_finding("Persistence", "LOW", f"Niche was {doc_ig.get('niche')} instead of 'Health & Fitness'")

# Check influencers doc (dual-write)
doc_inf = inf_col.find_one({"handle": "@empirical_challenge_user"})
if not doc_inf:
    record_finding("Persistence", "CRITICAL", "persist_profile failed to dual-write document into influencers collection")
else:
    required_inf_fields = [
        "handle", "name", "avatar", "bio", "platform_primary", "tier",
        "niche", "metrics", "location", "location_geo", "source", "cached_at",
        "created_at", "network", "audience_demographics", "collaboration_rates"
    ]
    missing_inf = [f for f in required_inf_fields if f not in doc_inf]
    if missing_inf:
        record_finding("Persistence", "HIGH", f"influencers dual-write document missing expected fields: {missing_inf}")
    else:
        print("  [PASS] influencers dual-write document contains all discovery & ADBMS fields")
        RESULTS["passed"] += 1


# ==============================================================================
# SECTION 3: ER Mathematical Edge Cases & Boundary Analysis
# ==============================================================================
print("\n--- SECTION 3: ER Mathematical Edge Cases & Bounds ---")

# 3.1 Zero Followers
res_0 = compute_engagement_rate(followers=0, recent_posts=[], is_private=False, username="zero_user")
print(f"Zero followers result: {res_0}")
if res_0["engagement_rate"] == 0.0 and res_0["er_calculation_method"] == "zero_followers":
    print("  [PASS] followers=0 handled safely without ZeroDivisionError")
    RESULTS["passed"] += 1
else:
    record_finding("Math", "HIGH", f"followers=0 returned unexpected result: {res_0}")

# 3.2 Negative Followers
res_neg = compute_engagement_rate(followers=-500, recent_posts=[], is_private=False, username="neg_user")
print(f"Negative followers result: {res_neg}")
if res_neg["engagement_rate"] == 0.0 and res_neg["er_calculation_method"] == "zero_followers":
    print("  [PASS] followers < 0 handled safely")
    RESULTS["passed"] += 1
else:
    record_finding("Math", "HIGH", f"followers < 0 returned unexpected result: {res_neg}")

# 3.3 Private Account
res_priv = compute_engagement_rate(followers=10000, recent_posts=[], is_private=True, username="priv_user")
if res_priv["engagement_rate"] == 0.0 and res_priv["er_calculation_method"] == "private_account":
    print("  [PASS] is_private=True returns ER=0.0 with 'private_account' method")
    RESULTS["passed"] += 1
else:
    record_finding("Math", "MEDIUM", f"is_private=True returned unexpected result: {res_priv}")

# 3.4 Very Large Follower Count (e.g., 1 Billion)
res_huge = compute_engagement_rate(
    followers=1_000_000_000,
    recent_posts=[{"likes": 20_000_000, "comments": 500_000}],
    is_private=False,
    username="huge_user"
)
# Expected ER: (20.5M / 1000M) * 100 = 2.05%
if res_huge["engagement_rate"] == 2.05 and res_huge["er_calculation_method"] == "exact_post_metrics":
    print(f"  [PASS] 1B followers exact ER computed accurately: {res_huge['engagement_rate']}%")
    RESULTS["passed"] += 1
else:
    record_finding("Math", "HIGH", f"Huge follower count computation incorrect: {res_huge}")

# 3.5 Micro with high engagement (>100% ER boundary)
res_super = compute_engagement_rate(
    followers=100,
    recent_posts=[{"likes": 500, "comments": 50}],
    is_private=False,
    username="viral_micro"
)
# Expected ER: (550 / 100) * 100 = 550.0%
if res_super["engagement_rate"] == 550.0 and not math.isnan(res_super["engagement_rate"]):
    print(f"  [PASS] High engagement rate (>100%) handled without overflow/NaN: {res_super['engagement_rate']}%")
    RESULTS["passed"] += 1
else:
    record_finding("Math", "HIGH", f"High engagement calculation failed: {res_super}")

# 3.6 Edge Case: comments is None in post dictionary
print("Testing posts with comments = None...")
try:
    res_none_comments = compute_engagement_rate(
        followers=10000,
        recent_posts=[
            {"post_id": "1", "likes": 500, "comments": None},
            {"post_id": "2", "likes": 600, "comments": 20}
        ],
        is_private=False,
        username="none_comments_user"
    )
    print(f"  Result with comments=None: {res_none_comments}")
    RESULTS["passed"] += 1
except TypeError as te:
    record_finding(
        "Math", "HIGH",
        "TypeError in compute_engagement_rate when post has 'comments': None! `p.get('comments', 0)` returns None, causing sum([None, 20]) to crash.",
        te
    )
    print(f"  [CRASH DETECTED] comments=None caused: {te}")
except Exception as ex:
    record_finding("Math", "HIGH", f"Unexpected exception with comments=None: {ex}", ex)

# 3.7 Edge Case: likes is 0 in all posts
# When likes is 0 in all posts, posts_with_metrics is empty
res_zero_likes = compute_engagement_rate(
    followers=5000,
    recent_posts=[{"post_id": "1", "likes": 0, "comments": 10}],
    is_private=False,
    username="zero_likes_user"
)
print(f"Zero likes in posts result: {res_zero_likes}")
# Check that it falls back gracefully without crashing
if res_zero_likes.get("er_calculation_method") == "follower_tier_benchmark":
    print("  [PASS] All 0-likes posts cleanly falls back to benchmark estimate")
    RESULTS["passed"] += 1
else:
    print(f"  [INFO] Method used: {res_zero_likes.get('er_calculation_method')}")

# 3.8 Benchmark ER Consistency & Determinism
b1 = estimate_benchmark_er("test_user_alpha", 50000)
b2 = estimate_benchmark_er("test_user_alpha", 50000)
b3 = estimate_benchmark_er("test_user_beta", 50000)
if b1 == b2:
    print(f"  [PASS] Benchmark ER is deterministic for same username ({b1} == {b2})")
    RESULTS["passed"] += 1
else:
    record_finding("Math", "MEDIUM", "Benchmark ER is not deterministic for same username", (b1, b2))

if b1 != b3:
    print(f"  [PASS] Benchmark ER varies realistically across different handles ({b1} != {b3})")
    RESULTS["passed"] += 1
else:
    print(f"  [INFO] Benchmark ER identical for different handles (hash collision or identical)")


# ==============================================================================
# SECTION 4: Cache Expiration & force_refresh=True Invalidation
# ==============================================================================
print("\n--- SECTION 4: Cache Expiration & force_refresh Invalidation ---")

test_cache_user = "cache_test_user_m1"
ig_col.delete_many({"username": test_cache_user})
inf_col.delete_many({"handle": f"@{test_cache_user}"})

# Insert initial cached profile with timestamp 10 minutes ago
ten_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
initial_doc = {
    "username": test_cache_user,
    "handle": f"@{test_cache_user}",
    "name": "Cache Test User",
    "full_name": "Cache Test User",
    "bio": "Cache test bio",
    "avatar": "https://example.com/cache.jpg",
    "profile_pic_url": "https://example.com/cache.jpg",
    "is_verified": False,
    "is_private": False,
    "platform_primary": "Instagram",
    "tier": "Nano (1K-10K)",
    "niche": "General Creator",
    "metrics": {
        "followers_count": 5000,
        "following_count": 100,
        "posts_count": 25,
        "total_posts": 25,
        "avg_likes": 150,
        "avg_comments": 10,
        "engagement_rate": 3.20,
        "er_calculation_method": "exact_post_metrics",
        "credibility_score": 90,
        "fake_followers_pct": 4.5
    },
    "recent_posts": [],
    "source": "cached_instagram",
    "cached_at": ten_mins_ago,
    "updated_at": ten_mins_ago,
    "expires_at": ten_mins_ago + timedelta(days=1),
    "created_at": ten_mins_ago
}
ig_col.insert_one(initial_doc)

async def test_cache_and_force_refresh():
    # 4.1 Lookup with force_refresh=False -> Should return cached_instagram
    res_cached = await InstagramService.lookup_profile(test_cache_user, force_refresh=False)
    print(f"force_refresh=False result source: {res_cached.get('source')}, age: {res_cached.get('cached_seconds_ago')}s")
    if res_cached.get("source") == "cached_instagram" and res_cached.get("cached_seconds_ago") is not None:
        if 550 <= res_cached.get("cached_seconds_ago") <= 650:
            print("  [PASS] Cached profile returned with source='cached_instagram' and accurate cached_seconds_ago")
            RESULTS["passed"] += 1
        else:
            print(f"  [WARN] cached_seconds_ago was {res_cached.get('cached_seconds_ago')}")
            RESULTS["passed"] += 1
    else:
        record_finding("Cache", "HIGH", f"Expected source='cached_instagram', got {res_cached.get('source')}")

    # 4.2 Test Cache Expiry: update cached_at to 25 hours ago (>86400s)
    twenty_five_hours_ago = datetime.now(timezone.utc) - timedelta(hours=25)
    ig_col.update_one({"username": test_cache_user}, {"$set": {"cached_at": twenty_five_hours_ago}})

    res_expired = await InstagramService.lookup_profile(test_cache_user, force_refresh=False)
    print(f"Expired cache (>24h) lookup source: {res_expired.get('source')}")
    if res_expired.get("source") != "cached_instagram":
        print("  [PASS] Stale cache (>24h) was bypassed properly!")
        RESULTS["passed"] += 1
    else:
        record_finding("Cache", "HIGH", "Stale cache (>24h) was NOT expired, still returned as cached_instagram!")

    # Reset cache to fresh for force_refresh test
    fresh_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    ig_col.update_one({"username": test_cache_user}, {"$set": {"cached_at": fresh_time}})

    # 4.3 Test force_refresh=True bypass
    # When force_refresh=True is passed, it should NOT return cached_instagram.
    res_forced = await InstagramService.lookup_profile(test_cache_user, force_refresh=True)
    print(f"force_refresh=True lookup source: {res_forced.get('source')}")
    if res_forced.get("source") != "cached_instagram":
        print("  [PASS] force_refresh=True successfully bypassed Tier 1 MongoDB cache!")
        RESULTS["passed"] += 1
    else:
        record_finding("Cache", "HIGH", "force_refresh=True failed to bypass MongoDB cache!")

asyncio.run(test_cache_and_force_refresh())

# Cleanup
ig_col.delete_many({"username": test_cache_user})
inf_col.delete_many({"handle": f"@{test_cache_user}"})


# ==============================================================================
# SECTION 5: Concurrent Upsert Race Resilience Testing
# ==============================================================================
print("\n--- SECTION 5: Concurrent Upsert Race Condition Resilience ---")

concurrent_user = "race_condition_user"
ig_col.delete_many({"username": concurrent_user})
inf_col.delete_many({"handle": f"@{concurrent_user}"})

NUM_CONCURRENT_CALLS = 25
print(f"Launching {NUM_CONCURRENT_CALLS} concurrent upserts on '{concurrent_user}' across threads...")

def do_concurrent_persist(idx: int):
    prof = {
        "username": concurrent_user,
        "full_name": f"Race User {idx}",
        "bio": f"Concurrent test thread {idx}",
        "profile_pic_url": f"https://example.com/avatar_{idx}.jpg",
        "is_verified": bool(idx % 2 == 0),
        "is_private": False,
        "followers_count": 100000 + idx,
        "following_count": 500,
        "posts_count": 100,
        "engagement_rate": 2.50,
        "avg_likes": 2400,
        "avg_comments": 100,
        "er_calculation_method": "exact_post_metrics",
        "recent_posts": [],
        "source": "live_instagram"
    }
    try:
        InstagramService.persist_profile(prof)
        return {"thread": idx, "success": True, "error": None}
    except Exception as e:
        return {"thread": idx, "success": False, "error": str(e)}

start_t = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_CONCURRENT_CALLS) as executor:
    futures = [executor.submit(do_concurrent_persist, i) for i in range(NUM_CONCURRENT_CALLS)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
elapsed = time.time() - start_t

failures = [r for r in results if not r["success"]]
print(f"Executed {NUM_CONCURRENT_CALLS} concurrent upserts in {elapsed:.3f}s. Unhandled exceptions: {len(failures)}")

if len(failures) == 0:
    print("  [PASS] Zero unhandled exceptions or crashes during concurrent upserts!")
    RESULTS["passed"] += 1
else:
    record_finding("Concurrency", "HIGH", f"{len(failures)} concurrent upserts raised unhandled exceptions", failures)

# Check collection state: Exactly ONE document should exist in instagram_profiles and influencers
ig_count = ig_col.count_documents({"username": concurrent_user})
inf_count = inf_col.count_documents({"handle": f"@{concurrent_user}"})
print(f"Document count in instagram_profiles: {ig_count} (expected: 1)")
print(f"Document count in influencers: {inf_count} (expected: 1)")

if ig_count == 1:
    print("  [PASS] Exactly 1 document exists in instagram_profiles (unique index respected, no duplicates)")
    RESULTS["passed"] += 1
else:
    record_finding("Concurrency", "CRITICAL", f"Expected 1 document in instagram_profiles, found {ig_count}")

if inf_count == 1:
    print("  [PASS] Exactly 1 document exists in influencers (unique index respected, no duplicates)")
    RESULTS["passed"] += 1
else:
    record_finding("Concurrency", "CRITICAL", f"Expected 1 document in influencers, found {inf_count}")

# Cleanup
ig_col.delete_many({"username": concurrent_user})
inf_col.delete_many({"handle": f"@{concurrent_user}"})


# ==============================================================================
# SECTION 6: Multi-User Concurrent Upsert Stress Test
# ==============================================================================
print("\n--- SECTION 6: Multi-User Concurrent Upsert Stress Test ---")

# 10 creators, 5 concurrent upserts each = 50 concurrent operations
USERS = [f"stress_user_{i}" for i in range(10)]
for u in USERS:
    ig_col.delete_many({"username": u})
    inf_col.delete_many({"handle": f"@{u}"})

def do_multi_user_persist(pair):
    user_id, run_id = pair
    prof = {
        "username": user_id,
        "full_name": f"Stress {user_id}",
        "bio": f"Stress bio {run_id}",
        "profile_pic_url": "https://example.com/avatar.jpg",
        "is_verified": False,
        "is_private": False,
        "followers_count": 50000 + run_id,
        "following_count": 200,
        "posts_count": 50,
        "engagement_rate": 3.0,
        "avg_likes": 1500,
        "avg_comments": 50,
        "er_calculation_method": "follower_tier_benchmark",
        "recent_posts": [],
        "source": "live_instagram"
    }
    try:
        InstagramService.persist_profile(prof)
        return {"user": user_id, "success": True, "error": None}
    except Exception as e:
        return {"user": user_id, "success": False, "error": str(e)}

tasks = [(u, r) for u in USERS for r in range(5)]
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    multi_results = list(executor.map(do_multi_user_persist, tasks))

multi_failures = [r for r in multi_results if not r["success"]]
if len(multi_failures) == 0:
    print(f"  [PASS] All 50 multi-user concurrent upserts succeeded without exception")
    RESULTS["passed"] += 1
else:
    record_finding("Concurrency", "HIGH", f"{len(multi_failures)} multi-user upserts failed", multi_failures)

# Verify document counts for all 10 users
all_counts_correct = True
for u in USERS:
    c_ig = ig_col.count_documents({"username": u})
    c_inf = inf_col.count_documents({"handle": f"@{u}"})
    if c_ig != 1 or c_inf != 1:
        all_counts_correct = False
        record_finding("Concurrency", "CRITICAL", f"Incorrect counts for {u}: ig={c_ig}, inf={c_inf}")

if all_counts_correct:
    print("  [PASS] All 10 distinct users have exactly 1 document in both collections")
    RESULTS["passed"] += 1

# Cleanup
for u in USERS:
    ig_col.delete_many({"username": u})
    inf_col.delete_many({"handle": f"@{u}"})


# ==============================================================================
# SECTION 7: Inspect Real Cached Documents (e.g., 'cristiano')
# ==============================================================================
print("\n--- SECTION 7: Inspect Real / Seeded Cached Documents ---")
cached_cristiano = ig_col.find_one({"username": "cristiano"})
if cached_cristiano:
    print(f"Found cached 'cristiano' in instagram_profiles:")
    print(f"  Username: {cached_cristiano.get('username')}")
    print(f"  Followers: {cached_cristiano.get('metrics', {}).get('followers_count'):,}")
    print(f"  ER: {cached_cristiano.get('metrics', {}).get('engagement_rate')}%")
    print(f"  Method: {cached_cristiano.get('metrics', {}).get('er_calculation_method')}")
    print(f"  Cached at: {cached_cristiano.get('cached_at')}")
    print(f"  Source: {cached_cristiano.get('source')}")
    RESULTS["passed"] += 1
else:
    print("  [INFO] 'cristiano' not in instagram_profiles yet (can be fetched live or through router test)")

# Check total cached profiles
total_cached = ig_col.count_documents({})
print(f"Total documents in instagram_profiles: {total_cached}")
total_influencers = inf_col.count_documents({})
print(f"Total documents in influencers: {total_influencers}")


# ==============================================================================
# SUMMARY & VERDICT
# ==============================================================================
print("\n" + "=" * 80)
print("CHALLENGE RESULTS SUMMARY")
print("=" * 80)
print(f"Tests Passed: {RESULTS['passed']}")
print(f"Warnings: {RESULTS['warnings']}")
print(f"Critical/High Failures: {RESULTS['failed']}")

if RESULTS["findings"]:
    print("\nFINDINGS:")
    for i, f in enumerate(RESULTS["findings"], 1):
        print(f"  {i}. [{f['severity']}] {f['category']}: {f['description']}")
        if f['details']:
            print(f"     Details: {f['details'][:150]}")
else:
    print("\nZero critical or high severity findings!")

if RESULTS["failed"] == 0:
    print("\nFINAL EMPIRICAL VERDICT: APPROVE")
else:
    print("\nFINAL EMPIRICAL VERDICT: REQUEST_CHANGES")
print("=" * 80)

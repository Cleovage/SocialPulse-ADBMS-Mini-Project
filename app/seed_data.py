import random
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from faker import Faker
from app.database import Database
import logging

logger = logging.getLogger("socialpulse.seeder")
fake = Faker()

CITIES = [
    {"city": "San Francisco", "country": "USA", "coords": [-122.4194, 37.7749]},
    {"city": "New York", "country": "USA", "coords": [-74.0060, 40.7128]},
    {"city": "London", "country": "UK", "coords": [-0.1278, 51.5074]},
    {"city": "Tokyo", "country": "Japan", "coords": [139.6917, 35.6895]},
    {"city": "Mumbai", "country": "India", "coords": [72.8777, 19.0760]},
    {"city": "Berlin", "country": "Germany", "coords": [13.4050, 52.5200]},
    {"city": "Paris", "country": "France", "coords": [2.3522, 48.8566]},
    {"city": "Dubai", "country": "UAE", "coords": [55.2708, 25.2048]},
    {"city": "Singapore", "country": "Singapore", "coords": [103.8198, 1.3521]},
    {"city": "Sydney", "country": "Australia", "coords": [151.2093, -33.8688]},
    {"city": "Toronto", "country": "Canada", "coords": [-79.3832, 43.6532]},
    {"city": "Seoul", "country": "South Korea", "coords": [126.9780, 37.5665]}
]

NICHES = [
    "Tech & AI",
    "Fashion & Lifestyle",
    "Gaming & Esports",
    "Health & Fitness",
    "Finance & Crypto",
    "Food & Culinary",
    "Travel & Adventure"
]

PLATFORMS = ["Instagram", "YouTube", "TikTok", "Twitter/X", "LinkedIn"]

NICHE_HASHTAGS = {
    "Tech & AI": ["#GenerativeAI", "#ArtificialIntelligence", "#MachineLearning", "#GenAI", "#Python", "#CloudComputing", "#OpenAI", "#NextGenTech", "#DevCommunity", "#Robotics", "#QuantumBreakthrough"],
    "Fashion & Lifestyle": ["#SustainableFashion", "#OOTD", "#Streetwear", "#MinimalStyle", "#VogueVibes", "#LuxuryLifestyle", "#BeautyTrends", "#SpringCollection"],
    "Gaming & Esports": ["#NextGenGaming", "#GamingSetup", "#TwitchStreamer", "#EsportsLife", "#ValorantClips", "#PlayStation5", "#RTX4090", "#IndieGames", "#GamerNation"],
    "Health & Fitness": ["#MicroWorkouts", "#FitnessGoals", "#GymLife", "#CleanEating", "#HIITWorkout", "#WellnessJourney", "#Bodybuilding", "#NutritionTips", "#HealthyHabits"],
    "Finance & Crypto": ["#DefiYields2026", "#Investing101", "#Bitcoin", "#StockMarket", "#PassiveIncome", "#PersonalFinance", "#Ethereum", "#FinancialFreedom", "#WealthBuilding"],
    "Food & Culinary": ["#SourdoughFermentation", "#FoodPorn", "#ChefSpecial", "#FarmToTable", "#ArtisanBakery", "#VeganEats", "#HomeCooked", "#StreetFoodEats", "#GourmetDining"],
    "Travel & Adventure": ["#NordicWanderlust", "#Wanderlust", "#SoloTravel", "#BucketList", "#HiddenGems", "#TravelPhotography", "#ExploreNature", "#DigitalNomad", "#TravelAddict"]
}

INFLUENCER_PROFILES = [
    # Tech & AI
    {"name": "Elena Rostova", "handle": "@elena_ai_tech", "niche": "Tech & AI", "platform": "YouTube", "tier": "Mega (1M+)", "followers": 1420000, "er": 5.4, "cred": 96, "gender": "female"},
    {"name": "Devin Chen", "handle": "@chen_codes", "niche": "Tech & AI", "platform": "Twitter/X", "tier": "Macro (500K-1M)", "followers": 680000, "er": 4.8, "cred": 94, "gender": "male"},
    {"name": "Dr. Sarah Vance", "handle": "@sarah_deepmind", "niche": "Tech & AI", "platform": "LinkedIn", "tier": "Mid-Tier (100K-500K)", "followers": 290000, "er": 6.2, "cred": 98, "gender": "female"},
    {"name": "Marcus Sterling", "handle": "@sterling_silicon", "niche": "Tech & AI", "platform": "YouTube", "tier": "Micro (10K-100K)", "followers": 78000, "er": 7.1, "cred": 92, "gender": "male"},
    {"name": "Aria Stark", "handle": "@aria_robotics", "niche": "Tech & AI", "platform": "Instagram", "tier": "Nano (1K-10K)", "followers": 9500, "er": 9.3, "cred": 95, "gender": "female"},
    {"name": "Vikram Malhotra", "handle": "@vikram_ai_labs", "niche": "Tech & AI", "platform": "Twitter/X", "tier": "Mid-Tier (100K-500K)", "followers": 340000, "er": 5.1, "cred": 91, "gender": "male"},
    {"name": "Chloe Dupont", "handle": "@chloe_ux_tech", "niche": "Tech & AI", "platform": "TikTok", "tier": "Micro (10K-100K)", "followers": 62000, "er": 8.4, "cred": 88, "gender": "female"},
    {"name": "Zack Ryder", "handle": "@cloud_architect_zack", "niche": "Tech & AI", "platform": "LinkedIn", "tier": "Mid-Tier (100K-500K)", "followers": 145000, "er": 4.5, "cred": 93, "gender": "male"},

    # Fashion & Lifestyle
    {"name": "Camille Laurent", "handle": "@camille_parisienne", "niche": "Fashion & Lifestyle", "platform": "Instagram", "tier": "Mega (1M+)", "followers": 2850000, "er": 3.9, "cred": 89, "gender": "female"},
    {"name": "Matteo Rossi", "handle": "@matteo_tailored", "niche": "Fashion & Lifestyle", "platform": "Instagram", "tier": "Macro (500K-1M)", "followers": 790000, "er": 4.2, "cred": 92, "gender": "male"},
    {"name": "Sierra Brooks", "handle": "@sierra_chic", "niche": "Fashion & Lifestyle", "platform": "TikTok", "tier": "Mid-Tier (100K-500K)", "followers": 410000, "er": 7.6, "cred": 87, "gender": "female"},
    {"name": "Kiara Advani Vibe", "handle": "@kiara_threads", "niche": "Fashion & Lifestyle", "platform": "Instagram", "tier": "Macro (500K-1M)", "followers": 920000, "er": 4.5, "cred": 90, "gender": "female"},
    {"name": "Oliver Twist Style", "handle": "@oliver_minimal", "niche": "Fashion & Lifestyle", "platform": "TikTok", "tier": "Micro (10K-100K)", "followers": 84000, "er": 6.8, "cred": 91, "gender": "male"},
    {"name": "Yuki Tanaka", "handle": "@yuki_harajuku", "niche": "Fashion & Lifestyle", "platform": "Instagram", "tier": "Mid-Tier (100K-500K)", "followers": 310000, "er": 5.9, "cred": 93, "gender": "female"},
    {"name": "Lucas Silva", "handle": "@lucas_streetstyle", "niche": "Fashion & Lifestyle", "platform": "TikTok", "tier": "Nano (1K-10K)", "followers": 7800, "er": 8.9, "cred": 96, "gender": "male"},

    # Gaming & Esports
    {"name": "Jordan 'Apex' Fox", "handle": "@apexfox_gaming", "niche": "Gaming & Esports", "platform": "YouTube", "tier": "Mega (1M+)", "followers": 3400000, "er": 6.8, "cred": 95, "gender": "male"},
    {"name": "Valkyrie Nova", "handle": "@nova_valkyrie", "niche": "Gaming & Esports", "platform": "TikTok", "tier": "Macro (500K-1M)", "followers": 860000, "er": 8.1, "cred": 91, "gender": "female"},
    {"name": "Kenji Takahashi", "handle": "@kenji_speedrun", "niche": "Gaming & Esports", "platform": "YouTube", "tier": "Mid-Tier (100K-500K)", "followers": 470000, "er": 5.7, "cred": 94, "gender": "male"},
    {"name": "Pixel Bandit", "handle": "@pixel_bandit", "niche": "Gaming & Esports", "platform": "Twitter/X", "tier": "Micro (10K-100K)", "followers": 69000, "er": 7.3, "cred": 89, "gender": "male"},
    {"name": "Siren Queen", "handle": "@siren_fps", "niche": "Gaming & Esports", "platform": "TikTok", "tier": "Mid-Tier (100K-500K)", "followers": 230000, "er": 9.2, "cred": 88, "gender": "female"},
    {"name": "Liam Vance", "handle": "@vance_hardware_rigs", "niche": "Gaming & Esports", "platform": "YouTube", "tier": "Micro (10K-100K)", "followers": 48000, "er": 6.4, "cred": 93, "gender": "male"},
    {"name": "Ghost Sniper", "handle": "@ghost_esports", "niche": "Gaming & Esports", "platform": "Twitter/X", "tier": "Nano (1K-10K)", "followers": 8200, "er": 11.2, "cred": 95, "gender": "male"},

    # Health & Fitness
    {"name": "Maya Lin", "handle": "@maya_yoga_flow", "niche": "Health & Fitness", "platform": "Instagram", "tier": "Macro (500K-1M)", "followers": 740000, "er": 5.2, "cred": 94, "gender": "female"},
    {"name": "Coach Jaxson", "handle": "@jaxson_iron_strength", "niche": "Health & Fitness", "platform": "YouTube", "tier": "Mega (1M+)", "followers": 1650000, "er": 4.9, "cred": 92, "gender": "male"},
    {"name": "Dr. Ananya Rao", "handle": "@dr_ananya_nutrition", "niche": "Health & Fitness", "platform": "Instagram", "tier": "Mid-Tier (100K-500K)", "followers": 380000, "er": 6.5, "cred": 97, "gender": "female"},
    {"name": "Brody Kincaid", "handle": "@brody_calisthenics", "niche": "Health & Fitness", "platform": "TikTok", "tier": "Mid-Tier (100K-500K)", "followers": 490000, "er": 8.7, "cred": 89, "gender": "male"},
    {"name": "Sophia Becker", "handle": "@sophia_marathon", "niche": "Health & Fitness", "platform": "Instagram", "tier": "Micro (10K-100K)", "followers": 52000, "er": 7.4, "cred": 95, "gender": "female"},
    {"name": "Liam O'Connor", "handle": "@liam_functional_fit", "niche": "Health & Fitness", "platform": "YouTube", "tier": "Micro (10K-100K)", "followers": 89000, "er": 5.8, "cred": 91, "gender": "male"},

    # Finance & Crypto
    {"name": "Arthur Pendelton", "handle": "@arthur_macro_hedge", "niche": "Finance & Crypto", "platform": "Twitter/X", "tier": "Macro (500K-1M)", "followers": 610000, "er": 4.1, "cred": 93, "gender": "male"},
    {"name": "Rachel Zane", "handle": "@rachel_fire_investing", "niche": "Finance & Crypto", "platform": "YouTube", "tier": "Mid-Tier (100K-500K)", "followers": 420000, "er": 5.6, "cred": 96, "gender": "female"},
    {"name": "Crypto Spartan", "handle": "@spartan_defi", "niche": "Finance & Crypto", "platform": "Twitter/X", "tier": "Mid-Tier (100K-500K)", "followers": 290000, "er": 6.3, "cred": 84, "gender": "male"},
    {"name": "Natasha Roman", "handle": "@natasha_wealth_hq", "niche": "Finance & Crypto", "platform": "LinkedIn", "tier": "Micro (10K-100K)", "followers": 75000, "er": 4.8, "cred": 95, "gender": "female"},
    {"name": "Benny The Bull", "handle": "@benny_options_trading", "niche": "Finance & Crypto", "platform": "TikTok", "tier": "Mid-Tier (100K-500K)", "followers": 180000, "er": 7.9, "cred": 82, "gender": "male"},
    {"name": "Priya Sharma", "handle": "@priya_fintech_law", "niche": "Finance & Crypto", "platform": "LinkedIn", "tier": "Nano (1K-10K)", "followers": 9800, "er": 6.1, "cred": 97, "gender": "female"},

    # Food & Culinary
    {"name": "Chef Marco Pierre", "handle": "@chef_marco_gourmet", "niche": "Food & Culinary", "platform": "Instagram", "tier": "Mega (1M+)", "followers": 2100000, "er": 4.7, "cred": 95, "gender": "male"},
    {"name": "Hana Kim", "handle": "@hana_korean_kitchen", "niche": "Food & Culinary", "platform": "TikTok", "tier": "Macro (500K-1M)", "followers": 830000, "er": 8.6, "cred": 93, "gender": "female"},
    {"name": "Leo 'Smokemaster' Vance", "handle": "@smokemaster_bbq", "niche": "Food & Culinary", "platform": "YouTube", "tier": "Mid-Tier (100K-500K)", "followers": 450000, "er": 5.9, "cred": 91, "gender": "male"},
    {"name": "Fatima Zahra", "handle": "@fatima_spice_route", "niche": "Food & Culinary", "platform": "Instagram", "tier": "Mid-Tier (100K-500K)", "followers": 280000, "er": 6.4, "cred": 94, "gender": "female"},
    {"name": "Dante Crust", "handle": "@dante_sourdough", "niche": "Food & Culinary", "platform": "TikTok", "tier": "Micro (10K-100K)", "followers": 65000, "er": 9.1, "cred": 92, "gender": "male"},
    {"name": "Zoe Baker", "handle": "@zoe_pastry_art", "niche": "Food & Culinary", "platform": "Instagram", "tier": "Micro (10K-100K)", "followers": 92000, "er": 7.3, "cred": 94, "gender": "female"},

    # Travel & Adventure
    {"name": "Noah & Kai", "handle": "@noah_kai_nomads", "niche": "Travel & Adventure", "platform": "YouTube", "tier": "Mega (1M+)", "followers": 1890000, "er": 5.8, "cred": 94, "gender": "other"},
    {"name": "Isabella Montez", "handle": "@isabella_explores", "niche": "Travel & Adventure", "platform": "Instagram", "tier": "Macro (500K-1M)", "followers": 670000, "er": 6.3, "cred": 92, "gender": "female"},
    {"name": "Finnian Wilder", "handle": "@wilder_alps", "niche": "Travel & Adventure", "platform": "TikTok", "tier": "Mid-Tier (100K-500K)", "followers": 390000, "er": 8.9, "cred": 90, "gender": "male"},
    {"name": "Zara Horizon", "handle": "@zara_ocean_dive", "niche": "Travel & Adventure", "platform": "Instagram", "tier": "Mid-Tier (100K-500K)", "followers": 240000, "er": 7.1, "cred": 93, "gender": "female"},
    {"name": "Tariq Desert Nomad", "handle": "@tariq_dunes", "niche": "Travel & Adventure", "platform": "YouTube", "tier": "Micro (10K-100K)", "followers": 71000, "er": 6.7, "cred": 91, "gender": "male"},
    {"name": "Mila Trekker", "handle": "@mila_patagonia", "niche": "Travel & Adventure", "platform": "Instagram", "tier": "Nano (1K-10K)", "followers": 8900, "er": 10.4, "cred": 97, "gender": "female"}
]

TRENDS_DATA = [
    {
        "hashtag": "#GenerativeAI",
        "topic": "Autonomous AI Agents & Reasoning Models",
        "category": "Tech & AI",
        "volume_24h": 482900,
        "velocity_score": 342.8,
        "viral_index": 98.4,
        "sentiment_summary": {"positive_pct": 74.2, "neutral_pct": 18.5, "negative_pct": 7.3},
        "platform_breakdown": {"Twitter/X": 210000, "LinkedIn": 125000, "YouTube": 82000, "TikTok": 65900},
        "lifecycle_status": "Surging",
        "top_influencer_handles": ["@elena_ai_tech", "@chen_codes", "@sarah_deepmind"]
    },
    {
        "hashtag": "#SustainableFashion",
        "topic": "Circular Wardrobe & Thrift Culture",
        "category": "Fashion & Lifestyle",
        "volume_24h": 298100,
        "velocity_score": 184.2,
        "viral_index": 89.1,
        "sentiment_summary": {"positive_pct": 82.0, "neutral_pct": 12.0, "negative_pct": 6.0},
        "platform_breakdown": {"Instagram": 164000, "TikTok": 98000, "YouTube": 26100, "Twitter/X": 10000},
        "lifecycle_status": "Emerging",
        "top_influencer_handles": ["@camille_parisienne", "@sierra_chic", "@yuki_harajuku"]
    },
    {
        "hashtag": "#NextGenGaming",
        "topic": "Unreal Engine 5.5 Ray-Tracing Showcases",
        "category": "Gaming & Esports",
        "volume_24h": 389400,
        "velocity_score": 260.5,
        "viral_index": 94.7,
        "sentiment_summary": {"positive_pct": 69.4, "neutral_pct": 21.2, "negative_pct": 9.4},
        "platform_breakdown": {"YouTube": 182000, "TikTok": 124000, "Twitter/X": 73400, "Instagram": 10000},
        "lifecycle_status": "Surging",
        "top_influencer_handles": ["@apexfox_gaming", "@nova_valkyrie", "@kenji_speedrun"]
    },
    {
        "hashtag": "#MicroWorkouts",
        "topic": "10-Minute Desk Stretches & Tabata Bursts",
        "category": "Health & Fitness",
        "volume_24h": 215000,
        "velocity_score": 145.0,
        "viral_index": 86.3,
        "sentiment_summary": {"positive_pct": 88.5, "neutral_pct": 8.5, "negative_pct": 3.0},
        "platform_breakdown": {"TikTok": 115000, "Instagram": 72000, "YouTube": 23000, "Twitter/X": 5000},
        "lifecycle_status": "Emerging",
        "top_influencer_handles": ["@maya_yoga_flow", "@brody_calisthenics", "@sophia_marathon"]
    },
    {
        "hashtag": "#DefiYields2026",
        "topic": "Real World Asset Tokenization & Liquid Staking",
        "category": "Finance & Crypto",
        "volume_24h": 194500,
        "velocity_score": 120.4,
        "viral_index": 81.2,
        "sentiment_summary": {"positive_pct": 58.0, "neutral_pct": 26.0, "negative_pct": 16.0},
        "platform_breakdown": {"Twitter/X": 142000, "YouTube": 31000, "LinkedIn": 18500, "TikTok": 3000},
        "lifecycle_status": "Surging",
        "top_influencer_handles": ["@arthur_macro_hedge", "@spartan_defi", "@rachel_fire_investing"]
    },
    {
        "hashtag": "#SourdoughFermentation",
        "topic": "Wild Yeast Artisan Baking Masterclasses",
        "category": "Food & Culinary",
        "volume_24h": 168000,
        "velocity_score": 95.8,
        "viral_index": 78.5,
        "sentiment_summary": {"positive_pct": 91.2, "neutral_pct": 6.8, "negative_pct": 2.0},
        "platform_breakdown": {"Instagram": 89000, "TikTok": 56000, "YouTube": 21000, "Twitter/X": 2000},
        "lifecycle_status": "Peaked",
        "top_influencer_handles": ["@chef_marco_gourmet", "@dante_sourdough", "@hana_korean_kitchen"]
    },
    {
        "hashtag": "#NordicWanderlust",
        "topic": "Aurora Borealis Glass Igloo Expeditions",
        "category": "Travel & Adventure",
        "volume_24h": 274000,
        "velocity_score": 215.3,
        "viral_index": 91.8,
        "sentiment_summary": {"positive_pct": 89.0, "neutral_pct": 8.0, "negative_pct": 3.0},
        "platform_breakdown": {"Instagram": 142000, "TikTok": 86000, "YouTube": 41000, "Twitter/X": 5000},
        "lifecycle_status": "Surging",
        "top_influencer_handles": ["@noah_kai_nomads", "@isabella_explores", "@wilder_alps"]
    },
    {
        "hashtag": "#QuantumBreakthrough",
        "topic": "Fault-Tolerant Quantum Logic Gates",
        "category": "Tech & AI",
        "volume_24h": 142000,
        "velocity_score": 110.2,
        "viral_index": 79.4,
        "sentiment_summary": {"positive_pct": 71.0, "neutral_pct": 22.0, "negative_pct": 7.0},
        "platform_breakdown": {"Twitter/X": 79000, "LinkedIn": 45000, "YouTube": 16000, "TikTok": 2000},
        "lifecycle_status": "Emerging",
        "top_influencer_handles": ["@sarah_deepmind", "@chen_codes"]
    }
]

BRAND_CAMPAIGNS = [
    {
        "brand_name": "NVIDIA",
        "campaign_title": "AI Creators Global Accelerator 2026",
        "target_niche": "Tech & AI",
        "total_budget": 120000.0,
        "spent_budget": 85000.0,
        "status": "Active",
        "assigned_handles": ["@elena_ai_tech", "@chen_codes", "@sterling_silicon"],
        "target_impressions": 5000000,
        "achieved_impressions": 4210000,
        "target_engagement": 320000,
        "achieved_engagement": 284000,
        "calculated_roi": 3.8
    },
    {
        "brand_name": "Gymshark",
        "campaign_title": "Unleash The Athlete Within",
        "target_niche": "Health & Fitness",
        "total_budget": 75000.0,
        "spent_budget": 52000.0,
        "status": "Active",
        "assigned_handles": ["@jaxson_iron_strength", "@maya_yoga_flow", "@brody_calisthenics"],
        "target_impressions": 3800000,
        "achieved_impressions": 3650000,
        "target_engagement": 290000,
        "achieved_engagement": 281000,
        "calculated_roi": 4.2
    },
    {
        "brand_name": "Sony PlayStation",
        "campaign_title": "PS5 Pro Ultimate Visuals Campaign",
        "target_niche": "Gaming & Esports",
        "total_budget": 150000.0,
        "spent_budget": 110000.0,
        "status": "Active",
        "assigned_handles": ["@apexfox_gaming", "@nova_valkyrie", "@kenji_speedrun"],
        "target_impressions": 8500000,
        "achieved_impressions": 7900000,
        "target_engagement": 650000,
        "achieved_engagement": 612000,
        "calculated_roi": 4.6
    },
    {
        "brand_name": "Sephora",
        "campaign_title": "Clean Glow Spring Essentials",
        "target_niche": "Fashion & Lifestyle",
        "total_budget": 90000.0,
        "spent_budget": 64000.0,
        "status": "Active",
        "assigned_handles": ["@camille_parisienne", "@sierra_chic", "@kiara_threads"],
        "target_impressions": 4500000,
        "achieved_impressions": 4120000,
        "target_engagement": 340000,
        "achieved_engagement": 328000,
        "calculated_roi": 3.9
    },
    {
        "brand_name": "Airbnb",
        "campaign_title": "Live Anywhere: Remote Creators Journey",
        "target_niche": "Travel & Adventure",
        "total_budget": 110000.0,
        "spent_budget": 95000.0,
        "status": "Active",
        "assigned_handles": ["@noah_kai_nomads", "@isabella_explores", "@wilder_alps"],
        "target_impressions": 6200000,
        "achieved_impressions": 6050000,
        "target_engagement": 480000,
        "achieved_engagement": 492000,
        "calculated_roi": 4.4
    }
]

def seed_database(force: bool = False):
    """Populates MongoDB with comprehensive realistic social media analytics data"""
    db = Database.db
    if db is None:
        Database.connect_db()
        db = Database.db

    influencer_count = db["influencers"].count_documents({})
    if influencer_count > 0 and not force:
        logger.info(f"Database already contains {influencer_count} influencers. Skipping seed.")
        return {"status": "skipped", "message": f"Already seeded with {influencer_count} influencers."}

    logger.info("Starting database seeding process...")

    # Clear existing collections
    for col in ["influencers", "posts", "trends", "campaigns", "live_trend_events"]:
        db[col].delete_many({})

    # 1. Insert Influencers
    influencer_docs = []
    handle_to_id = {}
    all_handles = [p["handle"] for p in INFLUENCER_PROFILES]

    for p in INFLUENCER_PROFILES:
        city_info = random.choice(CITIES)
        # Add slight jitter to coordinates
        lng = city_info["coords"][0] + random.uniform(-0.08, 0.08)
        lat = city_info["coords"][1] + random.uniform(-0.08, 0.08)

        # Generate collaboration connections for $graphLookup
        # Connect to 2 to 4 influencers in the same or adjacent niches
        potential_peers = [h for h in all_handles if h != p["handle"]]
        collaborators = random.sample(potential_peers, min(random.randint(2, 4), len(potential_peers)))

        doc_id = ObjectId()
        handle_to_id[p["handle"]] = doc_id

        # Compute realistic rates based on followers & tier
        follower_count = p["followers"]
        post_rate = round(follower_count * random.uniform(0.008, 0.015), -1)
        video_rate = round(post_rate * random.uniform(1.6, 2.4), -1)

        # Avatar URL
        avatar_id = random.randint(1, 70)
        avatar_gender = "women" if p.get("gender") == "female" else "men"
        avatar_url = f"https://randomuser.me/api/portraits/{avatar_gender}/{avatar_id}.jpg"

        doc = {
            "_id": doc_id,
            "handle": p["handle"],
            "name": p["name"],
            "avatar": avatar_url,
            "bio": f"Passionate {p['niche']} creator sharing authentic stories, insights and workflows.",
            "niche": p["niche"],
            "platform_primary": p["platform"],
            "tier": p["tier"],
            "metrics": {
                "followers_count": follower_count,
                "following_count": random.randint(200, 1500),
                "total_posts": random.randint(120, 1400),
                "engagement_rate": p["er"],
                "avg_likes": int(follower_count * (p["er"] / 100) * 0.85),
                "avg_comments": int(follower_count * (p["er"] / 100) * 0.15),
                "credibility_score": p["cred"],
                "fake_followers_pct": round(random.uniform(2.5, 9.8), 1)
            },
            "audience_demographics": {
                "gender": {
                    "male": round(random.uniform(40, 60), 1),
                    "female": round(random.uniform(35, 55), 1),
                    "other": round(random.uniform(2, 6), 1)
                },
                "age_brackets": {
                    "18-24": round(random.uniform(28, 42), 1),
                    "25-34": round(random.uniform(35, 48), 1),
                    "35-44": round(random.uniform(10, 20), 1),
                    "45+": round(random.uniform(3, 9), 1)
                },
                "top_countries": [
                    {"country": "US", "pct": round(random.uniform(30, 45), 1)},
                    {"country": "UK", "pct": round(random.uniform(12, 22), 1)},
                    {"country": "IN", "pct": round(random.uniform(10, 20), 1)},
                    {"country": "DE", "pct": round(random.uniform(5, 12), 1)},
                    {"country": "CA", "pct": round(random.uniform(4, 10), 1)}
                ]
            },
            "collaboration_rates": {
                "post_rate_usd": float(post_rate),
                "reel_video_rate_usd": float(video_rate)
            },
            "network": {
                "collaborates_with": collaborators
            },
            "location_geo": {
                "type": "Point",
                "coordinates": [round(lng, 4), round(lat, 4)]
            },
            "location": {
                "city": city_info["city"],
                "country": city_info["country"]
            },
            "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(100, 900))
        }
        influencer_docs.append(doc)

    db["influencers"].insert_many(influencer_docs)
    logger.info(f"Inserted {len(influencer_docs)} influencers.")

    # 2. Insert Realistic Posts (Approx 1200+ posts)
    post_docs = []
    post_types = ["Video", "Reel", "Image", "Carousel", "Tweet"]

    sample_post_captions = {
        "Tech & AI": [
            "Just tested the newest neural reasoning agent and the benchmark latency dropped by 64%! The architecture is mindblowing.",
            "Why your vector database indexing matters more than your LLM parameters. Deep dive tutorial dropping tonight!",
            "Building high-concurrency microservices with Python and MongoDB Aggregation Pipelines. Here are the 5 lessons learned.",
            "Can generative AI replace senior software engineers? My honest breakdown after leading engineering for 10 years.",
            "The future of open-source AI weights vs proprietary APIs. What developers need to prepare for this quarter.",
            "Full breakdown of quantum computing progress: why fault tolerance is arriving faster than predicted."
        ],
        "Fashion & Lifestyle": [
            "Capsule wardrobe principles that will save you hours every week. Minimalist aesthetic on point.",
            "Parisian autumn street style notes: oversized wool coats, vintage leather, and earthy tones.",
            "Sustainable textiles are finally competing with fast fashion quality. Here are my favorite eco-labels.",
            "Behind the scenes at Milan Fashion Week! Incredible craft, bold silhouettes, and sustainable fabrics.",
            "5 timeless luxury investment pieces that hold or increase value over time."
        ],
        "Gaming & Esports": [
            "Unreal Engine 5.5 path tracing test running in real time at 144 FPS! Hardware is officially insane.",
            "Clutched the 1v4 overtime round in today's tournament qualifiers! GG to the squad.",
            "The top 10 indie games you must play this month. Absolute hidden masterpieces in gameplay design.",
            "Reviewing the ultimate clean desk setup for streamers and competitive players."
        ],
        "Health & Fitness": [
            "Mastering the deadlift form: 3 subtle cue adjustments to protect your lumbar spine and increase power output.",
            "Morning mobility routine you can do in 8 minutes. Your hips and lower back will thank you forever.",
            "Nutrient timing vs total daily calories: What the newest clinical sports science tells us.",
            "Completed the 42km mountain marathon! The mental grit required was beyond anything I anticipated."
        ],
        "Finance & Crypto": [
            "Interest rates, inflation indexes, and liquidity cycles explained simply. How to allocate capital in 2026.",
            "Why dividend growth investing beats chasing high yield traps every single cycle.",
            "Smart contract security checklist: The top 7 vulnerabilities that drained protocols last year.",
            "Building multiple passive cashflow streams: My transparent portfolio allocation review."
        ],
        "Food & Culinary": [
            "72-hour cold fermented Neapolitan pizza dough with 80% hydration. Listen to that crust crunch!",
            "The secret to rich, velvet French demi-glace sauce. Patience and roasted marrow bones.",
            "Street food tour of Old Delhi: Exploring century-old spice secrets and artisan clay-oven flatbreads.",
            "Testing 5 different plant-based butter alternatives for laminated croissant pastry."
        ],
        "Travel & Adventure": [
            "Watching the Northern Lights dance over the Norwegian fjords. An unforgettable spectacle of nature.",
            "Off-the-grid in Patagonia: 7 days hiking through glacial valleys and granite peaks.",
            "Hidden Kyoto: 5 tranquil zen temples away from the crowded tourist routes.",
            "Solo backpacking across the Scottish Highlands. The ultimate freedom and solitude."
        ]
    }

    now = datetime.now(timezone.utc)

    for inf in influencer_docs:
        handle = inf["handle"]
        niche = inf["niche"]
        platform = inf["platform_primary"]
        coords = inf["location_geo"]["coordinates"]
        city = inf["location"]["city"]
        followers = inf["metrics"]["followers_count"]
        er = inf["metrics"]["engagement_rate"]

        # Check if influencer is designated top influencer for any trend or matches niche
        associated_trends = [t["hashtag"] for t in TRENDS_DATA if handle in t.get("top_influencer_handles", []) or t.get("category") == niche]

        # 20 to 35 posts per influencer
        num_posts = random.randint(20, 35)
        for i in range(num_posts):
            post_date = now - timedelta(days=random.randint(0, 60), hours=random.randint(0, 23), minutes=random.randint(0, 59))
            hashtags = random.sample(NICHE_HASHTAGS[niche], min(random.randint(2, 4), len(NICHE_HASHTAGS[niche])))

            # Ensure posts for creators associated with trends include the trending hashtag
            if associated_trends and (i < 5 or random.random() < 0.35):
                trend_tag = random.choice(associated_trends)
                if trend_tag not in hashtags:
                    hashtags.append(trend_tag)
            
            # 30% chance to mention an influencer they collaborate with
            mentions = []
            if random.random() < 0.35 and inf["network"]["collaborates_with"]:
                mentions.append(random.choice(inf["network"]["collaborates_with"]))

            caption_pool = sample_post_captions.get(niche, sample_post_captions["Tech & AI"])
            caption = random.choice(caption_pool) + " " + " ".join(hashtags)

            # Sentiment calculation
            sentiment_rand = random.random()
            if sentiment_rand < 0.65:
                sentiment_label = "Positive"
                sentiment_score = round(random.uniform(0.35, 0.95), 2)
            elif sentiment_rand < 0.85:
                sentiment_label = "Neutral"
                sentiment_score = round(random.uniform(-0.1, 0.3), 2)
            else:
                sentiment_label = "Negative"
                sentiment_score = round(random.uniform(-0.85, -0.2), 2)

            # Calculate realistic engagement metrics
            base_likes = int(followers * (er / 100) * random.uniform(0.6, 1.8))
            likes = max(15, base_likes)
            comments = max(3, int(likes * random.uniform(0.04, 0.18)))
            shares = max(1, int(likes * random.uniform(0.02, 0.12)))
            saves = max(1, int(likes * random.uniform(0.05, 0.25)))
            reach = int(likes * random.uniform(5.5, 12.0))
            impressions = int(reach * random.uniform(1.2, 1.8))

            # Viral score composite (0 - 100)
            engagement_ratio = (likes + comments * 2 + shares * 3) / max(1, followers)
            viral_score = min(100.0, round(engagement_ratio * 400 + random.uniform(5, 25), 1))

            post_doc = {
                "_id": ObjectId(),
                "influencer_id": inf["_id"],
                "influencer_handle": handle,
                "platform": platform,
                "content": caption,
                "hashtags": hashtags,
                "mentions": mentions,
                "post_type": random.choice(post_types),
                "metrics": {
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "saves": saves,
                    "impressions": impressions,
                    "reach": reach,
                    "viral_score": viral_score
                },
                "sentiment": {
                    "label": sentiment_label,
                    "score": sentiment_score,
                    "emotions": {
                        "joy": round(random.uniform(0.1, 0.9), 2),
                        "curiosity": round(random.uniform(0.1, 0.8), 2),
                        "surprise": round(random.uniform(0.0, 0.5), 2)
                    }
                },
                "location": {
                    "type": "Point",
                    "coordinates": [
                        round(coords[0] + random.uniform(-0.05, 0.05), 4),
                        round(coords[1] + random.uniform(-0.05, 0.05), 4)
                    ]
                },
                "place_name": city,
                "published_at": post_date
            }
            post_docs.append(post_doc)

    db["posts"].insert_many(post_docs)
    logger.info(f"Inserted {len(post_docs)} posts.")

    # 3. Insert Trends Data
    trend_docs = []
    for t in TRENDS_DATA:
        # Generate 24 hourly data points
        hourly = []
        base_vol = t["volume_24h"] // 24
        for h in range(24):
            hour_str = f"{(now - timedelta(hours=23-h)).strftime('%H:00')}"
            factor = random.uniform(0.65, 1.45)
            # Spikes in evening hours
            if 18 <= (23-h) % 24 <= 22:
                factor *= 1.35
            hourly.append({
                "hour": hour_str,
                "volume": int(base_vol * factor)
            })

        trend_doc = {
            "_id": ObjectId(),
            "hashtag": t["hashtag"],
            "topic": t["topic"],
            "category": t["category"],
            "volume_24h": t["volume_24h"],
            "velocity_score": t["velocity_score"],
            "viral_index": t["viral_index"],
            "sentiment_summary": t["sentiment_summary"],
            "platform_breakdown": t["platform_breakdown"],
            "lifecycle_status": t["lifecycle_status"],
            "top_influencer_handles": t["top_influencer_handles"],
            "hourly_history": hourly,
            "peak_time": now - timedelta(hours=random.randint(1, 8))
        }
        trend_docs.append(trend_doc)

    db["trends"].insert_many(trend_docs)
    logger.info(f"Inserted {len(trend_docs)} trends.")

    # 4. Insert Brand Campaigns
    campaign_docs = []
    for c in BRAND_CAMPAIGNS:
        assigned = []
        fee_per_creator = c["spent_budget"] / max(1, len(c["assigned_handles"]))
        for h in c["assigned_handles"]:
            assigned.append({
                "handle": h,
                "agreed_fee": round(fee_per_creator, 2),
                "deliverables": "2 Dedicated Reels, 1 Long-form Video & 3 Story Highlights",
                "status": "Contracted"
            })

        campaign_doc = {
            "_id": ObjectId(),
            "brand_name": c["brand_name"],
            "campaign_title": c["campaign_title"],
            "target_niche": c["target_niche"],
            "total_budget": c["total_budget"],
            "spent_budget": c["spent_budget"],
            "start_date": now - timedelta(days=15),
            "end_date": now + timedelta(days=25),
            "status": c["status"],
            "assigned_influencers": assigned,
            "performance_kpis": {
                "target_impressions": c["target_impressions"],
                "achieved_impressions": c["achieved_impressions"],
                "target_engagement": c["target_engagement"],
                "achieved_engagement": c["achieved_engagement"],
                "calculated_roi": c["calculated_roi"]
            }
        }
        campaign_docs.append(campaign_doc)

    db["campaigns"].insert_many(campaign_docs)
    logger.info(f"Inserted {len(campaign_docs)} campaigns.")

    # 5. Insert Live Trend Events (TTL Index demonstration)
    live_event_docs = []
    sample_tags = ["#GenerativeAI", "#SustainableFashion", "#NextGenGaming", "#QuantumBreakthrough"]
    for _ in range(150):
        live_event_docs.append({
            "_id": ObjectId(),
            "hashtag": random.choice(sample_tags),
            "platform": random.choice(PLATFORMS),
            "event_type": random.choice(["post_published", "mention_spike", "retweet_surge"]),
            "created_at": now - timedelta(hours=random.randint(0, 18), minutes=random.randint(0, 59))
        })
    db["live_trend_events"].insert_many(live_event_docs)
    logger.info(f"Inserted {len(live_event_docs)} live trend events for TTL demonstration.")

    return {
        "status": "success",
        "counts": {
            "influencers": len(influencer_docs),
            "posts": len(post_docs),
            "trends": len(trend_docs),
            "campaigns": len(campaign_docs),
            "live_events": len(live_event_docs)
        }
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = seed_database(force=True)
    print("Seed result:", res)

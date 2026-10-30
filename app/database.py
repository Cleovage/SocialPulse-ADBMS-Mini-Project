from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT, GEOSPHERE
import logging
from app.config import settings

logger = logging.getLogger("socialpulse.db")

class DatabaseMeta(type):
    _client = None
    _db = None

    @property
    def client(cls):
        if cls._client is None:
            cls.connect_db()
        return cls._client

    @client.setter
    def client(cls, val):
        cls._client = val

    @property
    def db(cls):
        if cls._db is None:
            cls.connect_db()
        return cls._db

    @db.setter
    def db(cls, val):
        cls._db = val

class Database(metaclass=DatabaseMeta):
    @classmethod
    def connect_db(cls):
        try:
            cls._client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
            cls._db = cls._client[settings.DATABASE_NAME]
            # Verify connection
            cls._client.admin.command('ping')
            logger.info(f"Connected to MongoDB at {settings.MONGO_URI}, database: {settings.DATABASE_NAME}")
            cls.create_indexes()
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise e

    @classmethod
    def close_db(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("MongoDB connection closed.")

    @classmethod
    def get_collection(cls, name: str):
        return cls.db[name]

    @classmethod
    def create_indexes(cls):
        """
        Creates advanced indexes demonstrating ADBMS indexing concepts:
        - Unique indexes
        - Compound indexes
        - Full-text search index ($text)
        - Geospatial 2dsphere index ($geoNear, $geoWithin)
        - Multikey index (arrays)
        - TTL index (automatic document expiration)
        - Partial filter expression index
        """
        try:
            # 1. Influencers Collection Indexes
            influencers = cls.db["influencers"]
            try:
                if "idx_influencer_geo_2dsphere" in influencers.index_information():
                    influencers.drop_index("idx_influencer_geo_2dsphere")
            except Exception:
                pass
            influencers.create_index([("handle", ASCENDING)], unique=True, name="idx_handle_unique")
            influencers.create_index([("niche", ASCENDING), ("metrics.followers_count", DESCENDING)], name="idx_niche_followers_compound")
            influencers.create_index([("platform_primary", ASCENDING), ("tier", ASCENDING)], name="idx_platform_tier_compound")
            influencers.create_index([("location_geo", GEOSPHERE)], name="idx_influencer_geo_2dsphere")
            influencers.create_index([("network.collaborates_with", ASCENDING)], name="idx_collabs_multikey")
            influencers.create_index([("metrics.credibility_score", DESCENDING)], name="idx_credibility")

            # 2. Posts Collection Indexes
            posts = cls.db["posts"]
            posts.create_index([("platform", ASCENDING), ("metrics.likes", DESCENDING), ("published_at", DESCENDING)], name="idx_platform_likes_date_compound")
            posts.create_index([("influencer_handle", ASCENDING), ("published_at", DESCENDING)], name="idx_influencer_posts_compound")
            posts.create_index([("hashtags", ASCENDING)], name="idx_hashtags_multikey")
            posts.create_index([("mentions", ASCENDING)], name="idx_mentions_multikey")
            posts.create_index([("location", GEOSPHERE)], name="idx_posts_geo_2dsphere")
            posts.create_index([("content", TEXT), ("hashtags", TEXT)], name="idx_post_text_search")
            
            # Partial index: only index high-viral-score posts (saves RAM & B-tree size)
            posts.create_index(
                [("metrics.viral_score", DESCENDING)],
                partialFilterExpression={"metrics.viral_score": {"$gte": 75}},
                name="idx_partial_high_viral_posts"
            )

            # 3. Trends Collection Indexes
            trends = cls.db["trends"]
            trends.create_index([("hashtag", ASCENDING)], unique=True, name="idx_trend_hashtag_unique")
            trends.create_index([("category", ASCENDING), ("velocity_score", DESCENDING)], name="idx_category_velocity_compound")
            trends.create_index([("viral_index", DESCENDING)], name="idx_viral_index_desc")

            # 4. Campaigns Collection Indexes
            campaigns = cls.db["campaigns"]
            campaigns.create_index([("status", ASCENDING), ("target_niche", ASCENDING)], name="idx_campaign_status_niche")
            campaigns.create_index([("brand_name", ASCENDING)], name="idx_brand_name")

            # 5. Live Trend Events Collection (TTL Index)
            # Expire events older than 86400 seconds (24 hours) automatically
            events = cls.db["live_trend_events"]
            events.create_index([("created_at", ASCENDING)], expireAfterSeconds=86400, name="idx_ttl_event_24h")

            # 6. Instagram Profiles Collection Indexes
            ig_profiles = cls.db["instagram_profiles"]
            ig_profiles.create_index([("username", ASCENDING)], unique=True, name="idx_ig_username_unique")
            ig_profiles.create_index([("cached_at", DESCENDING)], name="idx_ig_cached_at")

            logger.info("Successfully ensured all ADBMS MongoDB indexes.")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")


def serialize_doc(doc):
    """Recursively serialize MongoDB document converting ObjectId & datetime to JSON primitives"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for k, v in doc.items():
            if k == "_id":
                result["id"] = str(v)
            elif isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                result[k] = serialize_doc(v)
            else:
                result[k] = v
        return result
    return doc

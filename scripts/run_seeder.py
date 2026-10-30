#!/usr/bin/env python3
"""
SocialPulse CLI Seeder
Standalone script to populate MongoDB with benchmark creators, posts, trends, campaigns, and indexes.
"""
import sys
import os
import logging

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Database
from app.seed_data import seed_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("socialpulse.cli_seeder")

def main():
    print("=" * 65)
    print("  SocialPulse ADBMS Platform - MongoDB Dataset Generator")
    print("=" * 65)
    print("Connecting to MongoDB...")
    Database.connect_db()
    
    print("Seeding database (force=True)...")
    res = seed_database(force=True)
    
    print("\n[+] Seeding successfully finished!")
    print(f"    - Influencers:   {res['counts']['influencers']}")
    print(f"    - Posts:         {res['counts']['posts']}")
    print(f"    - Trends:        {res['counts']['trends']}")
    print(f"    - Campaigns:     {res['counts']['campaigns']}")
    print(f"    - TTL Events:    {res['counts']['live_events']}")
    print("=" * 65)
    Database.close_db()

if __name__ == "__main__":
    main()

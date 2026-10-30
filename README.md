# SocialPulse: Social Media Trend & Influencer Analytics Platform
### Advanced Database Management System (ADBMS) Mini Project | MongoDB Enterprise Engine

[![MongoDB](https://img.shields.io/badge/Database-MongoDB%207.x-green?style=for-the-badge&logo=mongodb)](https://www.mongodb.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![UI](https://img.shields.io/badge/Frontend-Dark%20Glassmorphism-6366f1?style=for-the-badge)](http://localhost:8000)

SocialPulse is a full-stack, high-performance social media trend and influencer analytics platform designed for an **Advanced Database Management Systems (ADBMS)** course. Built on top of **MongoDB**, the platform highlights document modeling, advanced indexing strategies, complex aggregation pipelines, distributed transaction semantics, and query optimization via `explain('executionStats')`.

---

## 🚀 Quick Start (1-Click Run)

### Option A: Windows 1-Click Startup (Recommended)
Simply double-click or run:
```bat
run.bat
```
*This script will verify your Python environment, install required packages from `requirements.txt`, connect to MongoDB, seed benchmark data, launch the FastAPI server, and automatically open your default browser to `http://localhost:8000`.*

---

### Option B: Manual Terminal Execution

1. **Verify Prerequisites**:
   - Python 3.10+
   - Local MongoDB running on `localhost:27017`

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Populate Benchmark Dataset**:
   ```bash
   python scripts/run_seeder.py
   ```

4. **Start the Application**:
   ```bash
   python main.py
   ```

5. **Access the Platform**:
   - **Frontend Analytics SPA:** [http://localhost:8000](http://localhost:8000)
   - **Interactive Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

6. **Run Automated Test Suite & Empirical Benchmark**:
   ```bash
   python tests/test_platform.py
   python scripts/benchmark_runner.py
   ```

---

## 🏛️ ADBMS Concepts Demonstrated

| Concept | Implementation in SocialPulse | Source Code Location |
| :--- | :--- | :--- |
| **Document Modeling** | Hybrid embedding (1:1 metrics, demographics) vs Referencing (1:N posts) | [`app/models/`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/models/) |
| **Compound Indexing** | B-Tree index obeying Equality-Sort-Range rule on `{ niche: 1, 'metrics.followers': -1 }` | [`app/database.py`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/database.py) |
| **Multikey Indexes** | Indexing arrays of hashtags and mentions for $O(\log N)$ search | [`app/database.py`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/database.py) |
| **Geospatial 2dsphere** | S2 Hilbert Curve decomposition for spherical proximity search (`$geoNear`) | [`app/routers/geo.py`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/routers/geo.py) |
| **Full-Text Inverted Index** | `$text` index with linguistic tokenization on post captions | [`app/database.py`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/database.py) |
| **Partial Filter Index** | Indexing only high-viral posts (`viral_score >= 75`) to save RAM & B-tree size | [`app/database.py`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/database.py) |
| **TTL Document Eviction** | Auto-expiring ephemeral live trend events older than 24 hours | [`app/database.py`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/database.py) |
| **Dynamic Bucketing** | `$bucket` pipeline stage categorizing creators into follower tiers | [`app/routers/adbms_lab.py`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/routers/adbms_lab.py) |
| **Multi-Faceted Pipelines** | `$facet` processing multiple parallel analytics streams in 1 round-trip | [`app/routers/adbms_lab.py`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/routers/adbms_lab.py) |
| **Recursive Graph Traversal** | `$graphLookup` traversing multi-hop creator collaboration networks | [`app/routers/adbms_lab.py`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/routers/adbms_lab.py) |
| **Relational Joins** | `$lookup` & `$unwind` joining campaigns with creator collections | [`app/routers/adbms_lab.py`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/routers/adbms_lab.py) |
| **Query Optimization** | Live `explain('executionStats')` comparing `IXSCAN` vs `COLLSCAN` | [`app/routers/adbms_lab.py`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/routers/adbms_lab.py) |
| **ACID Transactions** | Multi-document atomicity via `session.start_transaction()` with commit & rollback | [`app/routers/campaigns.py`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/app/routers/campaigns.py) |

---

## 🖥️ Interactive Single-Page Application (SPA) Views

The platform includes 6 interactive views rendered in modern dark-mode glassmorphism:

### 1. Overview Dashboard
- High-level KPIs: Total Creators Tracked, Posts Analyzed, Avg Engagement Rate, Cumulative Reach.
- Interactive Chart.js Trending Velocity bar chart.
- Platform share distribution doughnut chart.
- Creator Niche Aggregation table with progress bars.
- Real-time Top 5 Viral Posts ticker sorted via compound index.

### 2. Influencer Discovery & Analytics
- Multi-parameter filter toolbar: Search (name, handle, bio), Niche, Platform, Tier, Min ER %, Min Credibility score, and Sorting.
- Creator cards with verified badges, engagement gauges, and rates.
- **Detailed Creator Profile Modal**: Performance & Demographics Radar chart, audience demographics (age distribution chart, gender split, country breakdown), recent post feed with sentiment analysis, and content format breakdown.
- **Head-to-Head Comparison Tool**: Select 2 to 4 creators and compare them side-by-side using a normalized multi-dimensional **Radar Chart**.
- **Add Creator Modal**: Insert new creator documents directly into MongoDB with unique handle constraint enforcement.

### 3. Trend Radar & Velocity
- Category filter pills (Tech & AI, Gaming, Fashion, Finance, Food, Travel).
- Trending topic cards with real-time velocity scores, viral index meters, and audience sentiment distribution bars (Positive %, Neutral %, Negative %).
- **Deep Dive Modal**: 24-hour volume progression line chart and top associated posts matching the hashtag using multikey index lookup.

### 4. Campaign Planner & ACID Transactions Lab
- Brand marketing campaigns list with budget utilization bars, impression targets, and calculated ROI.
- **Creator Matchmaker**: Recommender tool matching creators within budget limits with high credibility and engagement scores.
- **Interactive ACID Multi-Document Transaction Sandbox**: Test atomic budget allocation with options to **Commit** or **Simulate Abort/Rollback**, viewing live execution logs and WiredTiger transaction status.

### 5. Geospatial Activity Heatmap ($geoNear)
- Interactive Leaflet.js map with CartoDB DarkMatter styling.
- Global tech & creator hubs selector (San Francisco, New York, London, Tokyo, Mumbai, Berlin, Paris, Dubai, Singapore, Sydney).
- Adjustable radius distance slider (50 km to 2,500 km).
- Executes MongoDB `$geoNear` aggregation stage using spherical trigonometry to find local social media posts and creator clusters.

### 6. ADBMS Architecture & Explain Plan Lab
- **Tab 1: Side-by-Side Explain Plan Benchmark**: Executes real MongoDB `executionStats` comparing B-Tree compound index scan (`IXSCAN`) against forced collection scan (`COLLSCAN`). Demonstrates avoiding up to 90% of document scans with raw JSON inspection.
- **Tab 2: Aggregation Pipeline Runner**: Interactive runner for `$bucket`, `$facet`, `$lookup`, and `$graphLookup`, showing PyMongo pipeline code, execution latency, and formatted output.
- **Tab 3: Social Collaboration Graph**: Visualizer for `$graphLookup` displaying root creator node, traversal hops, and connected collaborator clusters.
- **Tab 4: Storage & Index Inspector**: Live catalog of all collections, document volumes, B-Tree indexes, partial filters, and TTL configurations.

---

## 🔬 Examiner & Viva Evaluation Walkthrough

Follow these steps to demonstrate key ADBMS concepts during viva examination:

1. **Demonstrate B-Tree Compound Indexing vs Full Collection Scan**:
   - Open **ADBMS Lab & Explain** from the left navigation.
   - On the **Explain Plan Benchmark** tab, click **"Run Benchmark"**.
   - Show the examiner the comparison:
     - **IXSCAN**: Only examines matching keys and documents (e.g. 145 docs).
     - **COLLSCAN**: Scans 100% of the collection (1,272 docs).
     - Point out the **88.6% scan reduction** metric and explain how B-Tree index traversal skips irrelevant disk pages.
   - Run the CLI equivalent:
     ```bash
     python scripts/benchmark_runner.py
     ```

2. **Demonstrate Dynamic Data Bucketing (`$bucket`)**:
   - Switch to the **Aggregation Pipelines** tab in the ADBMS Lab.
   - Click **"Pipeline 1: $bucket"**.
   - Point out how creators are dynamically grouped into Nano, Micro, Mid-Tier, Macro, and Mega tiers based on follower boundaries, computing average engagement rate and pricing in a single pass.

3. **Demonstrate Multi-Faceted Aggregation (`$facet`)**:
   - Click **"Pipeline 2: $facet"**.
   - Explain how 3 completely independent analytics workflows (top viral tags, top positive content, format breakdown) execute concurrently on the database server in a single round-trip.

4. **Demonstrate Recursive Graph Traversal (`$graphLookup`)**:
   - Switch to the **Social Graph ($graphLookup)** tab.
   - Select `@elena_ai_tech`, Depth: `2 Hops`, and click **"Traverse Graph"**.
   - Explain how MongoDB recursively traverses the `network.collaborates_with` array to discover peer influencer clusters without requiring SQL joins or external graph databases.

5. **Demonstrate Geospatial 2dsphere Proximity (`$geoNear`)**:
   - Navigate to **Geospatial Heatmap**.
   - Click **"San Francisco"** or **"London"**, set distance radius to 500 km, and click **"Query $geoNear"**.
   - Explain the underlying Google S2 Hilbert curve cell decomposition used by the `2dsphere` index to compute spherical distances.

6. **Demonstrate ACID Multi-Document Transactions & Rollback**:
   - Navigate to **Campaigns & ACID Lab**.
   - Scroll to the **ACID Transaction Execution Sandbox**.
   - Click **"Simulate Abort / Rollback"**.
   - Show that the transaction was aborted cleanly without modifying campaign spent budget or persisting partial state.
   - Click **"Execute & Commit Transaction"**.
   - Show the atomic mutation, updated campaign budget, and newly contracted creator.

7. **Review Academic Report**:
   - Open [`docs/ADBMS_PROJECT_REPORT.md`](file:///c:/Users/rk107/Desktop/ADBMS%20Mini%20project/docs/ADBMS_PROJECT_REPORT.md) for detailed academic sections, mathematical formulation, RDBMS comparison, and 20+ viva interview questions with answers.

---

## 📁 Repository Structure

```
.
├── app/
│   ├── config.py                 # Application configuration & MongoDB URI
│   ├── database.py               # MongoDB connection manager & index catalog
│   ├── models/                   # Pydantic schema validation models
│   │   ├── campaign.py
│   │   ├── influencer.py
│   │   ├── post.py
│   │   └── trend.py
│   ├── routers/                  # Modular FastAPI API routers
│   │   ├── adbms_lab.py          # Aggregation pipelines & explain plan endpoints
│   │   ├── campaigns.py          # Brand campaigns & ACID transaction endpoints
│   │   ├── geo.py                # $geoNear geospatial analytics
│   │   ├── influencers.py        # Creator search, filters, CRUD & comparison
│   │   ├── overview.py           # Dashboard aggregated statistics
│   │   └── trends.py             # Viral topic radar & hashtag multikey lookup
│   ├── seed_data.py              # Synthetic benchmark dataset generator
│   └── static/                   # Frontend Single-Page Application (SPA)
│       ├── css/style.css         # Dark-mode glassmorphism styles
│       ├── js/adbms_lab.js       # Pipeline runner & explain plan benchmark UI
│       ├── js/app.js             # Main SPA routing & event controllers
│       ├── js/charts.js          # Chart.js visualizations
│       └── index.html            # Main dashboard interface
├── docs/
│   └── ADBMS_PROJECT_REPORT.md   # Comprehensive university academic report
├── scripts/
│   ├── benchmark_runner.py       # Standalone CLI query optimization benchmark
│   └── run_seeder.py             # Standalone CLI dataset generator
├── main.py                       # FastAPI application entrypoint
├── requirements.txt              # Python package dependencies
├── run.bat                       # 1-Click Windows execution script
└── README.md                     # Project documentation & evaluation guide
```

---

## 📜 Academic Attribution & License
Developed as an Advanced Database Management System (ADBMS) Capstone Project demonstrating modern NoSQL database internals, indexing architectures, and analytical query execution.

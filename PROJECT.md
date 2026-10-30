# Project: SocialPulse Live Instagram Creator Lookup & Metrics

## Architecture
- **Backend**: FastAPI (`main.py`) with asynchronous routing, PyMongo singleton (`app/database.py`), data models (`app/models/`), business logic service (`app/services/instagram_service.py`), and dedicated API router (`app/routers/instagram.py`).
- **Data Flow**:
  1. Frontend sends search query (`GET /api/instagram/profile/{username}`).
  2. Router calls `InstagramService.lookup_profile(username, api_key, force_refresh)`.
  3. Service checks MongoDB cache (`instagram_profiles` / `influencers`): if cached and fresh (<24h), returns immediately with `source="cached_instagram"`.
  4. If not cached or `force_refresh=True`:
     - Tries RapidAPI (if key configured) -> computes exact ER from recent post metrics.
     - Falls back to Direct Public Crawler Scraper (`httpx` + crawler UA) -> parses exact profile metrics and computes ER.
     - Falls back to Synthetic Local Database -> matches handle in `influencers` collection.
  5. Upserts successful lookup into MongoDB (`instagram_profiles` and dual-writes/updates `influencers` collection).
  6. Returns normalized profile JSON with computed Engagement Rate and caching metadata.
  7. Frontend SPA renders rich glassmorphism profile card with formula breakdown, KPI stats, and cache indicator.
- **Frontend**: Single-Page Application (`app/static/`) with Tailwind CSS, dark glassmorphism design system (`style.css`), sidebar navigation tab (`#nav-instagram`), hero search bar, one-click suggestion chips, loading skeleton, and error fallback UI.

## Feature Inventory
| # | Feature | Description | Milestone | Source | Status |
|---|---------|-------------|-----------|--------|--------|
| 1 | Instagram Data Service & Scrapers | Multi-tier fetching engine (Cache -> RapidAPI -> Direct Crawler Scraper -> Synthetic Fallback) | M1 | Survey / R1 | DONE |
| 2 | Engagement Rate (ER) Calculation | Compute `ER = (avg_likes + avg_comments) / followers * 100` with zero-division & edge-case guards | M1 | Survey / R1 | DONE |
| 3 | MongoDB Persistence & Caching Schema | Upsert searched profiles in `instagram_profiles` & dual-write to `influencers` with timestamps | M1 | Survey / R3 | DONE |
| 4 | Instagram API Endpoints & Router | REST endpoints: `GET /api/instagram/profile/{username}`, `GET /cached`, `GET /config`, `POST /config` | M1 | Survey / R1, R4 | DONE |
| 5 | API Key Configuration (Backend) | Support `INSTAGRAM_API_KEY` / `RAPIDAPI_KEY` via env var & runtime config | M1 | Survey / R4 | DONE |
| 6 | Live Search Sidebar Tab & Section | Dedicated `#nav-instagram` tab and `#view-instagram` container matching dark glassmorphism | M2 | Survey / R2 | IN_PROGRESS |
| 7 | Search UI, Chips & Loading Skeleton | Hero search bar, 5 one-click demo chips, animated shimmer skeleton loader, status messages | M2 | Survey / R2 | IN_PROGRESS |
| 8 | Rich Profile Card & ER Breakdown | Avatar with glow, verified badge, triple KPIs, explicit mathematical formula breakdown box | M2 | Survey / R2 | IN_PROGRESS |
| 9 | Graceful Error Handling & Fallback UI | Non-crashing error card with 1-click button to search local synthetic database | M2 | Survey / R2 | IN_PROGRESS |
| 10 | API Key Settings UI Modal | Settings modal (`#modal-api-settings`) with password masking and status verification | M2 | Survey / R4 | IN_PROGRESS |
| 11 | Automated Test Suite | E2E & unit tests in `tests/test_instagram.py` and extending `tests/test_platform.py` | M3 | Survey / Acceptance | PLANNED |
| 12 | E2E Verification & GitHub Publishing | Run all test modules, server launch test, git commit & push to GitHub public repo | M4 | Follow-up / Acceptance | PLANNED |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Backend Instagram Service, Persistence & API Endpoints | `app/services/instagram_service.py`, `app/routers/instagram.py`, `app/database.py`, `main.py` | none | DONE |
| M2 | Frontend UI/UX Live Search Integration | `app/static/index.html`, `app/static/css/style.css`, `app/static/js/app.js` | M1 | IN_PROGRESS |
| M3 | Automated Testing Suite | `tests/test_instagram.py`, `tests/test_platform.py` | M1 | PLANNED |
| M4 | Final Milestone: Full E2E Pass, Server Run & GitHub Repo Publish | Pass 100% tests, test server run, git init & push public repo via `gh` | M2, M3 | PLANNED |

## Interface Contracts
### `app.services.instagram_service` ↔ `app.routers.instagram`
```python
async def lookup_profile(
    username: str,
    api_key: Optional[str] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
    ...
```

### `app.routers.instagram` ↔ Frontend SPA (`app/static/js/app.js`)
- `GET /api/instagram/profile/{username}?force_refresh={true|false}`:
  - 200 OK: Profile JSON with `status`, `username`, `full_name`, `bio`, `profile_pic_url`, `is_verified`, `metrics`, `recent_posts`, `source`, `cached_at`.
  - 404 / 400: User-friendly error details with `{"error": "...", "suggest_synthetic": true}`.
- `GET /api/instagram/config`:
  - 200 OK: `{"has_api_key": bool, "api_key_masked": Optional[str], "active_mode": "rapidapi" | "direct_crawler"}`
- `POST /api/instagram/config`:
  - Body: `{"api_key": str}`
  - 200 OK: `{"status": "updated", "has_api_key": bool}`

## Code Layout
- `app/services/instagram_service.py`: Core Instagram fetching, parsing, ER calculation, MongoDB caching logic. (M1 - DONE)
- `app/routers/instagram.py`: FastAPI endpoints. (M1 - DONE)
- `app/database.py`: MongoDB indexes and collection access. (M1 - DONE)
- `main.py`: App initialization and router mounting. (M1 - DONE)
- `app/static/index.html`: Owned exclusively by M2 Worker.
- `app/static/css/style.css`: Owned exclusively by M2 Worker.
- `app/static/js/app.js`: Owned exclusively by M2 Worker.
- `tests/test_instagram.py`: Owned exclusively by M3 Worker.
- `tests/test_platform.py`: Owned exclusively by M3 Worker.

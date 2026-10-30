# E2E Test Infra: SocialPulse Live Instagram Creator Lookup & Metrics

## Test Philosophy
- Opaque-box, requirement-driven testing based strictly on `ORIGINAL_REQUEST.md`.
- Verifies real HTTP API endpoints, MongoDB caching persistence, engagement rate mathematics, UI asset delivery, and ensures 100% pass on all existing 8 test modules without regressions.
- Methodology: 4-Tier Test Design (Category-Partition, Boundary Value Analysis, Pairwise Combinatorial Testing, Real-World Scenarios).

## Feature Inventory
| # | Feature | Source | Tier 1 | Tier 2 | Tier 3 |
|---|---------|--------|:------:|:------:|:------:|
| 1 | Live Profile Fetching (Real IG accounts) | R1 | 5 | 5 | ✓ |
| 2 | Engagement Rate (ER) Calculation Formula | R1 | 5 | 5 | ✓ |
| 3 | MongoDB Persistence & Fast Cache Retrieval | R3 | 5 | 5 | ✓ |
| 4 | Graceful Error Handling & Synthetic Fallback | R1, R2 | 5 | 5 | ✓ |
| 5 | API Key Configuration (Env Var & Runtime) | R4 | 5 | 5 | ✓ |
| 6 | Frontend Static Files & SPA Navigation Integration | R2 | 5 | 5 | ✓ |
| 7 | Full Platform Regression (Existing 8 modules) | Criteria | 5 | 5 | ✓ |

## Test Architecture
- Test runner: Python `pytest` and `fastapi.testclient.TestClient`.
- Test files:
  - `tests/test_instagram.py`: Dedicated suite for live Instagram lookup, ER calculations, MongoDB cache hits/misses, fallback triggers, and configuration endpoints.
  - `tests/test_platform.py`: Existing end-to-end regression test suite covering all 8 database and platform modules.
- Invocation command:
  ```powershell
  python -m pytest tests/test_platform.py tests/test_instagram.py -v
  ```

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Expected Outcome |
|---|----------|--------------------|------------------|
| 1 | Mega creator search (`@cristiano`) | F1, F2, F3, F6 | HTTP 200, >600M followers, valid ER %, profile saved in MongoDB |
| 2 | Instant repeat lookup (`@cristiano`) | F3 | HTTP 200, `source: cached_instagram`, latency < 20ms |
| 3 | Nonexistent username search (`@nonexistent_user_99999`) | F4 | Clean response, `suggest_synthetic: true`, no server 500 error |
| 4 | Missing API key zero-config mode | F1, F5 | Direct crawler scraper succeeds automatically without prompt barrier |
| 5 | Full system regression check | F7 | All 8 existing modules pass with 100% success rate |

## Coverage Thresholds
- Tier 1: >= 5 test cases per feature (happy path isolation)
- Tier 2: >= 5 boundary & edge cases (zero followers, private accounts, rate limits)
- Tier 3: Pairwise combinations (cached + force_refresh, api_key + direct crawler)
- Tier 4: Real-world creator queries and full platform regression

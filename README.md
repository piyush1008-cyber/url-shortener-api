# ⚡ High-Performance URL Shortener & Analytics API

[![CI](https://github.com/piyush1008-cyber/url-shortener-api/actions/workflows/ci.yml/badge.svg)](https://github.com/piyush1008-cyber/url-shortener-api/actions)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=flat&logo=sqlalchemy&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)
![Pytest](https://img.shields.io/badge/Tests-8%20Passing-brightgreen?style=flat&logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

> **A scalable, enterprise-grade URL shortening and click-telemetry microservice engineered with FastAPI, SQLAlchemy ORM, and asynchronous background task processing.**

---

## 🎯 System Architecture & Design

```
+------------------+         HTTP POST /api/v1/shorten          +----------------------+
|   Client / UI    | -----------------------------------------> |                      |
+------------------+                                            |   FastAPI Service    |
         |                                                      |                      |
         |                   HTTP GET /{short_code}             |   - Base62 Generator |
         +----------------------------------------------------> |   - Input Validator  |
                                                                |   - Collision Retry  |
                                                                +----------------------+
                                                                      |          |
                                            Async Background Telemetry|          | Sync Query
                                                                      v          v
                                                            +--------------------------+
                                                            |  Relational Persistence  |
                                                            |    - URLs Table          |
                                                            |    - ClickLogs Table     |
                                                            +--------------------------+
```

---

## 🚀 Key Features

- ⚡ **Low-Latency Redirection:** Ultra-fast HTTP 307 temporary redirects with indexing.
- 🔠 **Base62 Collision-Resistant Encoding:** 7-character random tokens offering $62^7 \approx 3.52$ trillion unique codes.
- 🏷️ **Custom Vanity Aliases:** Allows users to choose custom readable names (e.g., `my-portfolio`).
- ⏳ **Time-to-Live (TTL) & Expiration:** Configurable automatic link expiration dates.
- 📊 **Real-Time Click Analytics:** Asynchronous logging of visitor referrers, IP origins, user agents, and timestamps without adding latency to redirects.
- 🛡️ **Defensive Validation:** Strict Pydantic v2 schemas preventing open-redirect abuse and invalid URLs.
- 🧪 **100% Test Coverage:** Comprehensive unit and integration test suite using `pytest` and in-memory isolated sessions.
- 🐳 **Containerized & Production-Ready:** Includes multi-stage Dockerfile and docker-compose configurations.

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **Framework** | FastAPI | High-concurrency async Web Framework |
| **Language** | Python 3.12 | Modern runtime with type hinting |
| **ORM / Database** | SQLAlchemy 2.0 / SQLite | Relational schema modeling & persistence |
| **Validation** | Pydantic v2 | High-throughput serialization & schema validation |
| **Testing** | Pytest + Starlette TestClient | Automated unit and integration testing |
| **Deployment** | Docker & Uvicorn | Production containerization & ASGI server |

---

## 📁 Repository Structure

```
url-shortener-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization, CORS, routing
│   ├── config.py            # Environment configuration & settings
│   ├── database.py          # SQLAlchemy engine, session maker, base
│   ├── models.py            # Database tables (URLItem, ClickLog)
│   ├── schemas.py           # Pydantic v2 validation models
│   ├── crud.py              # Database operations & telemetry logging
│   ├── utils.py             # Base62 code generation & expiry computation
│   └── routers/
│       ├── __init__.py
│       ├── urls.py          # /shorten, /{short_code}, /links endpoints
│       └── analytics.py     # /analytics/{short_code} endpoint
├── tests/
│   ├── __init__.py
│   └── test_api.py          # Automated test suite (8 tests)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## ⚡ Quickstart Guide

### Option 1: Run Locally

```bash
# 1. Clone repository
git clone https://github.com/piyush1008-cyber/url-shortener-api.git
cd url-shortener-api

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate       # On Linux/macOS: source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start local development server
uvicorn app.main:app --reload --port 8000
```

Open your browser to:
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Option 2: Run with Docker

```bash
docker-compose up --build -d
```

The containerized service will be running at `http://localhost:8000`.

---

## 📡 API Reference & Examples

### 1. Shorten a URL
```bash
curl -X POST "http://localhost:8000/api/v1/shorten" \
     -H "Content-Type: application/json" \
     -d '{"original_url": "https://github.com/piyush1008-cyber", "custom_code": "my-github", "expires_in_days": 30}'
```

**Response (`201 Created`):**
```json
{
  "id": 1,
  "original_url": "https://github.com/piyush1008-cyber",
  "short_code": "my-github",
  "short_url": "http://localhost:8000/my-github",
  "created_at": "2026-11-01T11:00:00Z",
  "expires_at": "2026-12-01T11:00:00Z",
  "click_count": 0,
  "is_active": true
}
```

---

### 2. Follow Redirect
```bash
curl -i "http://localhost:8000/my-github"
```

**Response (`307 Temporary Redirect`):**
```http
HTTP/1.1 307 Temporary Redirect
location: https://github.com/piyush1008-cyber
```

---

### 3. Inspect Click Analytics
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/my-github"
```

**Response (`200 OK`):**
```json
{
  "short_code": "my-github",
  "original_url": "https://github.com/piyush1008-cyber",
  "short_url": "http://localhost:8000/my-github",
  "total_clicks": 42,
  "created_at": "2026-11-01T11:00:00Z",
  "expires_at": "2026-12-01T11:00:00Z",
  "is_expired": false,
  "top_referrers": {
    "https://linkedin.com": 28,
    "https://twitter.com": 10,
    "Direct / None": 4
  },
  "recent_clicks": [
    {
      "clicked_at": "2026-11-01T11:15:32Z",
      "referrer": "https://linkedin.com",
      "user_agent": "Mozilla/5.0 ...",
      "ip_address": "192.168.1.1"
    }
  ]
}
```

---

### 4. Deactivate a Link
```bash
curl -X DELETE "http://localhost:8000/api/v1/links/my-github"
```

---

## 🧪 Running Automated Tests

Run the full Pytest suite with verbose telemetry output:

```bash
pytest -v
```

Expected output:
```text
tests/test_api.py::test_root_and_health_endpoints PASSED                 [ 12%]
tests/test_api.py::test_shorten_url_auto_generated PASSED                [ 25%]
tests/test_api.py::test_shorten_url_custom_alias PASSED                  [ 37%]
tests/test_api.py::test_shorten_url_duplicate_custom_alias PASSED        [ 50%]
tests/test_api.py::test_shorten_url_invalid_scheme PASSED                [ 62%]
tests/test_api.py::test_redirection_and_analytics_tracking PASSED        [ 75%]
tests/test_api.py::test_redirect_not_found PASSED                        [ 87%]
tests/test_api.py::test_deactivate_link PASSED                           [100%]

============================== 8 passed in 0.77s ==============================
```

---

## 👤 Author

**Peeyoosh Kangle**
- 📧 Email: piyushkangle@gmail.com
- 🐙 GitHub: [github.com/piyush1008-cyber](https://github.com/piyush1008-cyber)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

# Recommendations Microservice

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)

Flask + SQLAlchemy service for storing simple product-to-product recommendations. The project follows the NYU DevOps microservice pattern and currently exposes endpoints to create, fetch, and delete recommendations while we continue to layer on more features.

---

## Project Overview

- Handles **cross-sell**, **up-sell**, and **accessory** recommendations.
- Implements validation (enumerated types, numeric ranges, etc.) and returns JSON error payloads via shared error handlers.
- Ships with a Makefile workflow plus pytest and lint tooling to keep development friction low.
- The root `service/` package is the live code path for `wsgi.py`. The nested `recommendations/` folder contains the original course template (UI, Swagger, BDD assets) and is kept only for reference.

### Architecture

```
Client (HTTP/JSON)
        ↓
service/routes.py (Flask views + validation)
        ↓
service/models.py (SQLAlchemy Recommendation model)
        ↓
PostgreSQL database (configured through DATABASE_URI)
```

Supporting pieces:
- `service/__init__.py` contains the Flask app factory, logging setup, and auto `db.create_all()`.
- `service/common/` holds cross-cutting helpers (error handlers, CLI commands, log handlers, HTTP status codes).
- `tests/` host unit tests powered by pytest/factory-boy; each test run wipes the database tables to keep cases isolated.

### Repository Layout

```text
dot-env-example     # sample environment file
Makefile            # install, lint, run, test, and ops helpers
Procfile            # `honcho`/Heroku process definition (gunicorn)
Pipfile(.lock)      # pipenv environment (Python 3.11)
service/            # application package (app factory, models, routes, common helpers)
tests/              # pytest suite and factories
instance/           # Flask instance dir (placeholder for future configs)
recommendations/    # archived template with UI + swagger (not executed by wsgi.py)
wsgi.py             # runtime entry point used by `flask run` / gunicorn
```

---

## Prerequisites

- Python **3.11**
- [pipenv](https://pipenv.pypa.io/) for dependency management
- Access to a PostgreSQL instance (local container or remote); update `DATABASE_URI` if you use something other than the default `postgresql+psycopg://postgres:postgres@localhost:5432/postgres`
- GNU Make (optional but recommended for the provided commands)

> Tip: you can point `DATABASE_URI` at SQLite (`sqlite:///recommendations.db`) for quick local smoke tests, but CI and course rubrics expect PostgreSQL.

---

## Local Setup & Run

### 1. Clone and install

```bash
git clone https://github.com/CSCI-GA-2820-FA25-003/recommendations
cd recommendations
pip install pipenv
pipenv install --dev
```

### 2. Configure environment variables

```bash
cp dot-env-example .env
```

Update `.env` with your values:

```
FLASK_APP=wsgi:app
PORT=8080
DATABASE_URI=postgresql+psycopg://postgres:postgres@localhost:5432/postgres
SECRET_KEY=<replace_with_make_secret_output>
LOG_LEVEL=INFO
```

Generate a random secret any time with:

```bash
pipenv run make secret
```

### 3. Start PostgreSQL (example)

```bash
docker run --name recommendations-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  -d postgres:16
```

Create a matching `testdb` database (used by pytest) or adjust the `DATABASE_URI` in `tests/test_routes.py` to point at an existing database.

### 4. Run the service

```bash
pipenv shell
make run          # uses honcho + Procfile (gunicorn) on http://localhost:8080
# or run the built-in server explicitly:
FLASK_APP=wsgi:app FLASK_ENV=development flask run -h 0.0.0.0 -p 8080
```

On startup the app factory performs `db.create_all()`, so tables are provisioned automatically.

---

## Useful Make Targets

| Target | Description |
|--------|-------------|
| `make install` | Install dependencies into the host environment (used inside containers/GitHub Codespaces). |
| `make lint` | Run flake8 + pylint with the repo defaults. |
| `make test` | Execute the pytest suite with coverage (95% threshold). |
| `make run` | Launch the service via honcho + Procfile (`web: gunicorn ...`). |
| `make clean` | Remove cached Docker layers (helpful before container builds). |
| `make secret` | Emit a random hex string you can drop into `.env`. |

Run `make help` for the full catalog, including local k3d helpers.

---

## Database Utilities

We expose a simple Flask CLI command to reset schemas:

```bash
FLASK_APP=wsgi:app pipenv run flask db-create
```

This drops and recreates every table defined by SQLAlchemy, which is useful when you change the model during development.

---

## Testing & Quality

```bash
pipenv run make lint   # style + static analysis
pipenv run make test   # pytest --pspec --cov=service --cov-fail-under=95
```

Tests expect a PostgreSQL database reachable via `postgresql+psycopg://postgres:postgres@localhost:5432/testdb`. Create that database once (e.g., `createdb testdb`) or override `DATABASE_URI` before running `pytest`. Each test cleans up rows to keep the database state deterministic.

Coverage reports live in `htmlcov/` after running `pytest --cov` if you want a detailed breakdown.

---

## API Reference

> Swagger UI has not been wired up yet (the root response references `/apidocs` for future work). Use the examples below or HTTPie/cURL for manual testing.

### `GET /`

Returns a JSON landing payload with service metadata and helper links.

### `POST /recommendations`

Create a recommendation. `Content-Type: application/json` is required.

```http
POST /recommendations
Content-Type: application/json

{
  "base_product_id": 1001,
  "recommended_product_id": 2001,
  "recommendation_type": "cross-sell",
  "status": "active",
  "confidence_score": 0.85,
  "base_product_price": 19.99,
  "recommended_product_price": 9.99,
  "base_product_description": "Bundle anchor",
  "recommended_product_description": "Add-on"
}
```

Response:

```http
201 Created
Location: unknown

{
  "recommendation_id": 1,
  "base_product_id": 1001,
  "recommended_product_id": 2001,
  "recommendation_type": "cross-sell",
  "status": "active",
  "confidence_score": 0.85,
  "base_product_price": 19.99,
  "recommended_product_price": 9.99,
  "base_product_description": "Bundle anchor",
  "recommended_product_description": "Add-on",
  "created_date": "...",
  "updated_date": "..."
}
```

Example with HTTPie:

```bash
http POST :8080/recommendations \
  base_product_id:=1001 recommended_product_id:=2001 \
  recommendation_type=cross-sell status=active confidence_score:=0.85
```

### `GET /recommendations/<recommendation_id>`

Fetch a single recommendation.

```http
GET /recommendations/1
→ 200 OK
{
  "recommendation_id": 1,
  "base_product_id": 1001,
  "recommended_product_id": 2001,
  "recommendation_type": "cross-sell",
  "status": "active",
  "confidence_score": 0.85,
  ...
}
```

`404 Not Found` is returned if the ID does not exist.

### `DELETE /recommendations/<recommendation_id>`

Remove a recommendation permanently.

```http
DELETE /recommendations/1
→ 204 No Content
```

---

### Validation Rules

- `recommendation_type` must be one of `cross-sell`, `up-sell`, or `accessory`.
- `status` must be `active` or `inactive`.
- `confidence_score` is stored as Decimal(3,2) and must be between `0` and `1`.
- Price fields are optional but, when present, must be decimals parsable by SQLAlchemy.
- Missing or invalid attributes raise a `DataValidationError` and result in a `400 Bad Request` JSON response from the error handlers defined in `service/common/error_handlers.py`.

---

## Data Model

| JSON Field | DB Column | Type | Notes |
|------------|-----------|------|-------|
| `recommendation_id` | `recommendation_id` | Integer | Primary key, auto-incremented. |
| `base_product_id` | `base_product_id` | Integer (required) | Product that is the anchor for the recommendation. |
| `recommended_product_id` | `recommended_product_id` | Integer (required) | Product being suggested. |
| `recommendation_type` | `recommendation_type` | Enum | `cross-sell`, `up-sell`, or `accessory`. |
| `status` | `status` | Enum | `active` (default) or `inactive`. |
| `confidence_score` | `confidence_score` | Numeric(3,2) | Required probability-like score in `[0, 1]`. |
| `base_product_price` | `base_product_price` | Numeric(14,2) | Optional MSRP for the base product. |
| `recommended_product_price` | `recommended_product_price` | Numeric(14,2) | Optional MSRP for the recommended product. |
| `base_product_description` | `base_product_description` | String(1023) | Optional marketing copy. |
| `recommended_product_description` | `recommended_product_description` | String(1023) | Optional description for the recommendation. |
| `created_date` | `created_date` | DateTime (UTC) | Auto-populated when `create()` is called. |
| `updated_date` | `updated_date` | DateTime (UTC) | Auto-maintained on update mutations. |

---

## Deployment

- The `Procfile` runs `gunicorn --bind 0.0.0.0:$PORT wsgi:app`, which is what `make run` orchestrates through honcho. Use it locally to mimic production or on platforms like Heroku/Render.
- `make cluster`, `make deploy`, etc., are scaffolding for running inside a local k3d cluster; supply manifests under `k8s/` (or point `kubectl` at `recommendations/k8s`) if you intend to use those targets.

---

## License

Licensed under the **Apache License 2.0**. See [LICENSE](LICENSE) for the full text.

This microservice was produced for the NYU CSCI-GA.2820 DevOps and Agile Methodologies course.

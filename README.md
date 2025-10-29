# Recommendations Microservice

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)
[![Build](https://github.com/CSCI-GA-2820-FA25-003/recommendations/actions/workflows/ciworkflow.yml/badge.svg)](https://github.com/CSCI-GA-2820-FA25-003/recommendations/actions)

This repository implements a **Recommendations Microservice** built with Flask and SQLAlchemy.  
It follows the NYU DevOps microservice architecture template and supports RESTful endpoints for managing product recommendations.

---

## Overview

This project provides a backend service for managing product-to-product recommendations, such as **cross-sell**, **up-sell**, or **accessory** suggestions.  
It includes a data model, Flask API routes, test cases, and Docker/Makefile workflows for development and deployment.

### Quickstart (Local Setup)

```bash
# Clone repository
git clone https://github.com/CSCI-GA-2820-FA25-003/recommendations
cd recommendations

# Use Python 3.11 with Pipenv
pip install pipenv
pipenv install --dev
pipenv shell

# Copy environment variables
cp dot-env-example .env

# Run service
make run
# or
flask run -h 0.0.0.0 -p 8080
```

The service will be available at:  
👉 **http://localhost:8080**

---

## Automatic Setup

The repository can be initialized as a GitHub template by pressing the green **“Use this template”** button.  
This allows your team to create a new repository based on this scaffold.

---

## Manual Setup

You can also manually copy starter code into an existing project.  
If you do this, ensure you also copy hidden files that some GUI file managers may skip:

```bash
cp .gitignore      ../<your_repo_folder>/
cp .gitattributes  ../<your_repo_folder>/
```

For configuration, copy the provided `dot-env-example` and update as needed:

```
FLASK_APP=wsgi:app
PORT=8080
DATABASE_URI=postgresql+psycopg://postgres:postgres@localhost:5432/postgres
SECRET_KEY=
LOG_LEVEL=INFO
```

---

## Contents

```text
.gitignore          - ignores unnecessary files
.gitattributes      - handles CRLF line endings
dot-env-example     - environment variables sample
Pipfile             - Pipenv dependency manager (Python 3.11)
Procfile            - Gunicorn entry for deployment
Makefile            - developer tasks (install/lint/test/run/deploy)
setup.cfg           - lint/test configuration
wsgi.py             - WSGI entry point (create_app())

service/                   - main application package
├── __init__.py            - Flask app factory
├── config.py              - configuration settings
├── models.py              - SQLAlchemy model (Recommendation)
├── routes.py              - REST API routes
└── common/                - helper modules (CLI, logging, errors, status codes)

tests/                     - pytest suite
├── factories.py           - data factories
├── test_cli_commands.py   - CLI tests
├── test_models.py         - model tests
└── test_routes.py         - route tests
```

---

## Makefile Commands

Common developer commands:

```bash
make install     # install dependencies
make lint        # check code style
make format      # auto-format with black/isort
make test        # run all tests
make coverage    # run tests with coverage
make run         # run Flask locally (wsgi:app)
make build/push  # container image build & push
make deploy      # deploy to local Kubernetes cluster
```

> Run `make help` to view all available targets.

---

## API Overview

The following section provides **example API calls**, including request and response structures to guide developers during testing and integration.

### Root Endpoint

```
GET /
→ 200 OK
```
Returns a simple landing page text.

---

### Create a Recommendation

#### Example Request
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
  "base_product_description": "Base product",
  "recommended_product_description": "Accessory"
}
```

#### Example Response
```http
201 Created
Location: /recommendations/1

{
  "id": 1,
  "base_product_id": 1001,
  "recommended_product_id": 2001,
  "recommendation_type": "cross-sell",
  "status": "active",
  "confidence_score": 0.85
}
```

---

### Read a Recommendation

#### Example Request
```http
GET /recommendations/1
```

#### Example Response
```http
200 OK

{
  "id": 1,
  "base_product_id": 1001,
  "recommended_product_id": 2001,
  "recommendation_type": "cross-sell",
  "status": "active",
  "confidence_score": 0.85
}
```

---

### Update a Recommendation

#### Example Request
```http
PUT /recommendations/1
Content-Type: application/json

{
  "status": "inactive",
  "confidence_score": 0.6
}
```

#### Example Response
```http
200 OK

{
  "id": 1,
  "base_product_id": 1001,
  "recommended_product_id": 2001,
  "recommendation_type": "cross-sell",
  "status": "inactive",
  "confidence_score": 0.6
}
```

---

### Delete a Recommendation

#### Example Request
```http
DELETE /recommendations/1
```

#### Example Response
```http
204 No Content
```

---

### List All Recommendations

#### Example Request
```http
GET /recommendations
```

#### Example Response
```http
200 OK

[
  {
    "id": 1,
    "base_product_id": 1001,
    "recommended_product_id": 2001,
    "recommendation_type": "cross-sell",
    "status": "active"
  },
  {
    "id": 2,
    "base_product_id": 3001,
    "recommended_product_id": 4001,
    "recommendation_type": "up-sell",
    "status": "inactive"
  }
]
```

---

## Data Model

The `Recommendation` model is defined in `service/models.py` using SQLAlchemy.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| base_product_id | Integer | ID of the base product |
| recommended_product_id | Integer | ID of the recommended product |
| recommendation_type | Enum | `"cross-sell"`, `"up-sell"`, `"accessory"` |
| status | Enum | `"active"` or `"inactive"` |
| confidence_score | Numeric(3,2) | Confidence value (e.g., 0.85) |
| base_product_price | Numeric(14,2) | Optional |
| recommended_product_price | Numeric(14,2) | Optional |
| base_product_description | String(1023) | Optional |
| recommended_product_description | String(1023) | Optional |
| created_date | DateTime | Auto timestamp |
| updated_date | DateTime | Auto timestamp |

---

## Database

Configured for **PostgreSQL** by default:

```
postgresql+psycopg://postgres:postgres@localhost:5432/postgres
```

Tables are created automatically on app startup with `db.create_all()`.

---

## Testing

Run unit tests with:

```bash
make test
# or
pytest -q
```

Generate a coverage report:

```bash
make coverage
```

Tests are located in the `/tests` directory.

---

## Deployment

Production uses **Gunicorn** via the `Procfile`:

```
web: gunicorn --bind 0.0.0.0:$PORT wsgi:app
```

Docker and Kubernetes helpers are available through the Makefile (`make build`, `make cluster`, `make deploy`).

---

## License

Licensed under the **Apache License 2.0**.  
See [LICENSE](LICENSE) for details.

This repository is part of the **NYU CSCI-GA.2820 DevOps and Agile Methodologies** course.

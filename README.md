# Recommendations Microservice

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)

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
👉 **http://127.0.0.1:8080**

---

## API Overview

### Root Endpoint
```
GET /
→ 200 OK
```
Returns a simple landing page text.

---

### Create a Recommendation
```
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

→ 201 Created
Location: /recommendations/<id>
```

---

### Read a Recommendation
```
GET /recommendations/<id>
→ 200 OK | 404 Not Found
```
Retrieves a single recommendation by its ID.

---

### List All Recommendations
```
GET /recommendations
→ 200 OK
```
Returns a list of all recommendations.  
Optionally supports query parameters such as:
```
/recommendations?type=cross-sell&status=active
```

---

### Update a Recommendation
```
PUT /recommendations/<id>
Content-Type: application/json

{
  "status": "inactive",
  "confidence_score": 0.72
}

→ 200 OK | 404 Not Found
```
Updates one or more fields of an existing recommendation.

---

### Delete a Recommendation
```
DELETE /recommendations/<id>
→ 204 No Content | 404 Not Found
```
Deletes a specific recommendation from the database.

---

> ✅ With these endpoints, the service now supports full **CRUD** operations:
> **Create**, **Read**, **Update**, and **Delete**, plus **List** for retrieving multiple records.

---

## Roadmap

- [x] Add Read (CRUD terminology) instead of Retrieve
- [x] Document List, Update, and Delete endpoints
- [ ] Implement `GET /recommendations` (list all or filter by status/type)
- [ ] Add `PUT` and `DELETE` endpoints in the Flask app
- [ ] Add `Location` header in POST response dynamically
- [ ] Improve factory seeding for integration testing
- [ ] CI pipeline with GitHub Actions

---

## License

Licensed under the **Apache License 2.0**.  
See [LICENSE](LICENSE) for details.

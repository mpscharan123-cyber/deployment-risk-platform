# Backend Technical Report: Deployment Risk Platform

## 1. Architecture Overview
The backend of the platform is designed as a distributed, decoupled architecture consisting of a primary API Gateway and a dedicated Machine Learning Inference Service. Both services are built using **FastAPI** (Python 3) to leverage native asynchronous capabilities, robust Pydantic data validation, and automatic OpenAPI documentation generation.

- **Main API Gateway**: `backend/main.py`
- **ML Inference Service**: `ml_service/main.py`

---

## 2. Core Modules & Components

### 2.1 Routing and Endpoints (`main.py`)
The primary gateway handles all incoming traffic from the frontend and external CI/CD webhooks. 
- **Authentication**: Exposes `/api/auth/token` and `/api/auth/register` endpoints.
- **Synchronous Actions**: Handles fast database queries for dashboards (`/api/deployments`, `/api/risk-history`, `/api/analytics`).
- **Asynchronous Background Processing**: When a new deployment is registered via `POST /api/deployments`, the gateway immediately acknowledges the request (HTTP 200) and delegates the heavy ML analysis pipeline to FastAPI's `BackgroundTasks`.

### 2.2 Data Validation (`schemas.py`)
Relies on **Pydantic** models to rigorously enforce the schema of incoming HTTP requests and outgoing JSON responses. 
- E.g., `RiskPredictionRequest` strictly types the features required by the ML model (`files_changed`, `lines_added`, `author`, etc.), guaranteeing that the ML service never receives malformed data.

### 2.3 ORM & Database (`models.py` & `database.py`)
The platform uses **SQLAlchemy** as its Object-Relational Mapper (ORM).
- **Graceful Fallback**: It attempts to connect to PostgreSQL via the `DATABASE_URL` environment variable. If unavailable (like in local dev), it falls back to a local `sqlite:///./test.db`.
- **Relational Models**: Defines one-to-many and one-to-one relationships between `User`, `Deployment`, `CodeChange`, and `RiskPrediction`.

### 2.4 External Integrations
- **GitHub Analyzer (`github_analyzer.py`)**: Responsible for fetching real-time code deltas (lines added/deleted, files changed) from GitHub repositories using personal access tokens.
- **Rules Engine (`rules_engine.py`)**: A configurable module that interprets raw ML scores (e.g., `85.4`) and converts them into actionable, human-readable recommendations (e.g., "Senior Staff Approval Required").

---

## 3. Security & Authentication (`auth.py`)
- **JSON Web Tokens (JWT)**: Used for stateless authentication across the microservices. Tokens are signed using the `jose` library with a standard 30-minute expiration window.
- **Password Hashing**: Employs `passlib` wrapping `bcrypt` to salt and hash all user passwords before database insertion. (Note: A known deprecation warning with newer `bcrypt` versions is trapped and handled gracefully).
- **CORS Middleware**: Implemented at the API gateway level to restrict cross-origin requests exclusively to trusted frontend domains.

---

## 4. Machine Learning Inference Service
The ML engine is decoupled from the main gateway to allow for asymmetric scaling (e.g., throwing more GPU/CPU resources solely at inference without wasting resources on standard CRUD endpoints).

- **Interaction**: The Main Gateway sends a synchronous POST request to the ML Service over the internal network.
- **The Payload**: The ML service receives the extracted code metrics and passes them into the pre-trained **XGBoost Classifier**.
- **XAI Integration**: Alongside the quantitative risk score, the service computes **SHAP** values to provide Explainable AI reasoning back to the user, answering *why* a specific score was generated.

---

## 5. Performance and Concurrency
By utilizing FastAPI's `async def` routing and `BackgroundTasks`, the main thread is never blocked during long I/O operations (like querying GitHub APIs or awaiting the ML model). This architecture guarantees that the API remains responsive to frontend dashboard polling, even under high load during peak deployment hours.

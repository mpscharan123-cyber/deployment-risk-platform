# Backend API Documentation: AI-Based Deployment Risk Prediction Platform

## 1. Overview
The backend is built using **FastAPI** (Python) due to its high performance, native asynchronous support, and automatic OpenAPI (Swagger) documentation generation. It uses **PostgreSQL** for persistence via SQLAlchemy and implements **JWT Authentication** for security.

### 1.1 Middleware & Security Practices
- **CORS Middleware**: Configured to restrict cross-origin requests to trusted frontend domains.
- **JWT Authentication**: All sensitive routes are protected by an `OAuth2PasswordBearer` dependency. Tokens expire every 30 minutes.
- **Password Hashing**: Passwords are never stored in plain text; they are hashed using the `bcrypt` algorithm.
- **Rate Limiting (Future)**: Placed behind an API Gateway/Load Balancer to prevent DDoS attacks.
- **Exception Handling**: A global exception handler catches unhandled errors and returns standardized JSON responses to prevent stack trace leakage.

---

## 2. API Endpoints

### 2.1 User Authentication

#### `POST /api/auth/register`
Creates a new DevOps/Admin user.
- **Request Body**:
  ```json
  {
    "username": "sarah_ops",
    "email": "sarah@company.com",
    "password": "securepassword123",
    "full_name": "Sarah Connor",
    "role": "Release Manager"
  }
  ```
- **Success Response (200 OK)**: Returns user ID and details (excluding password).
- **Error Handling**: Returns `400 Bad Request` if the username or email already exists.

#### `POST /api/auth/token`
Authenticates a user and returns a JWT access token.
- **Request Body** (Form Data): `username`, `password`
- **Success Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI...",
    "token_type": "bearer"
  }
  ```

---

### 2.2 Upload Deployment Data & Predict Risk

#### `POST /api/deployments`
Registers a new deployment attempt and triggers the background ML analysis pipeline.
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "commit_hash": "a1b2c3d4e5f6",
    "author": "sarah_ops",
    "code_changes": {
      "lines_added": 1540,
      "lines_deleted": 20,
      "files_changed": 15
    }
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "id": 104,
    "commit_hash": "a1b2c3d4e5f6",
    "author": "sarah_ops",
    "status": "pending_ml_analysis",
    "timestamp": "2026-05-19T10:00:00Z"
  }
  ```

#### `POST /api/predict-risk`
A synchronous endpoint to instantly test risk predictions without saving to the database. Acts as a proxy to the ML Microservice.
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "files_changed": 15,
    "lines_added": 1540,
    "lines_deleted": 20,
    "author": "sarah_ops",
    "time_of_deployment": 14,
    "previous_failures": 1,
    "code_complexity": 8.5
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "risk_score": 89.5,
    "risk_level": "High Risk",
    "recommendation": "Senior Staff Approval Required",
    "is_anomaly": true,
    "shap_values": {
      "lines_added": 40.5,
      "previous_failures": 15.0
    }
  }
  ```

---

### 2.3 Fetch Deployment History

#### `GET /api/deployments`
Retrieves a paginated list of all historical deployments.
- **Headers**: `Authorization: Bearer <token>`
- **Query Params**: `skip` (default: 0), `limit` (default: 50)
- **Success Response (200 OK)**:
  ```json
  [
    {
      "id": 104,
      "commit_hash": "a1b2c3d4e5f6",
      "status": "flagged_high_risk",
      "timestamp": "2026-05-19T10:00:00Z"
    }
  ]
  ```

#### `GET /api/risk-history`
Retrieves historical risk scoring data for trend analysis.
- **Success Response (200 OK)**: Returns a list of ML scores and anomaly flags tied to deployment IDs.

---

### 2.4 Approval Recommendation API & Remediation

#### `GET /api/approval-recommendation/{deployment_id}`
Fetches the system's final approval routing recommendation and remediation suggestions based on the ML output and active rule thresholds.
- **Headers**: `Authorization: Bearer <token>`
- **Path Params**: `deployment_id` (Integer)
- **Success Response (200 OK)**:
  ```json
  {
    "deployment_id": 104,
    "risk_score": 89.5,
    "risk_level": "High Risk",
    "recommendation": "Reject & Request Review",
    "required_approval": "Senior Staff",
    "reasoning": "High risk detected. SHAP Values indicate excessive lines added (1540) by an author with previous outage history.",
    "remediation_suggestions": [
      "Break this commit into smaller, isolated PRs.",
      "Increase unit test coverage for the modified modules before proceeding."
    ],
    "estimated_delay_hours": 24
  }
  ```
- **Error Handling**: Returns `404 Not Found` if the ML engine hasn't finished scoring the deployment yet.

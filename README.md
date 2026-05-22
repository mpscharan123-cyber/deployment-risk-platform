# 🚀 AI-Based Deployment Risk Prediction Platform

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)
![React](https://img.shields.io/badge/React-18.2-61DAFB.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.103-009688.svg)

A production-ready, microservices-based system designed to predict and gate deployment risks using Machine Learning (XGBoost), historical outage analysis, and a configurable AI Rule Engine.

## 📖 Overview
Modern CI/CD pipelines move fast, but unit tests alone cannot predict complex architectural failures or human-centric risks. This platform acts as an **Intelligent Gatekeeper**, analyzing incoming code changes, developer experience, and historical data to predict the likelihood of a deployment causing a production outage.

### ✨ Key Features
- **🧠 ML Inference Engine**: Uses **XGBoost** for risk scoring (0-100) and **Isolation Forest** for anomaly detection.
- **🔍 Explainable AI (XAI)**: Generates SHAP values so developers understand exactly *why* a deployment was flagged (e.g., "High Risk due to 1500 lines changed by a junior developer").
- **🛡️ Automated CI/CD Gating**: Headless REST API designed to block risky pull requests in GitHub Actions, GitLab, or Jenkins.
- **📊 Modern Dashboard**: Premium dark-mode React UI for Release Managers to monitor deployments, view risk trends, and manually override system blocks.
- **🔐 Enterprise Security**: JWT Authentication, Role-Based Access Control (RBAC), and PostgreSQL database persistence.

---

## 🏗️ System Architecture
The platform is fully containerized using Docker and is split into decoupled microservices:

1. **Frontend (React.js/Vite)**: The visual command center for release managers.
2. **Backend Gateway (FastAPI)**: Handles CI/CD webhooks, routing, auth, and the Rules Engine.
3. **ML Service (FastAPI)**: A dedicated, compute-heavy inference service running the XGBoost model.
4. **Database (PostgreSQL)**: Stores deployment history, audit logs, and override justifications.

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (If running without Docker)
- Node.js 18+

### Quick Start
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/deployment-risk-platform.git
   cd deployment-risk-platform
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=riskplatform
   DATABASE_URL=postgresql://postgres:postgres@db:5432/riskplatform
   ML_SERVICE_URL=http://ml_service:8001
   ```

3. **Train the ML Model:**
   Before launching, generate the `risk_model.pkl` artifact.
   ```bash
   cd ml_service
   pip install -r requirements.txt
   python train_model.py
   cd ..
   ```

4. **Launch the Stack:**
   ```bash
   docker-compose up --build
   ```

5. **Access the Platform:**
   - **Frontend UI**: `http://localhost:5173`
   - **Backend API Docs (Swagger)**: `http://localhost:8000/docs`
   - **ML Service Docs**: `http://localhost:8001/docs`

---

## 🔌 CI/CD Integration
To integrate with GitHub Actions, add the following step to your deployment YAML:

```yaml
- name: Query AI Risk Platform
  run: |
    RESPONSE=$(curl -s -X POST "https://your-risk-api.com/api/predict-risk" \
      -H "Authorization: Bearer ${{ secrets.RISK_TOKEN }}" \
      -H "Content-Type: application/json" \
      -d "{\"files_changed\": 15, \"lines_added\": 300, \"lines_deleted\": 20, \"author\": \"${{ github.actor }}\"}")
    
    RISK_LEVEL=$(echo $RESPONSE | jq -r '.risk_level')
    if [ "$RISK_LEVEL" == "High Risk" ]; then
      echo "::error::Deployment blocked by AI. High Risk Detected."
      exit 1
    fi
```

---

## 📜 Documentation Map
For deeper technical dives, refer to the included project documentation files:
- `Feature_Requirements.md`: Functional and Non-Functional specs.
- `System_Architecture.md`: Detailed component layout and data flow.
- `Database_Design.md`: PostgreSQL schemas and ER Diagrams.
- `Backend_API_Documentation.md`: Complete REST API contracts.
- `CICD_Integration.md` & `Cloud_Deployment.md`: DevOps guides for AWS/Azure.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](#).

## 📄 License
This project is licensed under the MIT License.

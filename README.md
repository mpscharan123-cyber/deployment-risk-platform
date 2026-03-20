# AI-Based Deployment Risk Prediction Platform

A production-ready system to predict and gate deployment risks using XGBoost machine learning, GitHub historical analysis, and a configurable AI rule engine.

## 🚀 Overview
This platform analyzes incoming code changes and predicts the likelihood of deployment failure or architectural risk. It provides a visual dashboard for release managers and an automated gating mechanism for CI/CD pipelines.

### Key Features
- **📊 AI Dashboard**: Premium glassmorphism UI for risk visualization (React + Recharts).
- **🧠 ML Inference**: XGBoost-powered risk scoring (0-100) and classification (Low/Med/High).
- **🔗 GitHub Integration**: Real-time analysis of commit deltas, file impact, and contributor history.
- **🛡️ Approval Gatekeeper**: Configurable rule engine for multi-level release approvals (Auto/Manager/Senior).
- **⚙️ CI/CD Gating**: Headless Python script for automated PR blocking based on risk thresholds.

---

## 🏗️ Architecture
The system follows a microservices-based approach orchestrated via Docker:
- **Backend (FastAPI)**: Primary API Gateway, Database interaction, and Rule Engine.
- **ML Service (FastAPI)**: Dedicated inference service for XGBoost predictions.
- **Frontend (React/Vite)**: Modern SPA with Vanilla CSS design system.
- **Database (PostgreSQL)**: Persistent storage for deployments and risk history.

---

## 🛠️ Getting Started

### Prerequisites
- Docker & Docker Compose
- GitHub Personal Access Token (for `GITHUB_TOKEN`)

### Quick Start (Local Development)
1. **Clone the repository.**
2. **Create a `.env` file** in the root:
   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=riskplatform
   DATABASE_URL=postgresql://postgres:postgres@db:5432/riskplatform
   GITHUB_TOKEN=your_github_token_here
   ML_SERVICE_URL=http://ml_service:8001
   ```
3. **Launch the stack:**
   ```bash
   docker-compose up --build
   ```
4. **Access the services:**
   - **Frontend**: `http://localhost:5173`
   - **API Docs (Swagger)**: `http://localhost:8000/docs`
   - **ML Docs**: `http://localhost:8001/docs`

---

## 📋 API Documentation
The backend provides interactive Swagger documentation. Key namespaces include:
- `Data`: Create and list deployments.
- `Analysis`: GitHub code analysis and AI recommendations.
- `Rules`: Real-time configuration for risk thresholds.

---

## 🌩️ Cloud Deployment
Refer to [deployment_guide.md](./deployment_guide.md) for detailed instructions on deploying to **AWS** (EC2/RDS/S3) or **Azure** (App Service/SQL/Blob).

---

## 🛡️ Security & Best Practices
- **Environment Driven**: No secrets are hardcoded in source.
- **Background Processing**: Heavy ML tasks are handled via FastAPI BackgroundTasks to keep the main event loop responsive.
- **CORS Restricted**: Production middleware configured to prevent unauthorized access.
- **Explainable AI**: Every prediction includes a `reasoning` field describing the weighted factors.

---

## 📜 License
Internal Enterprise Use Only.

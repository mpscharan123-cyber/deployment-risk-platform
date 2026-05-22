# Cloud Deployment: AI-Based Deployment Risk Prediction Platform

## 1. Overview
The platform leverages a microservices architecture that is natively containerized, making it highly portable. This guide covers the deployment strategy for both Amazon Web Services (AWS) and Microsoft Azure, encompassing Docker containerization, Kubernetes orchestration, and serverless background tasks.

---

## 2. Docker Containerization
The system is built on three core containers:
1. **Frontend (React/Vite)**: Served via an Nginx container.
2. **Backend API (FastAPI)**: Runs via Uvicorn.
3. **ML Engine (FastAPI/XGBoost)**: A dedicated high-compute container for inference.

### 2.1 Docker Compose (Local & Sandbox)
```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: riskplatform

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db, ml_service]
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/riskplatform
      ML_SERVICE_URL: http://ml_service:8001

  ml_service:
    build: ./ml_service
    ports: ["8001:8001"]

  frontend:
    build: ./frontend
    ports: ["5173:80"]
```

---

## 3. AWS Deployment Strategy

### 3.1 Services Used
- **Compute**: Amazon EC2 / ECS (Elastic Container Service) for hosting the Backend and ML containers.
- **Database**: Amazon RDS for PostgreSQL.
- **Storage**: Amazon S3 to store historical `risk_model.pkl` artifacts and outage logs.
- **Serverless**: AWS Lambda for triggering asynchronous retraining of the ML model.
- **Monitoring**: Amazon CloudWatch for collecting container logs and tracking API latencies.

### 3.2 Deployment Steps (AWS ECS + RDS)
1. **Database Setup**: Provision an RDS PostgreSQL instance in a private subnet. Store credentials in AWS Secrets Manager.
2. **Push to ECR**: Authenticate Docker to Amazon Elastic Container Registry (ECR) and push the `backend`, `ml_service`, and `frontend` images.
3. **ECS Task Definitions**: Create Task Definitions for the containers. The ML Service should be allocated a higher CPU/Memory ratio.
4. **Application Load Balancer (ALB)**: Route public traffic to the `frontend` container, and `/api/*` traffic to the `backend` container. The `ml_service` remains entirely internal.
5. **Model Retraining**: Configure a CloudWatch Event to trigger an AWS Lambda function weekly. The Lambda pulls data from RDS, trains a new model, and uploads the new `.pkl` to S3.

---

## 4. Azure Deployment Strategy

### 4.1 Services Used
- **Compute**: Azure App Service (Containers) or Azure Kubernetes Service (AKS).
- **Database**: Azure Database for PostgreSQL (Flexible Server).
- **Serverless**: Azure Functions for background rule evaluation and notifications.
- **Monitoring**: Azure Monitor & Application Insights for deep application telemetry.

### 4.2 Deployment Steps (Azure App Service)
1. **Provision DB**: Create an Azure Database for PostgreSQL in a VNet.
2. **Azure Container Registry (ACR)**: Build and push the Docker images to ACR.
3. **App Service Creation**: 
   - Create a Web App for Containers (Frontend).
   - Create a Web App for Containers (Backend API).
   - Create a Web App for Containers (ML Engine).
4. **Networking**: Configure VNet Integration so the Backend can securely communicate with the Database and the internal ML Engine without exposing them to the internet.
5. **Continuous Deployment**: Link the App Services to ACR to enable auto-deployments when a new image tag (e.g., `latest`) is pushed via the CI/CD pipeline.

---

## 5. Kubernetes Support (EKS / AKS)
For enterprise-scale, the platform should be deployed using Kubernetes to ensure high availability and auto-scaling of the ML Engine during peak deployment hours.

- **Deployments**: Define replica sets (e.g., `replicas: 3` for Backend, `replicas: 2` for ML Engine).
- **Services**: Use `ClusterIP` to expose the ML Engine to the Backend internally, and a `LoadBalancer` or `Ingress` controller to expose the Frontend.
- **Horizontal Pod Autoscaler (HPA)**: Configure HPA to scale the `ml_service` pods if CPU utilization exceeds 75% when processing large code diffs.

---

## 6. Security Best Practices
- **Network Isolation**: Only the Application Load Balancer/Ingress should have a public IP. Databases and ML inference servers must reside in private subnets/VNets.
- **Secret Management**: Never hardcode database URIs or JWT secrets. Use AWS Secrets Manager or Azure Key Vault and inject them into containers at runtime.
- **Least Privilege IAM**: The AWS Lambda or Azure Function responsible for retraining the model should only have `READ` access to the DB and `WRITE` access to the specific S3 Bucket/Blob Storage.
- **WAF**: Enable AWS WAF or Azure Front Door to protect the public API endpoints from SQL injection and cross-site scripting (XSS).

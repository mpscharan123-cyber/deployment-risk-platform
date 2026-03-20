# Cloud Deployment Guide: Risk Prediction Platform

This guide outlines the production deployment of the Deployment Risk Prediction Platform on AWS and Azure using containerized microservices.

## 1. Shared Prerequisites
- Docker & Docker Compose installed locally.
- Cloud CLI (AWS CLI or Azure CLI) configured.
- Container Registry (AWS ECR or Azure Container Registry).

---

## 2. AWS Deployment (EC2 + RDS + S3)

### Service Architecture
- **Backend/ML Service**: Hosted on **EC2** using Docker.
- **Database**: **Amazon RDS (PostgreSQL)** for persistence.
- **Storage**: **Amazon S3** for exported risk reports and logs.

### Step-by-Step AWS Setup
1. **Provision RDS PostgreSQL:**
   ```bash
   aws rds create-db-instance --db-instance-identifier risk-db --db-instance-class db.t3.micro --engine postgres --allocated-storage 20 --master-username postgres --master-user-password YOUR_PASSWORD
   ```
2. **Create S3 Bucket:**
   ```bash
   aws s3 mb s3://risk-platform-storage-unique-id
   ```
3. **Launch EC2 & Deploy Container:**
   - Launch an Ubuntu-based EC2 instance.
   - Install Docker.
   - Pull your images and run using `docker-compose`:
     ```bash
     DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@your-rds-endpoint:5432/riskplatform \
     S3_BUCKET=risk-platform-storage-unique-id \
     docker-compose up -d
     ```

---

## 3. Azure Deployment (App Service + Azure SQL + Blob Storage)

### Service Architecture
- **Backend/ML Service**: **Azure App Service for Containers**.
- **Database**: **Azure SQL for PostgreSQL (Flexible Server)**.
- **Storage**: **Azure Blob Storage**.

### Step-by-Step Azure Setup
1. **Provision Azure Database for PostgreSQL:**
   ```az
   az postgres flexible-server create --resource-group RiskRG --name risk-db-server --admin-user myadmin --admin-password YOUR_PASSWORD --sku-name Standard_B1ms
   ```
2. **Setup Blob Storage:**
   ```az
   az storage account create --name riskstorageaccount --resource-group RiskRG --location eastus --sku Standard_LRS
   az storage container create --name reports --account-name riskstorageaccount
   ```
3. **Deploy Web App for Containers:**
   ```az
   az webapp create --resource-group RiskRG --plan MyPlan --name risk-backend-app --deployment-container-image-name myregistry.azurecr.io/risk-backend:latest
   ```

---

## 4. Production Environment Variables (.env)

| Variable | Description | Example (AWS) | Example (Azure) |
|----------|-------------|---------------|-----------------|
| `DATABASE_URL` | DB Connection String | `postgresql://user:pass@rds-host:5432/db` | `postgresql://user:pass@pg-server.postgres.database.azure.com:5432/db` |
| `ML_SERVICE_URL` | Internal/External ML URL | `http://ml_service:8001` | `https://risk-ml-app.azurewebsites.net` |
| `STORAGE_BUCKET` | S3 or Blob Container name | `risk-platform-s3` | `risk-blob-container` |
| `GITHUB_TOKEN` | Auth for GitHub Analysis | `ghp_yourtoken` | `ghp_yourtoken` |

---

## 5. Docker Production Hardening
Use the following command for production-ready orchestration with persistent volume mapping:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

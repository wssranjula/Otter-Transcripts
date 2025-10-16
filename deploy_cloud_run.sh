#!/bin/bash
# Deploy Google Drive RAG Pipeline to Cloud Run

# Configuration
PROJECT_ID="your-gcp-project-id"
SERVICE_NAME="gdrive-rag-pipeline"
REGION="us-central1"

# Build and push container
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --no-allow-unauthenticated \
  --memory 2Gi \
  --timeout 3600 \
  --set-env-vars PYTHONUNBUFFERED=1

# Set up Cloud Scheduler to run every hour
gcloud scheduler jobs create http ${SERVICE_NAME}-scheduler \
  --schedule="0 * * * *" \
  --uri="https://${SERVICE_NAME}-${PROJECT_ID}.a.run.app" \
  --http-method=POST \
  --oidc-service-account-email=${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com

echo "Deployment complete! The pipeline will run every hour."

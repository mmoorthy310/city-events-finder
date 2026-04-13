#!/bin/bash
set -e

PROJECT_ID="synthetix-gcp-project"
REGION="us-central1"
SERVICE_NAME="city-events-finder"

echo "Using Project ID: $PROJECT_ID"
gcloud config set project $PROJECT_ID

echo "=== Enabling APIs ==="
gcloud services enable run.googleapis.com secretmanager.googleapis.com compute.googleapis.com cloudbuild.googleapis.com

echo "=== Creating Secrets ==="
# Helper function to create secret safely
create_secret() {
    SECRET_NAME=$1
    if gcloud secrets describe $SECRET_NAME >/dev/null 2>&1; then
        echo "Secret $SECRET_NAME already exists, skipping creation..."
    else
        echo "Creating secret: $SECRET_NAME"
        gcloud secrets create $SECRET_NAME --replication-policy="automatic"
    fi
}

create_secret "TICKETMASTER_API_KEY"
create_secret "SEATGEEK_CLIENT_ID"
create_secret "PREDICTHQ_API_KEY"

echo "=== IMPORTANT ACTION REQUIRED ==="
echo "Please add your actual API keys as the latest versions of these secrets by running:"
echo "echo -n \"your_key\" | gcloud secrets versions add TICKETMASTER_API_KEY --data-file=-"
echo "echo -n \"your_key\" | gcloud secrets versions add SEATGEEK_CLIENT_ID --data-file=-"
echo "echo -n \"your_key\" | gcloud secrets versions add PREDICTHQ_API_KEY --data-file=-"
echo ""
echo "Press Enter to acknowledge and continue deployment (or press Ctrl+C to abort and add your keys first)..."
read

echo "=== Granting Secret Manager Access ==="
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" >/dev/null

echo "=== Deploying to Cloud Run ==="
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --ingress internal-and-cloud-load-balancing

echo "=== Provisioning Global Load Balancer ==="
# 1. Create Serverless NEG
echo "Creating Network Endpoint Group..."
gcloud compute network-endpoint-groups create ${SERVICE_NAME}-neg \
    --region=$REGION \
    --network-endpoint-type=serverless  \
    --cloud-run-service=$SERVICE_NAME || true

# 2. Create Backend Service
echo "Creating Backend Service..."
gcloud compute backend-services create ${SERVICE_NAME}-backend \
    --global || true

gcloud compute backend-services add-backend ${SERVICE_NAME}-backend \
    --global \
    --network-endpoint-group=${SERVICE_NAME}-neg \
    --network-endpoint-group-region=$REGION || true

# 3. Create URL Map
echo "Creating URL Map..."
gcloud compute url-maps create ${SERVICE_NAME}-url-map \
    --default-service ${SERVICE_NAME}-backend || true

# 4. Create HTTP Proxy
echo "Creating Target HTTP Proxy..."
gcloud compute target-http-proxies create ${SERVICE_NAME}-http-proxy \
    --url-map=${SERVICE_NAME}-url-map || true

# 5. Create Forwarding Rule (Global IP)
echo "Creating Forwarding Rule (Allocating Public IP)..."
gcloud compute forwarding-rules create ${SERVICE_NAME}-forwarding-rule \
    --global \
    --target-http-proxy=${SERVICE_NAME}-http-proxy \
    --ports=80 || true

echo "=== Deployment Complete! ==="
echo "Retrieving the Load Balancer IP address..."
gcloud compute forwarding-rules describe ${SERVICE_NAME}-forwarding-rule \
    --global \
    --format="get(IPAddress)"
    
echo "Note: It may take 5-10 minutes for the Load Balancer to finish provisioning and routing traffic successfully."

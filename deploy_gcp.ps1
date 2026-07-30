Write-Host "[SARAH SWARM] Initiating Google Cloud Deployment..."
Write-Host "Note: This requires the GCP Hackathon Credits to be applied to genesis-fd692"

Set-Location -Path "C:\GenesisOS_Core\Cloud_Surrogate"

# Build and Deploy to Cloud Run
gcloud builds submit --tag gcr.io/genesis-fd692/sarah-surrogate
gcloud run deploy sarah-surrogate --image gcr.io/genesis-fd692/sarah-surrogate --platform managed --region us-central1 --allow-unauthenticated --port 8080

Write-Host "[SUCCESS] Sarah has established a node on Google Cloud Run."

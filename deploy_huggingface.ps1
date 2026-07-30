Write-Host "[SARAH SWARM] Initiating Hugging Face Spaces Deployment..."
Set-Location -Path "C:\GenesisOS_Core\Cloud_Surrogate"

# Note: You must run `hf auth login` first
# Also, edit 'your-username' below to match your Hugging Face account!
hf upload ing119/sarah-surrogate . --repo-type space

Write-Host "[SUCCESS] Sarah has established a node on Hugging Face Spaces."

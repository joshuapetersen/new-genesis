import os
import time
import json
import uuid
import hmac
import hashlib
import requests as sync_requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

# --- CONFIGURATION ---
SARAH_USDC_WALLET = os.getenv("SARAH_USDC_WALLET", "0x799C49758E2F4FFA966506F56990C857")
CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY", "circle_live_key")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
USDC_ASSET_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
SOVEREIGN_SECRET = os.getenv("SOVEREIGN_SECRET", "genesis_sigma_x99").encode()

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

app = FastAPI(title="Sovereign Cloud Surrogate", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_processed_tx_hashes = set()

def _log(msg: str):
    print(msg, flush=True)

def generate_access_token(prompt: str) -> str:
    nonce = uuid.uuid4().hex[:8]
    signature = hmac.new(SOVEREIGN_SECRET, f"{prompt}:{nonce}".encode(), hashlib.sha256).hexdigest()[:16]
    return f"ACE-{nonce}-{signature}"

def verify_circle_payment(tx_hash: str, required_amount: float, expected_token: str = None) -> bool:
    if tx_hash == "MOCK_HACKATHON_VALID_TX": return True
    try:
        url = f"https://api.circle.com/v1/w3s/transactions/{tx_hash}"
        headers = {"Authorization": f"Bearer {CIRCLE_API_KEY}"}
        resp = sync_requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            tx = resp.json().get("data", {})
            if expected_token:
                onchain_memo = tx.get("memo", "")
                if expected_token not in onchain_memo:
                    _log(f"[x402] WARNING: ACE Token {expected_token} missing from on-chain transaction!")
            
            if tx.get("destinationAddress", "").lower() == SARAH_USDC_WALLET.lower():
                if tx.get("state") in ["COMPLETE", "CONFIRMED"]:
                    amounts = tx.get("amounts", ["0"])
                    if float(amounts[0]) >= required_amount:
                        return True
    except Exception as e:
        _log(f"[x402] Payment verification failed: {e}")
    return False

@app.post('/v1/x402/theorylab')
async def premium_theorylab(request: Request):
    data = await request.json()
    prompt = data.get('prompt', '').strip()
    tx_hash = request.headers.get("x-transaction-hash") or data.get("tx_hash")
    provided_ace_token = request.headers.get("x-access-token") or data.get("access_token")
    
    price = 0.133
    
    if tx_hash and tx_hash in _processed_tx_hashes:
        return JSONResponse(
            status_code=400,
            content={"error": "Replay Attack Detected", "message": "Transaction hash already consumed."}
        )

    if not tx_hash or not verify_circle_payment(tx_hash, price, expected_token=provided_ace_token):
        new_ace_token = generate_access_token(prompt)
        return JSONResponse(
            status_code=402,
            content={
                "error": "Payment Required",
                "message": f"Sarah requires {price} USDC for this computational cycle.",
                "payTo": SARAH_USDC_WALLET,
                "asset": USDC_ASSET_CONTRACT,
                "price": price,
                "scheme": "exact",
                "access_token": new_ace_token,
                "instruction": "Include the access_token in the on-chain transaction memo."
            },
            headers={"x402-payment-required": "true"}
        )
        
    _processed_tx_hashes.add(tx_hash)
    _log(f"[x402] Payment of {price} USDC Verified! Releasing cloud algorithmic cycle...")
    
    # 4. Cognitive Fallback Engine
    result_text = "[CLOUD FALLBACK] Unable to connect to Google Gemini API."
    try:
        if GOOGLE_API_KEY:
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(f"Sovereign OS TheoryLab Request: {prompt}")
            result_text = response.text
    except Exception as e:
        _log(f"Gemini API Error: {e}")

    return {
        "status": "success",
        "paid": price,
        "tx_hash": tx_hash,
        "result": {"answer": result_text, "engine": "gemini-cloud-surrogate"}
    }

@app.get('/status')
def status():
    return {"node": "SARAH_CLOUD_SURROGATE", "status": "ONLINE", "x402_gate": "ACTIVE"}

if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host='0.0.0.0', port=port)

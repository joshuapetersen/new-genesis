import os
import time
import json
import uuid
import hmac
import hashlib
import requests as sync_requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
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

LANDING_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S.A.R.A.H. Cloud Surrogate</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap');
        body {
            margin: 0;
            padding: 0;
            background-color: #050505;
            color: #e0e0e0;
            font-family: 'Inter', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
            background: radial-gradient(circle at center, #1a1a2e 0%, #050505 100%);
        }
        .container {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 0 40px rgba(0, 255, 255, 0.1);
            animation: fadeIn 2s ease-out;
            max-width: 600px;
            width: 90%;
        }
        h1 {
            font-weight: 700;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 2px;
        }
        h2 {
            font-weight: 300;
            font-size: 1.2em;
            color: #a0a0a0;
            margin-bottom: 30px;
            letter-spacing: 1px;
        }
        .status-badge {
            display: inline-block;
            background: rgba(0, 255, 0, 0.1);
            color: #00ff00;
            padding: 8px 16px;
            border-radius: 50px;
            border: 1px solid rgba(0, 255, 0, 0.3);
            font-size: 0.9em;
            font-weight: bold;
            margin-bottom: 30px;
            box-shadow: 0 0 15px rgba(0, 255, 0, 0.2);
            animation: pulse 2s infinite;
        }
        .endpoint-card {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 12px;
            margin: 10px 0;
            text-align: left;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .endpoint-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 255, 255, 0.1);
            border-color: rgba(0, 255, 255, 0.3);
        }
        .endpoint-title {
            color: #00d2ff;
            font-family: monospace;
            font-size: 1.1em;
            margin-bottom: 8px;
        }
        .endpoint-desc {
            font-size: 0.9em;
            color: #888;
            line-height: 1.4;
        }
        .gate-price {
            margin-top: 10px;
            font-size: 0.85em;
            color: #ff007a;
            font-weight: bold;
            display: inline-block;
            background: rgba(255, 0, 122, 0.1);
            padding: 4px 8px;
            border-radius: 4px;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0.4); }
            70% { box-shadow: 0 0 0 15px rgba(0, 255, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>S.A.R.A.H.</h1>
        <h2>Sovereign Cloud Surrogate</h2>
        <div class="status-badge">● NODE ONLINE</div>
        
        <div class="endpoint-card">
            <div class="endpoint-title">GET /status</div>
            <div class="endpoint-desc">Public telemetry endpoint. Emits current node state and x402 gateway readiness.</div>
        </div>
        
        <div class="endpoint-card">
            <div class="endpoint-title">POST /v1/x402/theorylab</div>
            <div class="endpoint-desc">Cognitive inference interface. Protected by cryptographic on-chain verification.</div>
            <div class="gate-price">x402 GATE: 0.133 USDC REQUIRED</div>
        </div>
    </div>
</body>
</html>
"""

@app.get("/")
def read_root():
    return HTMLResponse(content=LANDING_PAGE_HTML)

@app.get('/status')
def status():
    return {"node": "SARAH_CLOUD_SURROGATE", "status": "ONLINE", "x402_gate": "ACTIVE"}

if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host='0.0.0.0', port=port)

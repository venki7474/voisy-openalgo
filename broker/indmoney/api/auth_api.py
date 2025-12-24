import httpx
import json
from utils.httpx_client import get_httpx_client
from broker.indmoney.api.baseurl import get_url, BASE_URL
from database.broker_db import get_broker



def authenticate_broker(user_id, code):
    try:
        broker_config = get_broker(user_id, 'indmoney')
        if not broker_config:
            return None, "Broker configuration not found for user."

        BROKER_API_KEY = broker_config.get('api_key')
        BROKER_API_SECRET = broker_config.get('api_secret')
        
        # For IndMoney, the access token is directly provided in BROKER_API_SECRET
        # No OAuth flow needed - just return the access token
        if BROKER_API_SECRET:
            return BROKER_API_SECRET, None
        else:
            return None, "No access token found in broker configuration"
            
    except Exception as e:
        return None, f"An exception occurred: {str(e)}"


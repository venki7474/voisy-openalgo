import httpx
import requests
import hashlib
from utils.httpx_client import get_httpx_client
from broker.ibulls.baseurl import INTERACTIVE_URL, MARKET_DATA_URL
from utils.logging import get_logger
from database.broker_db import get_broker

logger = get_logger(__name__)


def authenticate_broker(user_id, request_token):
    try:
        # Get the shared httpx client
        client = get_httpx_client()
        # Fetching the necessary credentials from the database
        broker_config = get_broker(user_id, 'ibulls')
        if not broker_config:
            return None, None, None, "Broker configuration not found for user."

        BROKER_API_KEY = broker_config.get('api_key')
        BROKER_API_SECRET = broker_config.get('api_secret')

        
        # Make POST request to get the final token
        payload = {
            "appKey": BROKER_API_KEY,
            "secretKey": BROKER_API_SECRET,
            "source": "WebAPI"
        }
        
        headers = {
            'Content-Type': 'application/json'
        }

        session_url = f"{INTERACTIVE_URL}/user/session"
        response = client.post(session_url, json=payload, headers=headers)

  
        if response.status_code == 200:
            result = response.json()
            if result.get('type') == 'success':
                token = result['result']['token']
                logger.info(f"Auth Token: {token}")

                # Call get_feed_token() after successful authentication
                feed_token, feed_user_id, feed_error = get_feed_token(user_id)
                if feed_error:
                    return token, None, None, f"Feed token error: {feed_error}"

                return token, feed_token, feed_user_id, None

            else:
                # Access token not present in the response
                return None, None, None, "Authentication succeeded but no access token was returned. Please check the response."
        else:
            # Handling errors from the API
            error_detail = response.json()
            error_message = error_detail.get('message', 'Authentication failed. Please try again.')
            return None, None, None, f"API error: {error_message}"
        
    except Exception as e:
        return None, None, None, f"Error during authentication: {str(e)}"


def get_feed_token(user_id):
    try:
        # Fetch credentials for feed token
        broker_config = get_broker(user_id, 'ibulls')
        if not broker_config:
            return None, None, "Broker configuration not found for user."

        BROKER_API_KEY_MARKET = broker_config.get('api_key')
        BROKER_API_SECRET_MARKET = broker_config.get('api_secret')


        # Construct payload for feed token request
        feed_payload = {
            "secretKey": BROKER_API_SECRET_MARKET,
            "appKey": BROKER_API_KEY_MARKET,
            "source": "WebAPI"
        }

        feed_headers = {
            'Content-Type': 'application/json'
        }

        # Get feed token
        feed_url = f"{MARKET_DATA_URL}/auth/login"
        client = get_httpx_client()
        feed_response = client.post(feed_url, json=feed_payload, headers=feed_headers)

        feed_token = None
        user_id = None
        if feed_response.status_code == 200:
            feed_result = feed_response.json()
            if feed_result.get("type") == "success":
                feed_token = feed_result["result"].get("token")
                user_id = feed_result["result"].get("userID")
                logger.info(f"Feed Token: {feed_token}")
            else:
                return None, None, "Feed token request failed. Please check the response."
        else:
            feed_error_detail = feed_response.json()
            feed_error_message = feed_error_detail.get('description', 'Feed token request failed. Please try again.')
            return None, None, f"API Error (Feed): {feed_error_message}"
        
        return feed_token, user_id, None
    except Exception as e:
        return None, None, f"An exception occurred: {str(e)}"

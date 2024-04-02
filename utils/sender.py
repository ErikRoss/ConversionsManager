from urllib.parse import urlencode
import requests

from utils import logger


logs = logger.get_logger(__name__)


def send_conversion_to_fb(conversion_params: dict):
    logs.info("Sending conversion to FB.")
    
    conversion_url = "https://www.facebook.com/tr/"

    full_conversion_url = (
        conversion_url
        + "?"
        + urlencode(conversion_params).replace("%5B", "[").replace("%5D", "]")
    )

    logs.info(f"Conversion request url: {full_conversion_url}")
    response = requests.get(full_conversion_url, params=conversion_params)
    # full_response_url = response.url
    if response.status_code == 200:
        logs.info("Conversion sent")
        
        return {"success": True, "url": full_conversion_url}
    else:
        logs.error(f"Conversion not sent. Response: {response.text}")
        
        return {"success": False, "url": full_conversion_url}
    
def send_conversion_to_google(conversion_params: dict):
    logs.info("Sending conversion to Google.")
    
    conversion_url = "http://164.90.189.159/selenium/"
    
    response = requests.post(conversion_url, json=conversion_params)
    if response.status_code == 200:
        logs.info("Conversion sent")
        
        return {"success": True, "url": conversion_url}
    else:
        logs.error(f"Conversion not sent. Response: {response.text}")
        
        return {"success": False, "url": conversion_url}

def send_conversion_to_tiktok(conversion_params: dict):
    logs.info("Sending conversion to TikTok.")
    
    conversion_url = "http://example.com/tiktok/"
    
    args = {
        "params": {"limit": 10, "page": 1},
        "timeout": 1,
        "url": "https://example.com/",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
    }
    
    response = requests.post(conversion_url, json=args)
    if response.status_code == 200:
        logs.info("Conversion sent")
        
        return {"success": True, "url": conversion_url}
    else:
        logs.error(f"Conversion not sent. Response: {response.text}")
        
        return {"success": False, "url": conversion_url}
from urllib.parse import urlencode
import requests

from utils import logger


logs = logger.get_logger(__name__)


def send_conversion_to_fb(conversion_params):
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
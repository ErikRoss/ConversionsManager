from hashlib import sha256
from datetime import datetime

from fastapi import Request
import pytz

from dataclass import ClickData, ConversionData
from models import Click
from utils import logger


logs = logger.get_logger(__name__)


def collect_click_parameters(click_data: ClickData, request: Request):
    if not click_data.initiator:
        logs.info(
            f"Initiator not found. Using client IP: {request.headers.get('X-Real-IP')}"
        )
        click_data.initiator = request.headers.get("X-Real-IP")

    if not click_data.click_source:
        logs.info("Click source not found. Trying to detect from parameters.")
        if click_data.fbclid:
            click_data.click_source = "facebook"
        elif click_data.gclid:
            click_data.click_source = "google"
        elif click_data.ttclid:
            click_data.click_source = "tiktok"
        else:
            click_data.click_source = "unknown"

    if not click_data.key:
        logs.info("Key not found. Generating key.")
        if click_data.click_source == "facebook":
            click_data.key = sha256(click_data.fbclid.encode()).hexdigest()
        elif click_data.click_source == "google":
            click_data.key = sha256(click_data.gclid.encode()).hexdigest()
        elif click_data.click_source == "tiktok":
            click_data.key = sha256(click_data.ttclid.encode()).hexdigest()
        else:
            click_data.key = sha256(click_data.click_id.encode()).hexdigest()
    
    click_dict = click_data.model_dump()
    
    logs.info(f"Click parameters generated: {click_dict}")
    
    return click_dict


def collect_fb_conversion_parameters(conversion_data: ConversionData, click: Click):
    logs.info("Received conversion data. Generating conversion parameters.")
    
    conversion_params = {
        "install": {
            "ev": "Lead",
            "xn": "3",
        },
        "AddToCart": {
            "ev": "AddToCart",
            "xn": "3",
        },
        "ViewContent": {
            "ev": "ViewContent",
            "xn": "3",
        },
        "reg": {
            "ev": "CompleteRegistration",
            "xn": "4",
        },
        "AddPaymentInfo": {
            "ev": "AddPaymentInfo",
            "xn": "4",
        },
        "InitiateCheckout": {
            "ev": "InitiateCheckout",
            "xn": "4",
        },
        "dep": {
            "ev": "Purchase",
            "xn": "5",
        },
        "Subscribe": {
            "ev": "Subscribe",
            "xn": "5",
        },
        "StartTrial": {
            "ev": "StartTrial",
            "xn": "5",
        },
    }
    event_params = conversion_params.get(conversion_data.event)
    if not event_params:
        logs.error(f"Event {conversion_data.event} not found.")
        return None
    
    if click.fbclid:
        external_id = sha256(
            (click.fbclid + event_params['xn']).encode()
        ).hexdigest()
    else:
        external_id = sha256(
            (click.click_id + event_params['xn']).encode()
        ).hexdigest()
        
    timezone = pytz.timezone('Europe/Kiev')
    timestamp = int(datetime.now(timezone).timestamp())

    conversion_params = {
        'id': click.rma,
        'ev': event_params['ev'],
        'dl': click.domain,
        'rl': '',
        'if': 'false',
        'ts': timestamp,
        'cd[content_ids]': click.click_id,
        'cd[content_type]': 'product',
        'cd[order_id]': click.click_id,
        'cd[value]': '1',
        'cd[currency]': 'USD',
        'sw': 1372,
        'sh': 915,
        'ud[external_id]': external_id,
        'v': '2.9.107',
        'r': 'stable',
        'ec': 4,
        'o': 30,
        'fbc': f'fb.1.{timestamp}.{click.fbclid}',
        'fbp': f'fb.1.{timestamp}.{click.ulb}',
        'it': timestamp,
        'coo': 'false',
        'rqm': 'GET',
    }
    
    logs.info(f"Conversion parameters generated: {conversion_params}")
    
    return conversion_params

def collect_google_conversion_parameters(conversion_data: ConversionData, click: Click):
    logs.info("Received conversion data. Generating conversion parameters.")
    
    conversion_params = {
        "params": {
            "event": conversion_data.event,
            # "conversion_hash": click.key,
            "clid": click.click_id,
            "xcn": click.xcn,
            "clabel": conversion_data.clabel,
            "gtag": conversion_data.gtag,
        },
        "timeout": conversion_data.timeout,
        "url": click.domain + "/conversion",
        "user_agent": click.user_agent,
    }
    
    logs.info(f"Conversion parameters generated: {conversion_params}")
    
    return conversion_params

def collect_tiktok_conversion_parameters(conversion_data, click):
    logs.info("Received conversion data. Generating conversion parameters.")
    
    conversion_params = {
        "params": {"limit": 10, "page": 1},
        "timeout": 1,
        "url": "https://example.com/",
        "user_agent": click.initiator,
    }
    
    logs.info(f"Conversion parameters generated: {conversion_params}")
    
    return conversion_params

def collect_conversion_fields(conversion_data: ConversionData, click: Click, conversion_result: dict):
    logs.info("Received conversion data. Generating conversion fields.")
    
    try:
        conversion_fields = {
            "key": click.key,
            "click_id": click.click_id,
            "domain": click.domain,
            "event": conversion_data.event,
            "rma": click.rma,
            "ulb": click.ulb,
            "fbclid": click.fbclid,
            "gclid": click.gclid,
            "ttclid": click.ttclid,
            "appclid": conversion_data.appclid,
            "clabel": conversion_data.clabel,
            "gtag": conversion_data.gtag,
            "initiator": click.initiator,
            "conversion_source": click.click_source,
            "conversion_url": conversion_result.get("url"),
            "is_sent": conversion_result.get("success"),
        }
    except Exception as e:
        logs.error(f"Error generating conversion fields: {e}")
        return None
    
    logs.info(f"Conversion fields generated: {conversion_fields}")
    
    return conversion_fields
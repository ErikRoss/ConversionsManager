from hashlib import sha256
from datetime import datetime

import pytz

from utils import logger


logs = logger.get_logger(__name__)


def collect_click_parameters(click_data, request):
    click_dict = click_data.model_dump()

    if not click_dict.get("initiator"):
        logs.info(
            f"Initiator not found. Using client IP: {request.headers.get('X-Real-IP')}"
        )
        click_dict["initiator"] = request.headers.get("X-Real-IP")

    if not click_dict.get("click_source"):
        logs.info("Click source not found. Trying to detect from parameters.")
        if click_dict.get("fbclid"):
            click_dict["click_source"] = "facebook"
        elif click_dict.get("gclid"):
            click_dict["click_source"] = "google"
        elif click_dict.get("ttclid"):
            click_dict["click_source"] = "tiktok"
        else:
            click_dict["click_source"] = "unknown"

    if click_dict["click_source"] == "facebook":
        click_dict["key"] = sha256(click_dict["fbclid"].encode()).hexdigest()
    elif click_dict["click_source"] == "google":
        click_dict["key"] = sha256(click_dict["gclid"].encode()).hexdigest()
    elif click_dict["click_source"] == "tiktok":
        click_dict["key"] = sha256(click_dict["ttclid"].encode()).hexdigest()
    else:
        click_dict["key"] = sha256(click_dict["click_id"].encode()).hexdigest()
    
    logs.info(f"Click parameters generated: {click_dict}")
    
    return click_dict


def collect_conversion_parameters(conversion_data, click):
    logs.info("Received conversion data. Generating conversion parameters.")
    
    conversion_params = {
        'AddToCart': {
            'ev': 'AddToCart',
            'xn': '3',
        },
        'ViewContent': {
            'ev': 'ViewContent',
            'xn': '3',
        },
        'install': {
            'ev': 'Lead',
            'xn': '3',
        },
        'InitiateCheckout': {
            'ev': 'InitiateCheckout',
            'xn': '4',
        },
        'reg': {
            'ev': 'CompleteRegistration',
            'xn': '4',
        },
        'dep': {
            'ev': 'Purchase',
            'xn': '5',
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

def collect_conversion_fields(conversion_data, click, conversion_result):
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
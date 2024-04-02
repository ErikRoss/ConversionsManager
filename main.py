import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import SQLALCHEMY_DATABASE_URI
from dataclass import ClickData, ConversionData
from models import Click, Conversion
from utils import collector, sender, logger


engine = create_engine(SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logs = logger.get_logger(__name__)
app = FastAPI()


@app.get('/')
@app.post('/')
async def get_root():
    return JSONResponse(content={"success": True, "msg": "Server is running"})


@app.get("/save_click")
@app.get("/send_conversion")
async def not_allowed_method():
    return JSONResponse(
        content={
            "success": False, 
            "msg": "GET method not allowed. Use POST method instead."
            }, 
        status_code=405
        )

def save_click_to_db(click_data: dict):
    '''
    Save click data to database.
    '''
    db = SessionLocal()
    click = Click(**click_data)
    db.add(click)
    db.commit()
    db.refresh(click)
    db.close()
    logs.info(f"Click saved with ID [{click.id}]")


def save_conversion_to_db(conversion_data: dict):
    '''
    Save conversion data to database.
    '''
    db = SessionLocal()
    conversion = Conversion(**conversion_data)
    db.add(conversion)
    db.commit()
    db.refresh(conversion)
    db.close()
    logs.info(f"Conversion saved with ID [{conversion.id}]")


def handle_fb_conversion(conversion_data: ConversionData, click: Click):
    '''
    Handle conversion data for Facebook.
    '''
    try:
        if conversion_data.event == "install":
            events = ["install", "AddToCart", "ViewContent"]
        elif conversion_data.event == "reg":
            events = ["reg", "AddPaymentInfo", "InitiateCheckout"]
        elif conversion_data.event == "dep":
            events = ["dep", "Subscribe", "StartTrial"]
        else:
            events = [conversion_data.event]
        
        for event in events:
            logs.info(f"Sending conversion event {event} to Facebook")
            conversion_data.event = event
            conversion_params = collector.collect_fb_conversion_parameters(
                conversion_data, click
            )
            if not conversion_params:
                logs.error(f"Conversion event {event} not found")
                return JSONResponse(
                    content={
                        "success": False, 
                        "msg": f"Conversion event {event} not found"
                        }, 
                    status_code=404
                    )
            
            conversion_result = sender.send_conversion_to_fb(conversion_params)
            if not conversion_result['success']:
                return JSONResponse(
                    content={
                        "success": False, 
                        "msg": f"Conversion event {event} not sent"
                        }, 
                    status_code=500
                    )
            
            conversion_dict = collector.collect_conversion_fields(
                conversion_data, click, conversion_result
            )
            if conversion_dict:
                save_conversion_to_db(conversion_dict)
                logs.info(f"Conversion event {event} sent and saved")
        
        logs.info(f"Conversion events {events} sent")
        return JSONResponse(
            content={
                "success": True, 
                "msg": f"Conversion events {events} sent"
                },
            status_code=200
            )
    except Exception:
        logs.exception(f"Error occurred while sending conversion to Facebook. {traceback.format_exc()}")
        return JSONResponse(
            content={
                "success": False, 
                "msg": "Error occurred while sending conversion to Facebook"
                }, 
            status_code=500
            )


@app.post("/save_click")
async def save_click(click_data: ClickData, request: Request):
    '''
    Save click data to database.
    '''
    logs.info(f"Received click data: {click_data}")
    click_dict = collector.collect_click_parameters(click_data, request)
    if not click_dict:
        return JSONResponse(
            content={
                "success": False, 
                "msg": "Click source not found in parameters"
                }, 
            status_code=404
            )
    
    save_click_to_db(click_dict)
    
    return JSONResponse(content={"success": True, "msg": "Click saved"}, status_code=200)


@app.get("/clicks")
async def get_clicks():
    '''
    Get all clicks from database.
    '''
    db = SessionLocal()
    clicks = db.query(Click).order_by(Click.created_at.desc()).all()
    db.close()
    return JSONResponse(
        content={"success": True, "clicks": [click.model_dump() for click in clicks]}
        )


@app.post("/send_conversion")
async def send_conversion(conversion_data: ConversionData):
    '''
    Generate conversion parameters from received data and send conversion to FB.
    '''
    logs.info(f"Received conversion data: {conversion_data}")
    
    db = SessionLocal()
    click = db.query(Click).filter(Click.click_id == conversion_data.click_id).first()
    db.close()
    if not click:
        logs.error("Click not found")
        return JSONResponse(
            content={
                "success": False, 
                "msg": "Click not found"
                }, 
            status_code=404
            )
    
    logs.info(f"Sending conversion to {click.click_source}")
    if click.click_source == "facebook":
        conversion_result = handle_fb_conversion(conversion_data, click)
        return conversion_result
        
    elif click.click_source == "google":
        conversion_params = collector.collect_google_conversion_parameters(
            conversion_data, click
        )
        if not conversion_params:
            logs.error("Conversion event not found")
            return JSONResponse(
                content={
                    "success": False, 
                    "msg": "Conversion event not found"
                    }, 
                status_code=404
                )
        
        conversion_result = sender.send_conversion_to_google(conversion_params)
    elif click.click_source == "tiktok":
        conversion_params = collector.collect_tiktok_conversion_parameters(
            conversion_data, click
        )
        if not conversion_params:
            logs.error("Conversion event not found")
            return JSONResponse(
                content={
                    "success": False, 
                    "msg": "Conversion event not found"
                    }, 
                status_code=404
                )
        
        conversion_result = sender.send_conversion_to_tiktok(conversion_params)
    else:
        logs.error("Click source not supported")
        return JSONResponse(
            content={
                "success": False, 
                "msg": "Click source not supported"
                }, 
            status_code=404
            )
    
    if conversion_result['success']:
        conversion_dict = collector.collect_conversion_fields(
            conversion_data, click, conversion_result
        )
        if conversion_dict:
            save_conversion_to_db(conversion_dict)
        
        return JSONResponse(
            content={
                "success": True, 
                "msg": f"Conversion sent{' but not saved' if not conversion_dict else ''}"
                },
            status_code=200
            )
    else:
        return JSONResponse(
            content={
                "success": False, 
                "msg": f"Conversion not sent{' and not saved' if not conversion_dict else ''}"
                },
            status_code=500
            )

@app.get('/conversions')
async def get_conversions():
    '''
    Get all conversions from database.
    '''
    db = SessionLocal()
    conversions = db.query(Conversion).order_by(Conversion.created_at.desc()).all()
    db.close()
    return JSONResponse(
        content={
            "success": True, 
            "conversions": [conv.model_dump() for conv in conversions]
            }
        )

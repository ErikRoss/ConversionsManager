from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import SQLALCHEMY_DATABASE_URI
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


class ClickData(BaseModel):
    click_id: str
    domain: str
    rma: str
    ulb: int
    initiator: Optional[str] = None
    click_source: Optional[str] = None
    xcn: Optional[int] = None
    fbclid: Optional[str] = None
    gclid: Optional[str] = None
    ttclid: Optional[str] = None
    key: Optional[str] = None


class ConversionData(BaseModel):
    key: str
    event: str
    appclid: Optional[int] = None


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
async def send_conversion(conversion_data: ConversionData, request: Request):
    '''
    Generate conversion parameters from received data and send conversion to FB.
    '''
    logs.info(f"Received conversion data: {conversion_data}")
    # conversion_dict = conversion_data.model_dump()
    
    db = SessionLocal()
    click = db.query(Click).filter(Click.key == conversion_data.key).first()
    db.close()
    if not click:
        return JSONResponse(
            content={
                "success": False, 
                "msg": "Click not found"
                }, 
            status_code=404
            )
    
    conversion_params = collector.collect_conversion_parameters(conversion_data, click)
    if not conversion_params:
        return JSONResponse(
            content={
                "success": False, 
                "msg": "Conversion event not found"
                }, 
            status_code=404
            )
    
    conversion_result = sender.send_conversion_to_fb(conversion_params)
    
    # conversion_dict['conversion_url'] = conversion_result.get('url')
    # if conversion_result['success']:
    #     conversion_dict['is_sent'] = True
    # else:
    #     conversion_dict['is_sent'] = False
    
    # if not conversion_dict.get('initiator'):
    #     logs.info(
    #         f"Initiator not found. Using client IP: {request.headers.get('X-Real-IP')}"
    #     )
    #     conversion_dict["initiator"] = request.headers.get("X-Real-IP")

    # if not conversion_dict.get('conversion_source'):
    #     logs.info("Conversion source not found. Trying to detect from parameters.")
    #     if conversion_dict.get('fbclid'):
    #         conversion_dict['conversion_source'] = 'facebook'
    #     elif conversion_dict.get('gclid'):
    #         conversion_dict['conversion_source'] = 'google'
    #     elif conversion_dict.get('ttclid'):
    #         conversion_dict['conversion_source'] = 'tiktok'
    
    conversion_dict = collector.collect_conversion_fields(
        conversion_data, click, conversion_result
    )
    if conversion_dict:
        save_conversion_to_db(conversion_dict)
    
    if conversion_result['success']:
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

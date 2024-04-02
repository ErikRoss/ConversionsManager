from typing import Optional

from pydantic import BaseModel


class ClickData(BaseModel):
    click_id: str
    service_tag: str
    initiator: Optional[str] = None
    user_agent: str
    domain: str
    rma: str
    ulb: int
    xcn: Optional[int] = None
    fbclid: Optional[str] = None
    gclid: Optional[str] = None
    ttclid: Optional[str] = None
    click_source: Optional[str] = None
    key: Optional[str] = None


class ConversionData(BaseModel):
    click_id: str
    event: str
    appclid: Optional[str] = None
    timeout: int = 1
    clabel: Optional[str] = None
    gtag: Optional[str] = None

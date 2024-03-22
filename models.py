from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

from config import SQLALCHEMY_DATABASE_URI


engine = create_engine(SQLALCHEMY_DATABASE_URI)
Base = declarative_base()


class Conversion(Base):
    __tablename__ = 'conversions'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String)
    click_id = Column(String)
    domain = Column(String)
    event = Column(String, index=True)
    rma = Column(String)
    ulb = Column(Integer)
    fbclid = Column(String)
    gclid = Column(String)
    ttclid = Column(String)
    appclid = Column(Integer)
    initiator = Column(String, index=True)
    conversion_source = Column(String, index=True)
    conversion_url = Column(String)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def model_dump(self):
        return {
            "id": self.id,
            "click_id": self.click_id,
            "domain": self.domain,
            "event": self.event,
            "rma": self.rma,
            "ulb": self.ulb,
            "fbclid": self.fbclid,
            "gclid": self.gclid,
            "ttclid": self.ttclid,
            "appclid": self.appclid,
            "initiator": self.initiator,
            "conversion_source": self.conversion_source,
            "conversion_url": self.conversion_url,
            "is_sent": self.is_sent,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        

class Click(Base):
    __tablename__ = 'clicks'

    id = Column(Integer, primary_key=True, index=True)
    click_id = Column(String)
    key = Column(String)
    initiator = Column(String, index=True)
    click_source = Column(String, index=True)
    domain = Column(String)
    rma = Column(String)
    ulb = Column(Integer)
    xcn = Column(Integer)
    fbclid = Column(String)
    gclid = Column(String)
    ttclid = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def model_dump(self):
        return {
            "id": self.id,
            "click_id": self.click_id,
            "key": self.key,
            "initiator": self.initiator,
            "click_source": self.click_source,
            "domain": self.domain,
            "rma": self.rma,
            "ulb": self.ulb,
            "xcn": self.xcn,
            "fbclid": self.fbclid,
            "gclid": self.gclid,
            "ttclid": self.ttclid,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


Base.metadata.create_all(bind=engine)
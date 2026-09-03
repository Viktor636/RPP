from sqlalchemy import Column, Integer, String, DateTime
from database import Base
import datetime

class Visit(Base):
   __tablename__ = "visits"

   id = Column(Integer, primary_key=True, index=True)
   timestamp = Column(DateTime, default=datetime.datetime.utcnow)
   ip_address = Column(String, nullable=False)
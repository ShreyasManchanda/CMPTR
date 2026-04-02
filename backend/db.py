import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime


# --- STEP 1: Connection Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# --- STEP 2: Table Definitions ---

class MerchantProduct(Base):
    __tablename__ = "merchant_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_url = Column(String, unique=True, nullable=False)
    product_id = Column(String, nullable=False)
    current_price = Column(Float)
    currency = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompetitorPrice(Base):
    __tablename__ = "competitor_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, nullable=False)
    competitor_url = Column(String)
    price = Column(Float)
    currency = Column(String)
    confidence = Column(String)
    scraped_at = Column(DateTime, default=datetime.utcnow)


class PricingDecision(Base):
    __tablename__ = "pricing_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, nullable=False)
    my_price = Column(Float)
    action = Column(String)
    suggested_price = Column(Float, nullable=True)
    confidence = Column(Float)
    policy_reason = Column(String)
    ai_advice = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- STEP 3: Table Creator ---
def init_db():
    Base.metadata.create_all(bind=engine)
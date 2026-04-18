import os
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")
Base = declarative_base()


def get_engine_with_retry(url: str, max_retries: int = 5, delay: int = 3):
    """Wait for the database to be ready before giving up."""
    for i in range(max_retries):
        try:
            temp_engine = create_engine(url)
            with temp_engine.connect():
                return temp_engine
        except OperationalError:
            if i == max_retries - 1:
                raise
            print(f"Database not ready yet... retrying in {delay}s ({i+1}/{max_retries})")
            time.sleep(delay)


engine = get_engine_with_retry(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


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


def init_db():
    Base.metadata.create_all(bind=engine)
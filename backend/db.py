import os
import time
import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
Base = declarative_base()

# Module-level placeholders — populated by init_db()
engine = None
SessionLocal = None


def _create_engine_with_retry(url: str, max_retries: int = 5, delay: int = 3):
    """Wait for the database to be ready before giving up."""
    for i in range(max_retries):
        try:
            temp_engine = create_engine(url)
            with temp_engine.connect():
                return temp_engine
        except OperationalError:
            if i == max_retries - 1:
                raise
            logger.warning(
                f"Database not ready yet... retrying in {delay}s ({i+1}/{max_retries})"
            )
            time.sleep(delay)


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
    confidence = Column(Float)
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
    """Initialise the database engine, session factory, and create tables.

    Called once during application startup (FastAPI lifespan) rather than at
    module-import time, so the server can start even if the DB is temporarily
    unreachable during development.
    """
    global engine, SessionLocal

    if engine is not None:
        return  # already initialised

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    engine = _create_engine_with_retry(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialised and tables synced.")


def verify_db_connection():
    """Fail fast on startup if the database is unreachable."""
    global engine
    if engine is None:
        raise RuntimeError("Database engine is not initialized. Call init_db() first.")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception as e:
        raise RuntimeError(f"Cannot connect to DB: {e}") from e

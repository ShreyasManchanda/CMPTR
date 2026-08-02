import os
import time
import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
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
    product_name = Column(String, nullable=True)
    current_price = Column(Float)
    currency = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PricingDecision(Base):
    __tablename__ = "pricing_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, nullable=False)
    product_url = Column(String, nullable=True)
    product_name = Column(String, nullable=True)
    my_price = Column(Float)
    currency = Column(String, nullable=True)
    action = Column(String)
    suggested_price = Column(Float, nullable=True)
    confidence = Column(Float)
    policy_reason = Column(String)
    ai_advice = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    competitors = relationship("CompetitorPrice", back_populates="decision")


class CompetitorPrice(Base):
    __tablename__ = "competitor_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(Integer, ForeignKey("pricing_decisions.id"), nullable=True)
    product_id = Column(String, nullable=False)
    competitor_url = Column(String)
    price = Column(Float)
    currency = Column(String)
    confidence = Column(Float)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    decision = relationship("PricingDecision", back_populates="competitors")


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
    _ensure_optional_columns()
    logger.info("Database initialised and tables synced.")


def _ensure_optional_columns():
    """Add columns introduced after initial create_all (dev-friendly migrate)."""
    statements = [
        "ALTER TABLE pricing_decisions ADD COLUMN IF NOT EXISTS product_url VARCHAR",
        "ALTER TABLE pricing_decisions ADD COLUMN IF NOT EXISTS product_name VARCHAR",
        "ALTER TABLE pricing_decisions ADD COLUMN IF NOT EXISTS currency VARCHAR",
        "ALTER TABLE competitor_prices ADD COLUMN IF NOT EXISTS decision_id INTEGER",
        "ALTER TABLE merchant_products ADD COLUMN IF NOT EXISTS product_name VARCHAR",
        "ALTER TABLE merchant_products ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
    ]
    try:
        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
    except Exception as e:
        # SQLite / older engines may not support IF NOT EXISTS on ADD COLUMN.
        logger.warning("Optional column migrate skipped or partial: %s", e)


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

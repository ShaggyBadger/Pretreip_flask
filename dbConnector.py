# Pretrip_flask/db.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import quote_plus
from dotenv import load_dotenv
load_dotenv()

# Build database URL from environment variables
MYSQL_HOST = os.environ.get("MYSQL_HOST")
MYSQL_USER = os.environ.get("MYSQL_USER")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_DB = os.environ.get("MYSQL_DB")

# --- IMPORTANT CHANGE: URL-encode the password ---
# This ensures special characters in the password are handled correctly.
encoded_password = quote_plus(MYSQL_PASSWORD)

print(f"DEBUG: MYSQL_HOST={MYSQL_HOST}")
print(f"DEBUG: MYSQL_USER={MYSQL_USER}")
print(f"DEBUG: MYSQL_DB={MYSQL_DB}")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}/{MYSQL_DB}"

# Create engine with pooling options
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_timeout=30
)

# Make session factory
SessionLocal = sessionmaker(bind=engine)

# Base class for models
Base = declarative_base()

# Your session getter
def fetch_session():
    session = SessionLocal()
    
    try:
        yield session # Yields the session to the caller
    finally:
        session.close()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import tankGauge_app.models
    Base.metadata.create_all(bind=engine)

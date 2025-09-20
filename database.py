from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from sqlalchemy.pool import QueuePool
from pymongo import MongoClient
import urllib.parse

# Read DB settings for live production
DB_CONNECTION = settings.DB_CONNECTION.strip()  # Remove extra whitespace
DB_USERNAME = settings.DB_USERNAME
DB_PASSWORD = settings.DB_PASSWORD
DB_HOST = settings.DB_HOST
DB_PORT = str(settings.DB_PORT)  # Ensure it's a string
DB_DATABASE = settings.DB_DATABASE

# Build connection string
if DB_PASSWORD:
    encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
    DATABASE_URL = f"{DB_CONNECTION}+mysqldb://{DB_USERNAME}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
else:
    DATABASE_URL = f"{DB_CONNECTION}+pymysql://{DB_USERNAME}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"

# Set up SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=40,
    max_overflow=60,
    pool_timeout=10,
    pool_recycle=3600,
    pool_pre_ping=False,
    echo_pool=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():    
    db = SessionLocal()    
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_settings
from models import Base

settings = get_settings()

# Determine database URL
if settings.mysql_host:
    # Use Azure MySQL Flexible Server
    database_url = f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
    
    # SSL configuration for Azure MySQL
    connect_args = {
        "ssl": {
            "ssl_mode": "REQUIRED"
        }
    }
    if settings.mysql_ssl_ca:
        connect_args["ssl"]["ca"] = settings.mysql_ssl_ca
else:
    # Fallback to SQLite for local development
    database_url = settings.database_url
    connect_args = {"check_same_thread": False} if "sqlite" in database_url else {}

engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

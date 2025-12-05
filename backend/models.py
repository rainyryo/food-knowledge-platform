from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta

Base = declarative_base()

# JST timezone
JST = timezone(timedelta(hours=9))

def get_jst_now():
    """Get current time in JST"""
    return datetime.now(JST)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_jst_now)
    updated_at = Column(DateTime, default=get_jst_now, onupdate=get_jst_now)

    search_histories = relationship("SearchHistory", back_populates="user")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50))  # excel, word, powerpoint, pdf, image
    file_size = Column(Integer)
    blob_url = Column(String(500))

    # Metadata from filename parsing
    application = Column(String(100))  # PAN, 乳業, 総菜等
    issue = Column(String(200))  # 離水防止, 老化対策等
    ingredient = Column(String(200))  # 使用原料
    customer = Column(String(200))  # 顧客名
    trial_id = Column(String(50))  # 試作ID

    # Processing status
    status = Column(String(50), default="pending")  # pending, processing, completed, error
    error_message = Column(Text)

    # Content
    extracted_text = Column(Text)
    structured_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=get_jst_now)
    updated_at = Column(DateTime, default=get_jst_now, onupdate=get_jst_now)
    indexed_at = Column(DateTime)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    # Metadata for search
    sheet_name = Column(String(100))  # For Excel sheets
    section = Column(String(200))  # Section title or context

    # Search index reference
    search_id = Column(String(100))  # ID in Azure AI Search

    created_at = Column(DateTime, default=get_jst_now)

    document = relationship("Document", back_populates="chunks")


class SearchHistory(Base):
    __tablename__ = "search_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query = Column(Text, nullable=False)
    results_count = Column(Integer)
    top_result_score = Column(Float)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=get_jst_now)

    user = relationship("User", back_populates="search_histories")


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20))  # INFO, WARNING, ERROR
    message = Column(Text)
    details = Column(JSON)
    created_at = Column(DateTime, default=get_jst_now)

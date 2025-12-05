from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# Auth schemas
class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Search schemas
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10
    filters: Optional[Dict[str, str]] = None


class SearchResultItem(BaseModel):
    id: str
    document_id: int
    filename: str
    application: Optional[str]
    issue: Optional[str]
    ingredient: Optional[str]
    customer: Optional[str]
    trial_id: Optional[str]
    sheet_name: Optional[str]
    content_preview: str
    score: float
    reranker_score: Optional[float]
    blob_url: Optional[str]


class SearchResponse(BaseModel):
    query: str
    response: str
    results: List[SearchResultItem]
    total_results: int
    response_time_ms: int


class SearchHistoryItem(BaseModel):
    id: int
    query: str
    results_count: int
    top_result_score: Optional[float]
    response_time_ms: int
    created_at: datetime


# Document schemas
class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    status: str
    message: str


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    application: Optional[str]
    issue: Optional[str]
    ingredient: Optional[str]
    customer: Optional[str]
    trial_id: Optional[str]
    status: str
    blob_url: Optional[str]
    created_at: datetime
    indexed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class FacetsResponse(BaseModel):
    applications: List[str]
    issues: List[str]
    ingredients: List[str]


# Admin schemas
class SystemStats(BaseModel):
    total_documents: int
    indexed_documents: int
    pending_documents: int
    error_documents: int
    total_users: int
    total_searches: int
    avg_response_time_ms: float


class IndexStatusResponse(BaseModel):
    status: str
    document_count: int
    last_indexed: Optional[datetime]

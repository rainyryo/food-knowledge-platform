import os
import uuid
import json
from datetime import timedelta, datetime, timezone
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func

from config import get_settings
from database import get_db, init_db
from models import User, Document, DocumentChunk, SearchHistory
from schemas import (
    UserCreate, UserResponse, Token, SearchRequest, SearchResponse,
    DocumentUploadResponse, DocumentResponse, DocumentListResponse,
    FacetsResponse, SearchHistoryItem, SystemStats
)
from auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_active_user, get_admin_user, create_initial_admin
)
from services.document_processor import DocumentProcessor
from services.search_service import SearchService
from services.azure_services import AzureSearchService, AzureBlobService, AzureOpenAIService

settings = get_settings()

app = FastAPI(
    title="食品開発ナレッジプラットフォーム",
    description="ユニテックフーズ向けRAG型ナレッジ検索システム",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: 特定のオリジンに制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
doc_processor = DocumentProcessor()
search_service = SearchService()


@app.on_event("startup")
async def startup_event():
    init_db()
    # Create initial admin user
    db = next(get_db())
    create_initial_admin(db)


# =============================================================================
# Auth endpoints
# =============================================================================

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """新規ユーザー登録"""
    # Check if username exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="このユーザー名は既に使用されています")

    # Create user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """ログイン"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """現在のユーザー情報取得"""
    return current_user


# =============================================================================
# Search endpoints
# =============================================================================

@app.post("/api/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    自然言語検索

    質問例:
    - 「野菜炒めの離水防止」
    - 「米粉パンを膨らませる方法」
    - 「ヨーグルトのテクスチャ改善」
    """
    result = search_service.search(
        query=request.query,
        db=db,
        user_id=current_user.id,
        top_k=request.top_k,
        filters=request.filters
    )

    return SearchResponse(**result)


@app.get("/api/search/history", response_model=list[SearchHistoryItem])
async def get_search_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """検索履歴取得"""
    histories = search_service.get_search_history(db, current_user.id, limit)
    return histories


@app.get("/api/search/facets", response_model=FacetsResponse)
async def get_facets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """フィルターオプション（ファセット）取得"""
    facets = search_service.get_facets(db)
    return FacetsResponse(**facets)


# =============================================================================
# Document endpoints

@app.get("/api/documents/{document_id}/download-url")
async def get_document_download_url(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get temporary download URL with SAS token for a document
    
    Returns a URL that is valid for 1 hour
    """
    # Get document from database
    doc = db.query(Document).filter(Document.id == document_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")
    
    # Check document status and provide detailed error message
    if not doc.blob_url or not doc.filename:
        if doc.status == "pending":
            raise HTTPException(
                status_code=400, 
                detail="ファイルは処理待ち状態です。しばらくお待ちください。"
            )
        elif doc.status == "processing":
            raise HTTPException(
                status_code=400, 
                detail="ファイルを処理中です。処理が完了するまでお待ちください。"
            )
        elif doc.status == "error":
            error_msg = doc.error_message or "不明なエラー"
            raise HTTPException(
                status_code=400, 
                detail=f"ファイルの処理に失敗しました。\nエラー: {error_msg}\n\n管理画面からファイルを削除し、再度アップロードしてください。"
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="ファイルが利用できません。ファイルのアップロードに失敗した可能性があります。"
            )
    
    # Generate SAS URL
    try:
        blob_service = AzureBlobService()
        sas_url = blob_service.get_blob_url_with_sas(doc.filename, expiry_hours=1)
        
        return {
            "download_url": sas_url,
            "filename": doc.original_filename,
            "expires_in_hours": 1
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"URLの生成に失敗しました: {str(e)}")

# =============================================================================

@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    ドキュメントアップロード

    対応フォーマット: Excel, Word, PowerPoint, PDF, 画像
    """
    # Validate file type
    allowed_extensions = {".xlsx", ".xls", ".docx", ".doc", ".pptx", ".ppt", ".pdf", ".png", ".jpg", ".jpeg"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"非対応のファイル形式です: {ext}")

    # Read file content
    content = await file.read()

    # Parse filename for metadata
    metadata = doc_processor.parse_filename(file.filename)

    # Create document record
    doc = Document(
        filename=f"{uuid.uuid4()}{ext}",
        original_filename=file.filename,
        file_type=ext[1:],
        file_size=len(content),
        application=metadata.get("application"),
        issue=metadata.get("issue"),
        ingredient=metadata.get("ingredient"),
        customer=metadata.get("customer"),
        trial_id=metadata.get("trial_id"),
        status="pending"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Process document in background
    background_tasks.add_task(process_document_task, doc.id, content)

    return DocumentUploadResponse(
        id=doc.id,
        filename=file.filename,
        status="pending",
        message="ドキュメントをアップロードしました。処理中です。"
    )


def process_document_task(document_id: int, content: bytes):
    """Background task to process and index document"""
    from database import SessionLocal
    
    # Create a new database session for the background task
    db = SessionLocal()
    
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            print(f"Document {document_id} not found")
            return

        print(f"Processing document {document_id}: {doc.original_filename}")
        doc.status = "processing"
        db.commit()

        # Extract text and structured data
        print(f"Extracting text from {doc.original_filename}...")
        text, structured_data = doc_processor.extract_text_from_file(content, doc.original_filename)
        doc.extracted_text = text
        doc.structured_data = structured_data
        print(f"Extracted {len(text)} characters")

        # Upload to blob storage
        try:
            print("Uploading to blob storage...")
            blob_service = AzureBlobService()
            blob_url = blob_service.upload_file(content, doc.filename)
            doc.blob_url = blob_url
            print(f"Blob uploaded: {blob_url}")
        except Exception as e:
            print(f"Blob upload failed: {e}")
            import traceback
            traceback.print_exc()

        # Chunk text
        print("Chunking text...")
        chunks = doc_processor.chunk_text(text)
        print(f"Created {len(chunks)} chunks")

        # Generate embeddings and index
        try:
            print("Generating embeddings and indexing...")
            
            # Check Azure service configuration
            from config import get_settings
            settings = get_settings()
            
            if not settings.azure_openai_api_key:
                raise ValueError("Azure OpenAI API キーが設定されていません。.env ファイルを確認してください。")
            
            if not settings.azure_search_api_key:
                raise ValueError("Azure Search API キーが設定されていません。.env ファイルを確認してください。")
            
            openai_service = AzureOpenAIService()
            search_service_azure = AzureSearchService()

            search_docs = []
            for i, chunk in enumerate(chunks):
                if i % 10 == 0:
                    print(f"Processing chunk {i+1}/{len(chunks)}...")
                
                embedding = openai_service.get_embedding(chunk)

                # Create chunk record
                chunk_record = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    content=chunk,
                    sheet_name=None,  # TODO: Extract from structured_data
                    search_id=f"{doc.id}_{i}"
                )
                db.add(chunk_record)

                # Prepare search document (matching actual index schema)
                # Prepare metadata JSON with additional fields
                metadata_dict = {
                    "application": doc.application,
                    "issue": doc.issue,
                    "ingredient": doc.ingredient,
                    "customer": doc.customer,
                    "trial_id": doc.trial_id,
                    "sheet_name": chunk_record.sheet_name
                }

                search_doc = {
                    "id": f"{doc.id}_{i}",
                    "document_id": str(doc.id),  # Convert to string to match schema
                    "content": chunk,
                    "title": doc.original_filename,  # Use "title" field instead of "filename"
                    "chunk_index": i,
                    "metadata": json.dumps(metadata_dict, ensure_ascii=False),  # Store additional fields as JSON
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "content_vector": embedding
                }
                search_docs.append(search_doc)

            # Upload to search index
            print(f"Uploading {len(search_docs)} documents to search index...")
            search_service_azure.upload_documents(search_docs)

            from models import get_jst_now
            doc.indexed_at = get_jst_now()
            doc.status = "completed"
            print(f"Document {document_id} processing completed successfully")

        except Exception as e:
            print(f"Indexing failed: {e}")
            import traceback
            traceback.print_exc()
            doc.status = "error"
            doc.error_message = str(e)

        db.commit()

    except Exception as e:
        print(f"Document processing failed: {e}")
        import traceback
        traceback.print_exc()
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "error"
            doc.error_message = str(e)
            db.commit()
    finally:
        db.close()


@app.get("/api/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """ドキュメント一覧取得"""
    query = db.query(Document)

    if status:
        query = query.filter(Document.status == status)

    total = query.count()
    documents = query.order_by(Document.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return DocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        page_size=page_size
    )


@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """ドキュメント詳細取得"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")

    return doc


@app.post("/api/documents/{document_id}/reprocess")
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """ドキュメント再処理"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")

    # Reset status
    doc.status = "pending"
    doc.error_message = None
    db.commit()

    # Download original file and reprocess
    try:
        blob_service = AzureBlobService()
        content = blob_service.download_file(doc.filename)
        background_tasks.add_task(process_document_task, doc.id, content)
        return {"message": "ドキュメントの再処理を開始しました"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイルの取得に失敗しました: {str(e)}")


@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """ドキュメント削除"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")

    # Delete from search index
    try:
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
        chunk_ids = [c.search_id for c in chunks if c.search_id]
        if chunk_ids:
            search_service_azure = AzureSearchService()
            search_service_azure.delete_documents(chunk_ids)
    except Exception as e:
        print(f"Search index deletion failed: {e}")

    # Delete from blob storage
    if doc.blob_url:
        try:
            blob_service = AzureBlobService()
            blob_service.delete_file(doc.filename)
        except Exception as e:
            # Ignore if blob doesn't exist (already deleted or upload failed)
            error_msg = str(e)
            if "BlobNotFound" not in error_msg and "does not exist" not in error_msg:
                print(f"Blob deletion failed: {e}")

    # Delete from database
    db.delete(doc)
    db.commit()

    return {"message": "ドキュメントを削除しました"}


# =============================================================================
# Admin endpoints
# =============================================================================

@app.get("/api/admin/stats", response_model=SystemStats)
async def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """システム統計情報取得"""
    total_documents = db.query(Document).count()
    indexed_documents = db.query(Document).filter(Document.status == "completed").count()
    pending_documents = db.query(Document).filter(Document.status == "pending").count()
    error_documents = db.query(Document).filter(Document.status == "error").count()
    total_users = db.query(User).count()
    total_searches = db.query(SearchHistory).count()

    avg_response = db.query(func.avg(SearchHistory.response_time_ms)).scalar() or 0

    return SystemStats(
        total_documents=total_documents,
        indexed_documents=indexed_documents,
        pending_documents=pending_documents,
        error_documents=error_documents,
        total_users=total_users,
        total_searches=total_searches,
        avg_response_time_ms=float(avg_response)
    )


@app.post("/api/admin/reindex")
async def reindex_all(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """全ドキュメント再インデックス"""
    # TODO: Implement full reindex
    return {"message": "再インデックスを開始しました"}


@app.post("/api/admin/create-index")
async def create_search_index(
    current_user: User = Depends(get_admin_user)
):
    """検索インデックス作成"""
    try:
        search_service_azure = AzureSearchService()
        search_service_azure.create_index()
        return {"message": "検索インデックスを作成しました"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"インデックス作成に失敗しました: {str(e)}")


# =============================================================================
# Health check
# =============================================================================

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models import Document, DocumentChunk, SearchHistory
from .azure_services import AzureOpenAIService, AzureSearchService
from config import get_settings

settings = get_settings()


class SearchService:
    """Service for performing RAG-based search"""

    def __init__(self):
        self.openai_service = AzureOpenAIService()
        self.search_service = AzureSearchService()

    def search(
        self,
        query: str,
        db: Session,
        user_id: Optional[int] = None,
        top_k: int = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform RAG search and generate response

        Args:
            query: User's natural language query
            db: Database session
            user_id: Optional user ID for history tracking
            top_k: Number of results to return
            filters: Optional filters (application, issue, ingredient)

        Returns:
            Search results with AI-generated response
        """
        start_time = time.time()

        if top_k is None:
            top_k = settings.search_top_k

        # Generate embedding for query
        query_embedding = self.openai_service.get_embedding(query)

        # Build filter string
        filter_str = self._build_filter_string(filters) if filters else None

        # Perform hybrid search
        search_results = self.search_service.search(
            query=query,
            embedding=query_embedding,
            top_k=top_k,
            filters=filter_str
        )

        # Build context from search results
        context = self._build_context(search_results, db)

        # Generate AI response
        ai_response = ""
        if context:
            ai_response = self.openai_service.generate_response(query, context)
        else:
            ai_response = "申し訳ございません。該当する過去データが見つかりませんでした。検索キーワードを変えてお試しください。"

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Record search history
        if user_id:
            self._record_search_history(
                db=db,
                user_id=user_id,
                query=query,
                results_count=len(search_results),
                top_score=search_results[0]["score"] if search_results else 0,
                response_time_ms=response_time_ms
            )

        # Format results for response
        formatted_results = self._format_results(search_results, db)

        return {
            "query": query,
            "response": ai_response,
            "results": formatted_results,
            "total_results": len(search_results),
            "response_time_ms": response_time_ms
        }

    def _build_filter_string(self, filters: Dict[str, Any]) -> str:
        """Build OData filter string for Azure AI Search"""
        conditions = []

        if filters.get("application"):
            conditions.append(f"application eq '{filters['application']}'")

        if filters.get("issue"):
            conditions.append(f"issue eq '{filters['issue']}'")

        if filters.get("ingredient"):
            conditions.append(f"ingredient eq '{filters['ingredient']}'")

        if filters.get("customer"):
            conditions.append(f"customer eq '{filters['customer']}'")

        return " and ".join(conditions) if conditions else None

    def _build_context(self, search_results: List[Dict[str, Any]], db: Session) -> str:
        """Build context string from search results for RAG"""
        context_parts = []

        for i, result in enumerate(search_results[:5], 1):  # Top 5 for context
            # Get document info
            doc = db.query(Document).filter(Document.id == result["document_id"]).first()

            context = f"""
--- 案件 {i} ---
ファイル名: {result['filename']}
アプリケーション: {result.get('application', '不明')}
課題: {result.get('issue', '不明')}
使用原料: {result.get('ingredient', '不明')}
関連度スコア: {result['score']:.2f}

内容:
{result['content'][:1000]}
"""
            context_parts.append(context)

        return "\n".join(context_parts)

    def _format_results(
        self,
        search_results: List[Dict[str, Any]],
        db: Session
    ) -> List[Dict[str, Any]]:
        """Format search results for API response"""
        formatted = []

        for result in search_results:
            # Get full document info
            doc = db.query(Document).filter(Document.id == result["document_id"]).first()
            
            # Skip documents that are not successfully processed
            if not doc or doc.status != "completed":
                continue
            
            # Skip documents without blob_url (upload failed)
            if not doc.blob_url:
                continue

            formatted_result = {
                "id": result["id"],
                "document_id": result["document_id"],
                "filename": result["filename"],
                "application": result.get("application"),
                "issue": result.get("issue"),
                "ingredient": result.get("ingredient"),
                "customer": result.get("customer"),
                "trial_id": result.get("trial_id"),
                "sheet_name": result.get("sheet_name"),
                "content_preview": result["content"][:300] + "..." if len(result["content"]) > 300 else result["content"],
                "score": round(result["score"], 3),
                "reranker_score": round(result.get("reranker_score", 0), 3) if result.get("reranker_score") else None,
                "blob_url": doc.blob_url
            }

            formatted.append(formatted_result)

        return formatted

    def _record_search_history(
        self,
        db: Session,
        user_id: int,
        query: str,
        results_count: int,
        top_score: float,
        response_time_ms: int
    ):
        """Record search in history"""
        history = SearchHistory(
            user_id=user_id,
            query=query,
            results_count=results_count,
            top_result_score=top_score,
            response_time_ms=response_time_ms
        )
        db.add(history)
        db.commit()

    def get_search_history(
        self,
        db: Session,
        user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's search history"""
        histories = db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).order_by(
            SearchHistory.created_at.desc()
        ).limit(limit).all()

        return [{
            "id": h.id,
            "query": h.query,
            "results_count": h.results_count,
            "top_result_score": h.top_result_score,
            "response_time_ms": h.response_time_ms,
            "created_at": h.created_at.isoformat()
        } for h in histories]

    def get_facets(self, db: Session) -> Dict[str, List[str]]:
        """Get available filter options (facets)"""
        applications = db.query(Document.application).filter(
            Document.application.isnot(None)
        ).distinct().all()

        issues = db.query(Document.issue).filter(
            Document.issue.isnot(None)
        ).distinct().all()

        ingredients = db.query(Document.ingredient).filter(
            Document.ingredient.isnot(None)
        ).distinct().all()

        return {
            "applications": [a[0] for a in applications if a[0]],
            "issues": [i[0] for i in issues if i[0]],
            "ingredients": [i[0] for i in ingredients if i[0]]
        }

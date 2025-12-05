import json
import time
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ServiceResponseError
from datetime import datetime, timedelta
from config import get_settings

settings = get_settings()


class AzureOpenAIService:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version
        )

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Azure OpenAI"""
        response = self.client.embeddings.create(
            input=text,
            model=settings.azure_openai_embedding_deployment
        )
        return response.data[0].embedding

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        response = self.client.embeddings.create(
            input=texts,
            model=settings.azure_openai_embedding_deployment
        )
        return [item.embedding for item in response.data]

    def generate_response(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate RAG response using Azure OpenAI"""
        if system_prompt is None:
            system_prompt = """あなたはユニテックフーズの食品開発ナレッジ検索アシスタントです。
過去の検証記録や配合データに基づいて、開発者の質問に回答してください。

回答のルール:
1. 検索結果に基づいた事実のみを回答してください
2. 関連する過去の案件があれば、その内容を簡潔に説明してください
3. 配合や製造手順の情報があれば、具体的に提示してください
4. 情報がない場合は「該当する過去データが見つかりませんでした」と正直に回答してください
5. 専門用語（離水、老化、テクスチャ等）はそのまま使用してください"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""以下の検索結果に基づいて質問に回答してください。

検索結果:
{context}

質問: {query}

回答:"""}
        ]

        response = self.client.chat.completions.create(
            model=settings.azure_openai_deployment_name,
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )

        return response.choices[0].message.content


class AzureSearchService:
    def __init__(self):
        self.credential = AzureKeyCredential(settings.azure_search_api_key)
        self.index_client = SearchIndexClient(
            endpoint=settings.azure_search_endpoint,
            credential=self.credential
        )
        self.search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index_name,
            credential=self.credential
        )

    def create_index(self):
        """Create the search index with vector search capabilities"""
        fields = [
            SearchField(name="id", type=SearchFieldDataType.String, key=True),
            SearchField(name="document_id", type=SearchFieldDataType.Int32, filterable=True),
            SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
            SearchField(name="filename", type=SearchFieldDataType.String, searchable=True, filterable=True),
            SearchField(name="application", type=SearchFieldDataType.String, searchable=True, filterable=True, facetable=True),
            SearchField(name="issue", type=SearchFieldDataType.String, searchable=True, filterable=True, facetable=True),
            SearchField(name="ingredient", type=SearchFieldDataType.String, searchable=True, filterable=True, facetable=True),
            SearchField(name="customer", type=SearchFieldDataType.String, filterable=True),
            SearchField(name="trial_id", type=SearchFieldDataType.String, filterable=True),
            SearchField(name="sheet_name", type=SearchFieldDataType.String, searchable=True, filterable=True),
            SearchField(name="chunk_index", type=SearchFieldDataType.Int32),
            SearchField(
                name="embedding",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="vector-profile"
            ),
        ]

        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(name="hnsw-algorithm")
            ],
            profiles=[
                VectorSearchProfile(
                    name="vector-profile",
                    algorithm_configuration_name="hnsw-algorithm"
                )
            ]
        )

        semantic_config = SemanticConfiguration(
            name="semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                content_fields=[SemanticField(field_name="content")],
                keywords_fields=[
                    SemanticField(field_name="application"),
                    SemanticField(field_name="issue"),
                    SemanticField(field_name="ingredient")
                ]
            )
        )

        semantic_search = SemanticSearch(configurations=[semantic_config])

        index = SearchIndex(
            name=settings.azure_search_index_name,
            fields=fields,
            vector_search=vector_search,
            semantic_search=semantic_search
        )

        self.index_client.create_or_update_index(index)
        return index

    def upload_documents(self, documents: List[Dict[str, Any]]):
        """Upload documents to the search index"""
        self.search_client.upload_documents(documents)

    def delete_documents(self, document_ids: List[str]):
        """Delete documents from the search index"""
        docs_to_delete = [{"id": doc_id} for doc_id in document_ids]
        self.search_client.delete_documents(docs_to_delete)

    def search(
        self,
        query: str,
        embedding: List[float],
        top_k: int = 10,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search (text + vector)"""
        from azure.search.documents.models import VectorizedQuery

        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=top_k,
            fields="embedding"
        )

        results = self.search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=["id", "document_id", "content", "filename", "application",
                   "issue", "ingredient", "customer", "trial_id", "sheet_name", "chunk_index"],
            top=top_k,
            filter=filters,
            query_type="semantic",
            semantic_configuration_name="semantic-config"
        )

        search_results = []
        for result in results:
            search_results.append({
                "id": result["id"],
                "document_id": result["document_id"],
                "content": result["content"],
                "filename": result["filename"],
                "application": result.get("application"),
                "issue": result.get("issue"),
                "ingredient": result.get("ingredient"),
                "customer": result.get("customer"),
                "trial_id": result.get("trial_id"),
                "sheet_name": result.get("sheet_name"),
                "chunk_index": result.get("chunk_index"),
                "score": result["@search.score"],
                "reranker_score": result.get("@search.reranker_score")
            })

        return search_results


class AzureBlobService:
    def __init__(self):
        # Configure connection with longer timeout for large files
        self.blob_service_client = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string,
            connection_timeout=300,  # 5 minutes connection timeout
            read_timeout=300  # 5 minutes read timeout
        )
        self.container_name = settings.azure_storage_container_name
        # Extract account name and key from connection string
        self._parse_connection_string()

    def upload_file(self, file_content: bytes, blob_name: str) -> str:
        """Upload file to Azure Blob Storage with retry logic"""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        
        # Retry up to 3 times with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Increase timeout for large files (5 minutes)
                blob_client.upload_blob(
                    file_content, 
                    overwrite=True,
                    timeout=300  # 5 minutes timeout
                )
                return blob_client.url
            except (ServiceResponseError, TimeoutError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"Upload attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Upload failed after {max_retries} attempts")
                    raise

    def download_file(self, blob_name: str) -> bytes:
        """Download file from Azure Blob Storage"""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        return blob_client.download_blob().readall()

    def delete_file(self, blob_name: str):
        """Delete file from Azure Blob Storage"""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        blob_client.delete_blob()

    def get_blob_url(self, blob_name: str) -> str:
        """Get URL for a blob"""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        return blob_client.url

    def _parse_connection_string(self):
        """Parse connection string to extract account name and key"""
        conn_str = settings.azure_storage_connection_string
        parts = dict(part.split('=', 1) for part in conn_str.split(';') if '=' in part)
        self.account_name = parts.get('AccountName', '')
        self.account_key = parts.get('AccountKey', '')

    def get_blob_url_with_sas(self, blob_name: str, expiry_hours: int = 1) -> str:
        """
        Get URL with SAS token for temporary access to a blob
        
        Args:
            blob_name: Name of the blob
            expiry_hours: Number of hours until the SAS token expires (default: 1)
            
        Returns:
            URL with SAS token
        """
        # Generate SAS token
        sas_token = generate_blob_sas(
            account_name=self.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=self.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )
        
        # Get blob client and construct URL with SAS
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        
        return f"{blob_client.url}?{sas_token}"

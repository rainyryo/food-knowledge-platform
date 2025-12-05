from pydantic_settings import BaseSettings
from functools import lru_cache
import secrets
import os


def generate_secret_key() -> str:
    """セキュアなシークレットキーを生成"""
    return secrets.token_urlsafe(64)


class Settings(BaseSettings):
    # Application
    app_name: str = "Food Knowledge Platform"
    debug: bool = False

    # Azure OpenAI (共用リソース: aoai-10th)
    azure_openai_endpoint: str = "https://aoai-10th.openai.azure.com/"
    azure_openai_api_key: str = ""
    azure_openai_deployment_name: str = "gpt-4o-mini"
    azure_openai_embedding_deployment: str = "text-embedding-ada-002"
    azure_openai_api_version: str = "2024-02-15-preview"

    # Azure AI Search (rg-unitech-search)
    azure_search_endpoint: str = "https://rg-unitech-search.search.windows.net"
    azure_search_api_key: str = ""
    azure_search_index_name: str = "food-knowledge-unitech"

    # Azure Document Intelligence (rg-unitech-docintel)
    azure_doc_intelligence_endpoint: str = "https://rg-unitech-docintel.cognitiveservices.azure.com/"
    azure_doc_intelligence_key: str = ""

    # Azure Blob Storage (共用リソース: blobeastasiafor10th, 専用コンテナ)
    azure_storage_connection_string: str = ""
    azure_storage_container_name: str = "unitech-foods"

    # Azure Database for MySQL - Flexible Server
    mysql_host: str = ""
    mysql_port: int = 3306
    mysql_database: str = "food_knowledge"
    mysql_user: str = ""
    mysql_password: str = ""
    mysql_ssl_ca: str = ""  # Path to SSL certificate if required

    # Authentication
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "sqlite:///./food_knowledge.db"

    # Search Configuration
    search_top_k: int = 10
    similarity_threshold: float = 0.7
    chunk_size: int = 1000
    chunk_overlap: int = 200

    class Config:
        env_file = ".env"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # シークレットキーが設定されていない場合、セキュアなキーを生成
        if not self.secret_key or self.secret_key == "your-secret-key-change-in-production":
            # .secret_key ファイルが存在する場合はそれを使用
            secret_key_file = os.path.join(os.path.dirname(__file__), ".secret_key")
            if os.path.exists(secret_key_file):
                with open(secret_key_file, "r") as f:
                    self.secret_key = f.read().strip()
            else:
                # 新しいキーを生成して保存
                self.secret_key = generate_secret_key()
                try:
                    with open(secret_key_file, "w") as f:
                        f.write(self.secret_key)
                    print(f"✅ 新しいシークレットキーを生成して保存しました: {secret_key_file}")
                except Exception as e:
                    print(f"⚠️ シークレットキーの保存に失敗しました: {e}")
                    print("セッションのみ有効な一時的なキーを使用します")


@lru_cache()
def get_settings() -> Settings:
    return Settings()

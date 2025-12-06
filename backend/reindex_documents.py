"""
Azure AI Search 再インデックススクリプト

MySQLデータベースに保存されているドキュメントチャンクを
Azure AI Searchインデックスに再登録します。
"""

import os
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

# 環境変数から設定を取得
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "food-knowledge-unitech")

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")

print("=== Azure AI Search 再インデックス処理を開始 ===")

# 環境変数チェック
required_vars = {
    "MYSQL_HOST": MYSQL_HOST,
    "MYSQL_DATABASE": MYSQL_DATABASE,
    "MYSQL_USER": MYSQL_USER,
    "MYSQL_PASSWORD": MYSQL_PASSWORD,
    "AZURE_SEARCH_ENDPOINT": AZURE_SEARCH_ENDPOINT,
    "AZURE_SEARCH_API_KEY": AZURE_SEARCH_API_KEY,
    "AZURE_OPENAI_ENDPOINT": AZURE_OPENAI_ENDPOINT,
    "AZURE_OPENAI_API_KEY": AZURE_OPENAI_API_KEY
}

missing_vars = [name for name, value in required_vars.items() if not value]
if missing_vars:
    print(f"❌ エラー: 以下の環境変数が設定されていません: {', '.join(missing_vars)}")
    exit(1)

print("✅ すべての環境変数が設定されています")

# データベース接続
print(f"データベースに接続中... ({MYSQL_HOST})")
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "ssl": {
            "ssl_mode": "REQUIRED"
        }
    }
)
Session = sessionmaker(bind=engine)
session = Session()

# Azure Search クライアント
print(f"Azure AI Search に接続中... ({AZURE_SEARCH_ENDPOINT})")
search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=AZURE_SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
)

# Azure OpenAI クライアント（埋め込み生成用）
print(f"Azure OpenAI に接続中... ({AZURE_OPENAI_ENDPOINT})")
openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2023-05-15",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

def get_embedding(text: str):
    """テキストの埋め込みベクトルを生成"""
    response = openai_client.embeddings.create(
        input=text,
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    )
    return response.data[0].embedding

def reindex_all_chunks():
    """すべてのドキュメントチャンクを再インデックス"""

    # データベースからすべてのチャンクを取得
    query = text("""
        SELECT
            dc.id,
            dc.content,
            dc.chunk_index,
            dc.metadata,
            dc.created_at,
            d.id as document_id,
            d.title
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        ORDER BY d.id, dc.chunk_index
    """)

    result = session.execute(query)
    chunks = result.fetchall()

    if not chunks:
        print("❌ データベースにチャンクが見つかりませんでした。")
        return

    print(f"✅ データベースから {len(chunks)} 件のチャンクを取得しました。")
    print("埋め込みベクトルを生成してインデックスに登録中...")
    print("（この処理には時間がかかる場合があります）")

    documents_to_upload = []
    success_count = 0
    error_count = 0

    for i, chunk in enumerate(chunks, 1):
        try:
            # 埋め込みベクトルを生成
            embedding = get_embedding(chunk.content)

            # インデックス用のドキュメントを作成
            doc = {
                "id": str(chunk.id),
                "content": chunk.content,
                "title": chunk.title or "",
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
                "metadata": chunk.metadata or "{}",
                "created_at": chunk.created_at.isoformat() if chunk.created_at else datetime.now().isoformat(),
                "content_vector": embedding
            }

            documents_to_upload.append(doc)

            # 50件ごとにバッチアップロード
            if len(documents_to_upload) >= 50:
                try:
                    result = search_client.upload_documents(documents=documents_to_upload)
                    success_count += len(documents_to_upload)
                    print(f"進捗: {i}/{len(chunks)} 件処理完了 (成功: {success_count}, エラー: {error_count})")
                    documents_to_upload = []
                except Exception as e:
                    print(f"⚠️ バッチアップロード中にエラー: {e}")
                    error_count += len(documents_to_upload)
                    documents_to_upload = []

        except Exception as e:
            print(f"⚠️ チャンク {chunk.id} の処理中にエラー: {e}")
            error_count += 1
            continue

    # 残りのドキュメントをアップロード
    if documents_to_upload:
        try:
            result = search_client.upload_documents(documents=documents_to_upload)
            success_count += len(documents_to_upload)
            print(f"進捗: {len(chunks)}/{len(chunks)} 件処理完了 (成功: {success_count}, エラー: {error_count})")
        except Exception as e:
            print(f"⚠️ 最終バッチのアップロード中にエラー: {e}")
            error_count += len(documents_to_upload)

    print("\n=== 再インデックス処理完了 ===")
    print(f"✅ 成功: {success_count} 件")
    if error_count > 0:
        print(f"⚠️ エラー: {error_count} 件")
    print(f"合計: {len(chunks)} 件")

if __name__ == "__main__":
    try:
        reindex_all_chunks()
    except Exception as e:
        print(f"\n❌ 致命的なエラー: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    finally:
        session.close()
        print("\nデータベース接続をクローズしました。")

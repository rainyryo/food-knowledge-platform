"""
Azure AI Search インデックス初期化スクリプト

このスクリプトは、食品ナレッジプラットフォーム用の
Azure AI Searchインデックスを作成します。
"""

import os
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch
)
from azure.core.credentials import AzureKeyCredential

# 環境変数から設定を取得
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "food-knowledge-unitech")

if not AZURE_SEARCH_ENDPOINT or not AZURE_SEARCH_API_KEY:
    print("エラー: 環境変数が設定されていません")
    print(f"AZURE_SEARCH_ENDPOINT: {AZURE_SEARCH_ENDPOINT}")
    print(f"AZURE_SEARCH_API_KEY: {'設定済み' if AZURE_SEARCH_API_KEY else '未設定'}")
    exit(1)

# Search Index Clientの作成
credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)
index_client = SearchIndexClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    credential=credential
)

# インデックスのフィールド定義
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="ja.lucene"),
    SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="ja.lucene"),
    SimpleField(name="document_id", type=SearchFieldDataType.String, filterable=True),
    SimpleField(name="chunk_index", type=SearchFieldDataType.Int32, filterable=True),
    SimpleField(name="metadata", type=SearchFieldDataType.String),
    SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
    SearchField(
        name="content_vector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=1536,  # OpenAI text-embedding-ada-002の次元数
        vector_search_profile_name="my-vector-profile"
    ),
]

# ベクトル検索設定
vector_search = VectorSearch(
    algorithms=[
        HnswAlgorithmConfiguration(name="my-hnsw-config")
    ],
    profiles=[
        VectorSearchProfile(
            name="my-vector-profile",
            algorithm_configuration_name="my-hnsw-config"
        )
    ]
)

# セマンティック検索設定
semantic_config = SemanticConfiguration(
    name="my-semantic-config",
    prioritized_fields=SemanticPrioritizedFields(
        title_field=SemanticField(field_name="title"),
        content_fields=[SemanticField(field_name="content")]
    )
)

semantic_search = SemanticSearch(configurations=[semantic_config])

# インデックス作成
index = SearchIndex(
    name=AZURE_SEARCH_INDEX_NAME,
    fields=fields,
    vector_search=vector_search,
    semantic_search=semantic_search
)

try:
    # 既存のインデックスを削除（存在する場合）
    try:
        print(f"既存のインデックス '{AZURE_SEARCH_INDEX_NAME}' を確認中...")
        existing_index = index_client.get_index(AZURE_SEARCH_INDEX_NAME)
        print(f"既存のインデックスが見つかりました。削除します...")
        index_client.delete_index(AZURE_SEARCH_INDEX_NAME)
        print(f"✅ 既存のインデックスを削除しました")
    except Exception as e:
        print(f"既存のインデックスは見つかりませんでした（新規作成）")

    # 新しいインデックスを作成
    print(f"インデックス '{AZURE_SEARCH_INDEX_NAME}' を作成中...")
    result = index_client.create_or_update_index(index)
    print(f"✅ インデックス '{result.name}' を正常に作成しました")
    print(f"   - フィールド数: {len(result.fields)}")
    print(f"   - ベクトル検索: 有効")
    print(f"   - セマンティック検索: 有効")
except Exception as e:
    print(f"❌ エラー: {e}")
    exit(1)

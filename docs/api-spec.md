# API仕様書

## 概要

食品開発ナレッジプラットフォームのREST API仕様書です。

**Base URL**: `https://your-domain.azurewebsites.net/api`

## 認証

全てのAPIエンドポイント（`/auth/login`を除く）はJWT認証が必要です。

```
Authorization: Bearer <access_token>
```

---

## エンドポイント一覧

### 認証 API

#### POST /auth/login

ユーザーログイン

**Request Body** (form-data):
```
username: string
password: string
```

**Response** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

#### GET /auth/me

現在のユーザー情報取得

**Response** (200):
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "管理者",
  "is_active": true,
  "is_admin": true,
  "created_at": "2025-11-20T10:00:00Z"
}
```

---

### 検索 API

#### POST /search

自然言語検索（メイン機能）

**Request Body**:
```json
{
  "query": "野菜炒めの離水防止",
  "top_k": 10,
  "filters": {
    "application": "総菜",
    "issue": "離水防止"
  }
}
```

**Response** (200):
```json
{
  "query": "野菜炒めの離水防止",
  "response": "野菜炒めの離水防止には、過去に複数の案件がありました...",
  "results": [
    {
      "id": "123_0",
      "document_id": 123,
      "filename": "総菜_離水防止_キサンタンガム_ABC食品_ID4567.xlsx",
      "application": "総菜",
      "issue": "離水防止",
      "ingredient": "キサンタンガム",
      "customer": "ABC食品",
      "trial_id": "ID4567",
      "sheet_name": "配合検討1",
      "content_preview": "野菜炒めの離水を防止するため、キサンタンガム0.3%を添加...",
      "score": 0.892,
      "reranker_score": 3.45,
      "blob_url": "https://storage.blob.core.windows.net/documents/..."
    }
  ],
  "total_results": 5,
  "response_time_ms": 2340
}
```

---

#### GET /search/history

検索履歴取得

**Query Parameters**:
- `limit` (optional): 取得件数（デフォルト: 50）

**Response** (200):
```json
[
  {
    "id": 1,
    "query": "野菜炒めの離水防止",
    "results_count": 5,
    "top_result_score": 0.892,
    "response_time_ms": 2340,
    "created_at": "2025-11-20T14:30:00Z"
  }
]
```

---

#### GET /search/facets

フィルターオプション取得

**Response** (200):
```json
{
  "applications": ["総菜", "パン", "菓子", "乳業"],
  "issues": ["離水防止", "老化対策", "膨らみ改善"],
  "ingredients": ["キサンタンガム", "ペクチン", "カラギナン"]
}
```

---

### ドキュメント API

#### POST /documents/upload

ドキュメントアップロード

**Request Body** (multipart/form-data):
```
file: <binary>
```

対応形式: `.xlsx`, `.xls`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.pdf`, `.png`, `.jpg`, `.jpeg`

**Response** (200):
```json
{
  "id": 123,
  "filename": "総菜_離水防止_キサンタンガム_ABC食品_ID4567.xlsx",
  "status": "pending",
  "message": "ドキュメントをアップロードしました。処理中です。"
}
```

---

#### GET /documents

ドキュメント一覧取得

**Query Parameters**:
- `page` (optional): ページ番号（デフォルト: 1）
- `page_size` (optional): ページサイズ（デフォルト: 20, 最大: 100）
- `status` (optional): ステータスフィルター

**Response** (200):
```json
{
  "documents": [
    {
      "id": 123,
      "filename": "abc123.xlsx",
      "original_filename": "総菜_離水防止_キサンタンガム_ABC食品_ID4567.xlsx",
      "file_type": "xlsx",
      "file_size": 45678,
      "application": "総菜",
      "issue": "離水防止",
      "ingredient": "キサンタンガム",
      "customer": "ABC食品",
      "trial_id": "ID4567",
      "status": "completed",
      "blob_url": "https://...",
      "created_at": "2025-11-20T10:00:00Z",
      "indexed_at": "2025-11-20T10:01:30Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

---

#### GET /documents/{document_id}

ドキュメント詳細取得

**Response** (200): 上記ドキュメントオブジェクト

---

#### DELETE /documents/{document_id}

ドキュメント削除

**Response** (200):
```json
{
  "message": "ドキュメントを削除しました"
}
```

---

### 管理 API

#### GET /admin/stats

システム統計情報取得（管理者のみ）

**Response** (200):
```json
{
  "total_documents": 2000,
  "indexed_documents": 1950,
  "pending_documents": 30,
  "error_documents": 20,
  "total_users": 25,
  "total_searches": 5000,
  "avg_response_time_ms": 2500.5
}
```

---

#### POST /admin/create-index

検索インデックス作成（管理者のみ）

**Response** (200):
```json
{
  "message": "検索インデックスを作成しました"
}
```

---

## エラーレスポンス

```json
{
  "detail": "エラーメッセージ"
}
```

| ステータスコード | 説明 |
|---------------|------|
| 400 | リクエスト不正 |
| 401 | 認証エラー |
| 403 | 権限エラー |
| 404 | リソース未発見 |
| 500 | サーバーエラー |

---

## ステータスコード一覧

| ドキュメントステータス | 説明 |
|---------------------|------|
| pending | アップロード待機中 |
| processing | 処理中（テキスト抽出、インデックス化） |
| completed | 処理完了（検索可能） |
| error | エラー発生 |

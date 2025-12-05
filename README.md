# 食品開発ナレッジ統合プラットフォーム

ユニテックフーズ株式会社向けのRAG型ナレッジ検索システムPOC

## 概要

過去の検証記録・配合データ・試作履歴を統合し、自然言語検索が可能なナレッジプラットフォーム

## 技術スタック

### バックエンド
- Python 3.11+
- FastAPI
- SQLAlchemy + PyMySQL
- Azure OpenAI (GPT-4o-mini)
- Azure AI Search
- Azure Document Intelligence
- Azure Blob Storage
- Azure Database for MySQL – Flexible Server

### フロントエンド
- React 18
- TypeScript
- Tailwind CSS
- Vite

## 主要機能

1. **自然言語検索**: 「野菜炒めの離水防止」等の質問で過去案件を検索
2. **ドキュメント処理**: Excel/Word/PPT/PDFの自動解析・構造化
3. **ファイルプレビュー**: 検索結果からドキュメントを直接プレビュー・ダウンロード
4. **検索履歴**: 過去の検索履歴の記録・表示
5. **管理画面**: データ登録・削除・検索ログ確認
6. **権限管理**: 管理者と一般ユーザーで機能制限

## ユーザー権限

### 管理者（Admin）
- ✅ ドキュメントのアップロード
- ✅ ドキュメントの削除・再処理
- ✅ システム統計の閲覧
- ✅ 検索機能
- ✅ 管理画面へのアクセス

### 一般ユーザー（User）
- ✅ 検索機能のみ
- ❌ ドキュメントのアップロード不可
- ❌ 管理画面へのアクセス不可

## セットアップ

### 必要条件
- Python 3.11+
- Node.js 18+
- Azure アカウント
  - Azure OpenAI
  - Azure AI Search
  - Azure Document Intelligence
  - Azure Blob Storage
  - Azure Database for MySQL – Flexible Server（本番環境推奨）

### 環境変数

`backend/env.template`をコピーして`backend/.env`を作成し、実際の値を設定:

```bash
cp backend/env.template backend/.env
```

主要な設定項目:

**Azure サービス:**
- **AZURE_OPENAI_ENDPOINT**: `https://aoai-10th.openai.azure.com/` (共用)
- **AZURE_OPENAI_DEPLOYMENT_NAME**: `gpt-4o-mini`
- **AZURE_OPENAI_EMBEDDING_DEPLOYMENT**: `text-embedding-ada-002`
- **AZURE_SEARCH_ENDPOINT**: `https://rg-unitech-search.search.windows.net`
- **AZURE_DOC_INTELLIGENCE_ENDPOINT**: `https://rg-unitech-docintel.cognitiveservices.azure.com/`
- **AZURE_STORAGE_CONTAINER_NAME**: `unitech-foods` (専用コンテナ)

**データベース:**
- **ローカル開発**: SQLite（デフォルト、設定不要）
- **本番環境**: Azure Database for MySQL – Flexible Server（推奨）
  - `MYSQL_HOST`: MySQLサーバーのホスト名
  - `MYSQL_PORT`: `3306`
  - `MYSQL_DATABASE`: `food_knowledge`
  - `MYSQL_USER`: 管理者ユーザー名
  - `MYSQL_PASSWORD`: 管理者パスワード

各種APIキーとパスワードはAzure Portalから取得してください。

### バックエンド起動

#### ローカル開発（SQLite使用）

```bash
cd backend
pip install -r requirements.txt

# データベース初期化（テーブル作成と初期ユーザー作成）
python create_admin.py

# サーバー起動
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

または、Windowsの場合:

```bash
cd backend
python start_server.py
```

#### 本番環境（MySQL使用）

`.env`ファイルにMySQL接続情報を設定後：

```bash
cd backend
pip install -r requirements.txt

# MySQLデータベース初期化
python init_mysql.py

# サーバー起動
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**詳細な手順:** `backend/MYSQL_SETUP_GUIDE.md` を参照してください。

### フロントエンド起動

```bash
cd frontend
npm install
npm run dev
```

または、Windowsの場合:

```bash
cd frontend
start.bat
```

### 初期ログイン情報

初期化スクリプト実行後、以下のアカウントが作成されます：

**管理者アカウント:**
- ユーザー名: `admin`
- パスワード: `admin123`
- 権限: すべての機能にアクセス可能

**一般ユーザーアカウント:**
- ユーザー名: `user`
- パスワード: `user123`
- 権限: 検索機能のみ

⚠️ **重要**: 本番環境では初期パスワードを必ず変更してください！

## API エンドポイント

### 認証
- `POST /api/auth/login` - ログイン
- `GET /api/auth/me` - 現在のユーザー情報取得

### 検索（全ユーザー）
- `POST /api/search` - 自然言語検索
- `GET /api/search/history` - 検索履歴
- `GET /api/search/facets` - フィルターオプション取得

### ドキュメント管理（管理者のみ）
- `POST /api/documents/upload` - ドキュメントアップロード
- `GET /api/documents` - ドキュメント一覧
- `GET /api/documents/{id}` - ドキュメント詳細
- `GET /api/documents/{id}/download-url` - ダウンロード/プレビューURL取得
- `DELETE /api/documents/{id}` - ドキュメント削除
- `POST /api/documents/{id}/reprocess` - ドキュメント再処理

### システム管理（管理者のみ）
- `GET /api/admin/stats` - システム統計情報
- `POST /api/admin/create-index` - 検索インデックス作成

## デプロイ

**📋 [デプロイチェックリスト](./DEPLOYMENT_CHECKLIST.md)** - デプロイ前の確認項目  
**📖 [詳細なデプロイ手順](./DEPLOYMENT_GUIDE.md)** - ステップバイステップガイド  
**🚀 [GitHub Actions ワークフロー](./.github/workflows/README.md)** - CI/CD設定ガイド

### デプロイ方法

このプロジェクトは **GitHub Actions** による自動デプロイを推奨しています。

1. GitHubリポジトリを作成してコードをプッシュ
2. Azure Portal のデプロイセンターで GitHub を連携
3. 発行プロファイルを GitHub Secrets に登録
4. コードをプッシュすると自動的にデプロイされます

詳細は [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) を参照してください。

### デプロイ済みAzureリソース

| リソース名 | 種類 | リージョン | 用途 | 備考 |
|-----------|------|-----------|------|------|
| aoai-10th | Azure OpenAI | East US | GPT-4o-mini, Embedding | 共用リソース |
| rg-unitech-search | Azure AI Search | Japan East | ナレッジ検索インデックス | 専用 |
| rg-unitech-webapp-frontend | Azure Web App | Japan East | フロントエンドホスティング | 専用 |
| rg-unitech-webapp-backend | Azure Web App | Japan East | バックエンドAPI | 専用 |
| blobeastasiafor10th | Blob Storage | East Asia | ドキュメント保存 | 共用（専用コンテナ） |
| rg-unitech-mysql | MySQL Flexible Server | East Asia | アプリケーションDB | 専用（本番環境推奨） |
| rg-unitech-docintel | Document Intelligence | East US | ドキュメント解析 | 専用 |

**注意事項:**
- **共用リソース**: `aoai-10th`と`blobeastasiafor10th`
- **Blob Storage**: 専用コンテナ`unitech-foods`を使用
- **Azure OpenAI**: AI Foundryからモデルをデプロイ
- **MySQL**: 本番環境では必須、開発環境ではSQLiteで代替可能

## ライセンス

著作権は発注側（ユニテックフーズ株式会社）に帰属

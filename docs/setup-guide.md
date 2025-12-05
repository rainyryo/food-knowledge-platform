# 導入マニュアル

## 目次

1. [必要要件](#必要要件)
2. [Azure リソースの作成](#azure-リソースの作成)
3. [ローカル開発環境のセットアップ](#ローカル開発環境のセットアップ)
4. [Azure へのデプロイ](#azure-へのデプロイ)
5. [初期設定](#初期設定)
6. [データ登録方法](#データ登録方法)
7. [トラブルシューティング](#トラブルシューティング)

---

## 必要要件

### ソフトウェア要件

- Python 3.11以上
- Node.js 18以上
- Git

### Azure リソース

**既にデプロイ済みのリソース:**

| リソース名 | 種類 | リージョン | エンドポイント/URL |
|-----------|------|-----------|-------------------|
| aoai-10th | Azure OpenAI | East US | https://aoai-10th.openai.azure.com/ |
| rg-unitech-search | Azure AI Search | Japan East | https://rg-unitech-search.search.windows.net |
| rg-unitech-webapp-frontend | Azure Web App | Japan East | https://rg-unitech-webapp-frontend.azurewebsites.net |
| rg-unitech-webapp-backend | Azure Web App | Japan East | https://rg-unitech-webapp-backend.azurewebsites.net |
| blobeastasiafor10th | Blob Storage | East Asia | blobeastasiafor10th.blob.core.windows.net |
| rg-unitech-cosmosdb | Cosmos DB | East Asia | https://rg-unitech-cosmosdb.documents.azure.com:443/ |
| rg-unitech-docintel | Document Intelligence | East US | https://rg-unitech-docintel.cognitiveservices.azure.com/ |

**重要な注意事項:**
- `aoai-10th` (Azure OpenAI): 共用リソースです。AI Foundryからモデルをデプロイしてください
- `blobeastasiafor10th` (Blob Storage): 共用リソースです。専用コンテナ`unitech-foods`を作成して使用してください
- すべてのリソースは`rg-001-gen10`リソースグループに所属しています

---

## Azure リソースの設定

**注意:** Azureリソースは既に作成済みです。以下の手順で設定を行ってください。

### 1. Azure OpenAI Service (aoai-10th)

**共用リソースのため、以下の手順でモデルをデプロイしてください:**

1. [Azure AI Foundry](https://ai.azure.com/)にアクセス
2. `aoai-10th`リソースを選択
3. 「デプロイ」セクションで以下のモデルをデプロイ:
   - **GPT-4.1-mini** (チャット生成用)
     - デプロイ名: `gpt-4.1-mini`
     - モデル: gpt-4.1-mini (2025-04-14)
     - TPM: 100K推奨
     - メリット: GPT-4より高速でコスト効率が良い
   - **text-embedding-ada-002** (ベクトル埋め込み用)
     - デプロイ名: `text-embedding-ada-002`
     - TPM: 100K推奨
4. デプロイ名をメモしておく

### 2. Azure AI Search (rg-unitech-search)

1. [Azure Portal](https://portal.azure.com)で`rg-unitech-search`を開く
2. 「キー」セクションで管理キーを確認
3. インデックス名: `food-knowledge-unitech`を使用

### 3. Azure Blob Storage (blobeastasiafor10th)

**共用リソースのため、専用コンテナを作成してください:**

1. [Azure Portal](https://portal.azure.com)で`blobeastasiafor10th`を開く
2. 「コンテナ」セクションで新しいコンテナを作成:
   - コンテナ名: `unitech-foods`
   - パブリックアクセスレベル: プライベート
3. 接続文字列を「アクセスキー」セクションからコピー

### 4. Azure Document Intelligence (rg-unitech-docintel)

1. [Azure Portal](https://portal.azure.com)で`rg-unitech-docintel`を開く
2. 「キーとエンドポイント」セクションでAPIキーとエンドポイントを確認

### 5. Azure Cosmos DB (rg-unitech-cosmosdb) ※オプション

現在はSQLiteを使用していますが、本番環境ではCosmos DBへの移行を推奨します。

---

## ローカル開発環境のセットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd food-knowledge-platform
```

### 2. バックエンドのセットアップ

```bash
cd backend

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp env.template .env
# .env ファイルを編集してAzureの認証情報を設定
# 実際のAPIキーはAzure Portalから取得してください
```

### 3. フロントエンドのセットアップ

```bash
cd frontend

# 依存関係のインストール
npm install
```

### 4. 開発サーバーの起動

バックエンド（ターミナル1）:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

フロントエンド（ターミナル2）:
```bash
cd frontend
npm run dev
```

ブラウザで http://localhost:3000 にアクセス

---

## Azure へのデプロイ

### 方法1: Docker を使用

```bash
# イメージをビルド
docker build -t food-knowledge-platform .

# Azure Container Registry にプッシュ
az acr login --name <your-acr-name>
docker tag food-knowledge-platform <your-acr-name>.azurecr.io/food-knowledge-platform
docker push <your-acr-name>.azurecr.io/food-knowledge-platform

# App Service にデプロイ
az webapp create --resource-group <rg-name> --plan <plan-name> \
  --name food-knowledge-platform \
  --deployment-container-image-name <your-acr-name>.azurecr.io/food-knowledge-platform
```

### 方法2: GitHub Actions を使用

1. `.github/workflows/deploy.yml` を確認
2. GitHub Secrets に以下を設定:
   - `AZURE_WEBAPP_PUBLISH_PROFILE`: Azure Portal からダウンロード
3. main ブランチにプッシュで自動デプロイ

### 方法3: 手動デプロイ

```bash
# フロントエンドをビルド
cd frontend && npm run build
cp -r dist ../backend/static

# バックエンドをZIP化
cd ../backend
zip -r ../deploy.zip . -x "*.pyc" -x "__pycache__/*" -x "venv/*"

# Azure CLIでデプロイ
az webapp deployment source config-zip \
  --resource-group <rg-name> \
  --name <app-name> \
  --src ../deploy.zip
```

### 環境変数の設定

#### バックエンド (rg-unitech-webapp-backend)

Azure Portal > rg-unitech-webapp-backend > 構成 > アプリケーション設定

以下の環境変数を設定:

| 名前 | 値 | 備考 |
|------|-----|------|
| AZURE_OPENAI_ENDPOINT | https://aoai-10th.openai.azure.com/ | 共用リソース |
| AZURE_OPENAI_API_KEY | [Azure Portal で確認] | |
| AZURE_OPENAI_DEPLOYMENT_NAME | gpt-4.1-mini | AI Foundryでデプロイした名前 |
| AZURE_OPENAI_EMBEDDING_DEPLOYMENT | text-embedding-ada-002 | |
| AZURE_OPENAI_API_VERSION | 2024-02-15-preview | |
| AZURE_SEARCH_ENDPOINT | https://rg-unitech-search.search.windows.net | |
| AZURE_SEARCH_API_KEY | [Azure Portal で確認] | |
| AZURE_SEARCH_INDEX_NAME | food-knowledge-unitech | |
| AZURE_DOC_INTELLIGENCE_ENDPOINT | https://rg-unitech-docintel.cognitiveservices.azure.com/ | |
| AZURE_DOC_INTELLIGENCE_KEY | [Azure Portal で確認] | |
| AZURE_STORAGE_CONNECTION_STRING | [Azure Portal で確認] | 共用リソース |
| AZURE_STORAGE_CONTAINER_NAME | unitech-foods | 専用コンテナ |
| SECRET_KEY | [ランダムな文字列を生成] | セキュリティ重要 |
| DATABASE_URL | sqlite:///./food_knowledge.db | または Cosmos DB |

#### フロントエンド (rg-unitech-webapp-frontend)

| 名前 | 値 |
|------|-----|
| VITE_API_URL | https://rg-unitech-webapp-backend.azurewebsites.net |

---

## 初期設定

### 1. 検索インデックスの作成

管理画面にログイン後、「インデックス作成」ボタンをクリック

または API で実行:
```bash
curl -X POST https://your-app.azurewebsites.net/api/admin/create-index \
  -H "Authorization: Bearer <token>"
```

### 2. 初期ユーザー

システム起動時に以下の管理者アカウントが自動作成されます:
- ユーザー名: `admin`
- パスワード: `admin123`

**重要**: 本番環境では必ずパスワードを変更してください。

---

## データ登録方法

### ファイル命名規則

以下の形式に従うと、メタデータが自動抽出されます:

```
[アプリケーション]_[課題感]_[使用原料]_[顧客名]_[試作ID].xlsx
```

例:
- `総菜_離水防止_キサンタンガム_ABC食品_ID4567.xlsx`
- `パン_老化対策_ペクチン_XYZ製パン_ID5678.docx`

### アップロード方法

1. 管理画面にログイン
2. 「ドキュメントアップロード」エリアにファイルをドラッグ＆ドロップ
3. 処理完了を待つ（ステータスが「完了」になる）

### 対応ファイル形式

| 形式 | 説明 |
|-----|------|
| .xlsx, .xls | Excel（メイン形式） |
| .docx, .doc | Word |
| .pptx, .ppt | PowerPoint |
| .pdf | PDF |
| .png, .jpg | 画像 |

---

## トラブルシューティング

### 検索結果が返ってこない

1. インデックスが作成されているか確認
2. ドキュメントのステータスが「完了」になっているか確認
3. Azure AI Search のインデックス数を確認

### アップロードが失敗する

1. ファイルサイズを確認（上限: 50MB）
2. ファイル形式を確認
3. Azure Blob Storage の接続文字列を確認

### 認証エラーが発生する

1. 環境変数が正しく設定されているか確認
2. トークンの有効期限を確認
3. SECRET_KEY が正しいか確認

### 応答が遅い

1. Azure OpenAI のクォータを確認
2. Azure AI Search のスケールを確認
3. チャンクサイズを調整

---

## サポート

問題が解決しない場合は、以下の情報を添えてお問い合わせください:

- エラーメッセージ
- 実行した操作
- 環境情報（OS、ブラウザ等）

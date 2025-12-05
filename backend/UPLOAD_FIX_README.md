# ファイルアップロード問題の修正

## 問題の原因

エクセルファイルのアップロードが「処理中」のまま完了しない問題は、以下の原因で発生していました：

1. **データベースセッションの問題**: バックグラウンドタスクでデータベースセッションが正しく作成されていませんでした
2. **環境変数の未設定**: `.env` ファイルが存在せず、Azure サービスへの接続情報が設定されていませんでした
3. **エラーハンドリングの不足**: Azure サービスへの接続エラーが明確に報告されていませんでした

## 修正内容

### 1. データベースセッションの修正

`main.py` の `process_document_task` 関数で、データベースセッションの作成方法を修正しました：

```python
# 修正前
db = next(get_db())

# 修正後
from database import SessionLocal
db = SessionLocal()
```

### 2. エラーハンドリングの改善

Azure サービスへの接続エラーをより明確に報告するようにしました：

```python
# Azure サービスの設定チェックを追加
if not settings.azure_openai_api_key:
    raise ValueError("Azure OpenAI API キーが設定されていません。.env ファイルを確認してください。")
```

### 3. 修正スクリプトの作成

処理中で止まっているドキュメントを修正するスクリプトを作成しました：

- `fix_stuck_documents.py`: 処理中のドキュメントのステータスを修正

## 次のステップ

### ステップ1: 環境変数の設定

以下のいずれかの方法で `.env` ファイルを作成してください：

#### 方法A: セットアップスクリプトを使用（推奨）

```bash
cd food-knowledge-platform/backend
python setup_env.py
```

その後、生成された `.env` ファイルを編集して、Azure サービスの接続情報を設定してください。

#### 方法B: 手動でコピー

```bash
cd food-knowledge-platform/backend
copy env.template .env
```

その後、`.env` ファイルを編集して、以下の値を設定してください：

- `AZURE_OPENAI_API_KEY`: Azure OpenAI の API キー
- `AZURE_SEARCH_API_KEY`: Azure AI Search の API キー
- `AZURE_DOC_INTELLIGENCE_KEY`: Azure Document Intelligence の API キー
- `AZURE_STORAGE_CONNECTION_STRING`: Azure Blob Storage の接続文字列

### ステップ2: 処理中のドキュメントを修正

現在「処理中」で止まっているドキュメントを修正します：

```bash
cd food-knowledge-platform/backend
python fix_stuck_documents.py
```

### ステップ3: サーバーを再起動

サーバーを再起動して、修正を適用します：

```bash
cd food-knowledge-platform/backend
python start_server.py
```

または：

```bash
cd food-knowledge-platform/backend
start.bat
```

### ステップ4: ファイルを再アップロード

1. ブラウザで管理画面にアクセス: http://localhost:3000/admin
2. 「処理中」だったファイルを削除
3. ファイルを再度アップロード

## ローカル開発のみの場合

Azure サービスの設定なしでローカル開発を行う場合は、以下の機能のみが動作します：

- ✅ ログイン認証
- ✅ ドキュメント一覧の表示
- ✅ ファイルのアップロード（メタデータのみ）
- ❌ ファイルからのテキスト抽出
- ❌ AI検索機能
- ❌ Blobストレージへの保存

完全な機能を使用するには、Azure サービスの設定が必要です。

## トラブルシューティング

### Q: まだ「処理中」のままです

A: 以下を確認してください：

1. サーバーが正しく再起動されているか
2. `.env` ファイルが正しく設定されているか
3. ブラウザのキャッシュをクリアして、ページをリロード

### Q: エラーメッセージが表示されます

A: エラーメッセージを確認して、以下を確認してください：

1. Azure サービスの API キーが正しいか
2. Azure サービスのリソースが存在するか
3. ネットワーク接続が正常か

### Q: PowerShellでコマンドが実行できません

A: Windows環境でPowerShellに問題がある場合は、以下の方法を試してください：

1. コマンドプロンプト (cmd) を使用する
2. Pythonスクリプトを直接ダブルクリックして実行する
3. Visual Studio Code などのIDEから実行する

## サポート

問題が解決しない場合は、以下の情報を添えてお問い合わせください：

- エラーメッセージの全文
- ブラウザのコンソールログ
- サーバーのログ出力
















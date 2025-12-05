# Azure Database for MySQL - Flexible Server セットアップガイド

このガイドでは、Azure Database for MySQL – Flexible Serverをセットアップし、アプリケーションを接続する手順を説明します。

## 📋 前提条件

- Azure サブスクリプション
- Azure Portal へのアクセス権限
- Python 3.11以上

## 🚀 Azure MySQL Flexible Server のセットアップ

### 1. Azure Portal でリソースを作成

1. Azure Portal にログイン
2. 「リソースの作成」→「Azure Database for MySQL - Flexible Server」を選択
3. 以下の情報を入力：

#### 基本設定
- **リソースグループ**: `rg-001-gen10`（既存のリソースグループを使用）
- **サーバー名**: `gen10-mysql-dev-01`（一意の名前）
- **リージョン**: `East Asia`（他のリソースと同じリージョン）
- **MySQL バージョン**: `8.0`
- **ワークロードタイプ**: `開発`または`本番`

#### コンピューティングとストレージ
- **コンピューティング層**: `Burstable`（開発用）または`General Purpose`（本番用）
- **コンピューティングサイズ**: `Standard_B1ms`（最小）
- **ストレージサイズ**: `20 GiB`（初期値）
- **ストレージの自動拡張**: 有効

#### 認証
- **認証方法**: `MySQL 認証のみ`
- **管理者ユーザー名**: `students`
- **パスワード**: `10th-tech0`

#### ネットワーク
- **接続方法**: `パブリック アクセス (許可された IP アドレス)`
- **ファイアウォール規則**: 
  - 開発環境: `Azure サービスへのパブリック アクセスを許可する`を有効化
  - 本番環境: 特定のIPアドレスのみ許可

#### セキュリティ
- **SSL の適用**: `有効`（推奨）
- **TLS バージョン**: `TLS 1.2`以上

### 2. データベースの作成

サーバー作成後、データベースを作成：

1. Azure Portal で作成したMySQLサーバーを開く
2. 「データベース」→「追加」
3. データベース名: `food_knowledge`
4. 文字セット: `utf8mb4`
5. 照合順序: `utf8mb4_unicode_ci`

## 🔧 アプリケーションのセットアップ

### 1. 依存関係のインストール

```bash
cd backend
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルに以下の情報を追加：

```bash
# Azure Database for MySQL - Flexible Server
MYSQL_HOST=gen10-mysql-dev-01.mysql.database.azure.com
MYSQL_PORT=3306
MYSQL_DATABASE=food_knowledge
MYSQL_USER=students
MYSQL_PASSWORD=10th-tech0
MYSQL_SSL_CA=  # オプション: SSL証明書のパス
```

### 3. データベースの初期化

テーブルと初期ユーザーを作成：

```bash
python init_mysql.py
```

実行結果：
```
================================================================================
MySQL Database Initialization
================================================================================

📦 Creating database tables...
✅ Tables created successfully

👤 Creating initial users...
✅ Admin user created: admin / admin123
✅ Regular user created: user / user123

✅ MySQL database initialization completed successfully!

初期アカウント:
  - admin / admin123 (管理者)
  - user / user123 (一般ユーザー)
================================================================================
```

### 4. アプリケーションの起動

```bash
python start_server.py
```

または

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🐛 トラブルシューティング

### エラー: "Can't connect to MySQL server"

**原因**: ファイアウォール規則で接続が許可されていない

**解決方法**:
1. Azure Portal でMySQLサーバーを開く
2. 「ネットワーク」→「ファイアウォール規則」
3. クライアントIPアドレスを追加

### エラー: "SSL connection error"

**原因**: SSL証明書の検証に失敗

**解決方法**:
```python
# SSL検証を緩和（開発環境のみ）
connect_args = {
    "ssl": {
        "ssl_mode": "PREFERRED"  # または "DISABLED"
    }
}
```

### エラー: "Access denied for user"

**原因**: ユーザー名またはパスワードが間違っている

**解決方法**:
1. `.env`ファイルの認証情報を確認
2. Azure Portal でパスワードをリセット

## 💰 コスト管理

### 開発環境の推奨構成

- **コンピューティング**: Burstable B1ms
- **ストレージ**: 20 GiB
- **バックアップ**: 7日間保持
- **推定コスト**: 約 ¥2,000-3,000/月

### 本番環境の推奨構成

- **コンピューティング**: General Purpose D2ds_v4
- **ストレージ**: 100 GiB（自動拡張有効）
- **バックアップ**: 30日間保持
- **高可用性**: 有効
- **推定コスト**: 約 ¥20,000-30,000/月

## 📚 参考資料

- [Azure Database for MySQL ドキュメント](https://docs.microsoft.com/ja-jp/azure/mysql/flexible-server/)
- [SQLAlchemy ドキュメント](https://docs.sqlalchemy.org/)
- [PyMySQL ドキュメント](https://pymysql.readthedocs.io/)

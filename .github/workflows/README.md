# GitHub Actions ワークフロー

このディレクトリには、Azure Web App への自動デプロイ用の GitHub Actions ワークフローが含まれています。

## ワークフロー一覧

### 1. backend-deploy.yml
バックエンド（FastAPI）を Azure Web App にデプロイします。

- **トリガー**: `backend/` フォルダ内のファイルが変更されたとき
- **デプロイ先**: `rg-unitech-webapp-backend`
- **必要な Secret**: `AZURE_WEBAPP_BACKEND_PUBLISH_PROFILE`

### 2. frontend-deploy.yml
フロントエンド（React + Vite）をビルドして Azure Web App にデプロイします。

- **トリガー**: `frontend/` フォルダ内のファイルが変更されたとき
- **デプロイ先**: `rg-unitech-webapp-frontend`
- **必要な Secret**: `AZURE_WEBAPP_FRONTEND_PUBLISH_PROFILE`

## セットアップ手順

### 1. 発行プロファイルの取得

#### バックエンド
1. Azure Portal で `rg-unitech-webapp-backend` を開く
2. 「発行プロファイルの取得」をクリック
3. ダウンロードされた `.PublishSettings` ファイルの内容をコピー

#### フロントエンド
1. Azure Portal で `rg-unitech-webapp-frontend` を開く
2. 「発行プロファイルの取得」をクリック
3. ダウンロードされた `.PublishSettings` ファイルの内容をコピー

### 2. GitHub Secrets の設定

1. GitHubリポジトリを開く
2. **Settings** > **Secrets and variables** > **Actions** に移動
3. **New repository secret** をクリック
4. 以下の2つのシークレットを追加:

#### AZURE_WEBAPP_BACKEND_PUBLISH_PROFILE
- Name: `AZURE_WEBAPP_BACKEND_PUBLISH_PROFILE`
- Value: バックエンドの発行プロファイルの内容（XML全体）

#### AZURE_WEBAPP_FRONTEND_PUBLISH_PROFILE
- Name: `AZURE_WEBAPP_FRONTEND_PUBLISH_PROFILE`
- Value: フロントエンドの発行プロファイルの内容（XML全体）

### 3. デプロイの実行

#### 自動デプロイ
- `backend/` または `frontend/` 内のファイルを変更
- `main` ブランチにプッシュ
- 該当するワークフローが自動的に実行されます

#### 手動デプロイ
1. GitHubリポジトリの **Actions** タブを開く
2. デプロイしたいワークフローを選択
3. **Run workflow** をクリック
4. ブランチを選択して実行

## トラブルシューティング

### デプロイが失敗する場合

1. **GitHub Secrets の確認**
   - 発行プロファイルが正しく設定されているか確認
   - XMLファイル全体がコピーされているか確認

2. **ビルドエラー**
   - Actions タブでログを確認
   - ローカルで `npm run build` または `pip install -r requirements.txt` を実行してエラーを特定

3. **Azure Web App の状態確認**
   - Azure Portal でアプリが実行中か確認
   - ログストリームでエラーを確認

### よくあるエラー

#### Error: No such file or directory
- ワークフローファイルのパス指定を確認
- `package:` の値が正しいか確認

#### Error: Failed to deploy
- 発行プロファイルの有効期限を確認
- Azure Portal で新しい発行プロファイルを取得して更新

## デプロイ先URL

- **フロントエンド**: https://rg-unitech-webapp-frontend.azurewebsites.net
- **バックエンド**: https://rg-unitech-webapp-backend.azurewebsites.net
- **API ドキュメント**: https://rg-unitech-webapp-backend.azurewebsites.net/docs

## 参考資料

- [Azure Web Apps Deploy Action](https://github.com/Azure/webapps-deploy)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)



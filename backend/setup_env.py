"""
環境変数ファイル (.env) をセットアップするスクリプト
"""
import os
import shutil

def setup_env():
    env_file = ".env"
    template_file = "env.template"
    
    # .envファイルが既に存在する場合
    if os.path.exists(env_file):
        print(f"⚠️  {env_file} は既に存在します。")
        response = input("上書きしますか？ (y/N): ")
        if response.lower() != 'y':
            print("キャンセルしました。")
            return
        
        # バックアップを作成
        backup_file = f"{env_file}.backup"
        shutil.copy(env_file, backup_file)
        print(f"📦 既存のファイルを {backup_file} にバックアップしました。")
    
    # テンプレートから .env ファイルを作成
    shutil.copy(template_file, env_file)
    print(f"✅ {env_file} を作成しました。")
    print()
    print("=" * 60)
    print("⚠️  重要: 以下の設定を行ってください")
    print("=" * 60)
    print()
    print(f"1. {env_file} ファイルを開いてください")
    print()
    print("2. 以下の値を実際の値に置き換えてください：")
    print("   - AZURE_OPENAI_API_KEY")
    print("   - AZURE_SEARCH_API_KEY")
    print("   - AZURE_DOC_INTELLIGENCE_KEY")
    print("   - AZURE_STORAGE_CONNECTION_STRING")
    print("   - SECRET_KEY (本番環境)")
    print()
    print("3. 設定が完了したら、サーバーを起動してください：")
    print("   python start_server.py")
    print()
    print("💡 ローカル開発のみの場合は、Azure サービスの設定なしでも")
    print("   基本的な機能（ログイン、ドキュメント一覧など）は動作します。")
    print()

if __name__ == "__main__":
    setup_env()
















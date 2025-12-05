"""
バックエンドサーバー起動スクリプト
venvフォルダを監視対象から除外して安定して起動します
"""
import uvicorn
import os

if __name__ == "__main__":
    # 現在のディレクトリを取得
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    # venvフォルダを監視から除外
    reload_excludes = [
        os.path.join(backend_dir, "venv"),
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "__pycache__",
        "*.db",
        "*.db-journal"
    ]
    
    print("=" * 80)
    print("食品開発ナレッジプラットフォーム - バックエンドサーバー")
    print("=" * 80)
    print(f"起動中...")
    print(f"URL: http://127.0.0.1:8000")
    print(f"APIドキュメント: http://127.0.0.1:8000/docs")
    print("=" * 80)
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_excludes=reload_excludes
    )

















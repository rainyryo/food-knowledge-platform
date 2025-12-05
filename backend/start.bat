@echo off
chcp 65001 > nul
echo ================================================================================
echo 食品開発ナレッジプラットフォーム - バックエンドサーバー
echo ================================================================================
echo.

cd /d "%~dp0"

REM 仮想環境をアクティベート
if exist "venv\Scripts\activate.bat" (
    echo 仮想環境をアクティベート中...
    call venv\Scripts\activate.bat
    
    REM 依存関係を確認・インストール
    echo 依存関係を確認中...
    pip install -q pymysql cryptography 2>nul
) else (
    echo 警告: 仮想環境が見つかりません。グローバル環境で実行します。
)

echo.
echo サーバーを起動中...
echo URL: http://127.0.0.1:8000
echo APIドキュメント: http://127.0.0.1:8000/docs
echo.
echo サーバーを停止するには Ctrl+C を押してください
echo ================================================================================
echo.

REM 安定した起動スクリプトを使用
python start_server.py

pause



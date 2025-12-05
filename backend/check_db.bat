@echo off
chcp 65001 > nul
echo ================================================================================
echo MySQL データベース確認
echo ================================================================================
echo.

cd /d "%~dp0"

REM 仮想環境をアクティベート
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python check_mysql_data.py

echo.
pause







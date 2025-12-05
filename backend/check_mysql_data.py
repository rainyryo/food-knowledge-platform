"""
MySQL データベース確認スクリプト
データベース内のテーブルとデータを表示します
"""
import sys
from sqlalchemy import create_engine, text, inspect
from config import get_settings

settings = get_settings()

def check_database():
    """データベースの内容を確認"""
    
    print("=" * 80)
    print("MySQL データベース確認")
    print("=" * 80)
    print()
    
    # データベース接続
    if not settings.mysql_host:
        print("❌ MySQL設定が見つかりません。SQLiteを使用しています。")
        DATABASE_URL = "sqlite:///./food_knowledge.db"
        connect_args = {"check_same_thread": False}
    else:
        DATABASE_URL = (
            f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
            f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
        )
        # SSL configuration for Azure MySQL
        connect_args = {
            "ssl": {
                "ssl_mode": "REQUIRED"
            }
        }
        if settings.mysql_ssl_ca:
            connect_args["ssl"]["ca"] = settings.mysql_ssl_ca
    
    try:
        engine = create_engine(DATABASE_URL, connect_args=connect_args)
        
        with engine.connect() as conn:
            # データベース情報
            print(f"📊 データベース: {settings.mysql_database if settings.mysql_host else 'SQLite'}")
            if settings.mysql_host:
                print(f"🌐 ホスト: {settings.mysql_host}")
            print()
            
            # テーブル一覧
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"📋 テーブル一覧: {', '.join(tables)}")
            print()
            
            # ユーザーテーブル
            print("-" * 80)
            print("👥 ユーザー (users)")
            print("-" * 80)
            result = conn.execute(text("SELECT id, username, is_admin, created_at FROM users ORDER BY id"))
            users = result.fetchall()
            if users:
                print(f"{'ID':<5} {'ユーザー名':<20} {'管理者':<10} {'作成日時'}")
                print("-" * 70)
                for user in users:
                    is_admin = "✓ admin" if user[2] else "user"
                    print(f"{user[0]:<5} {user[1]:<20} {is_admin:<10} {user[3]}")
                print(f"\n合計: {len(users)}件")
            else:
                print("データなし")
            print()
            
            # ドキュメントテーブル
            print("-" * 80)
            print("📄 ドキュメント (documents)")
            print("-" * 80)
            result = conn.execute(text("""
                SELECT id, filename, file_type, status, created_at, application, issue
                FROM documents 
                ORDER BY created_at DESC
            """))
            documents = result.fetchall()
            if documents:
                print(f"{'ID':<5} {'ファイル名':<40} {'形式':<8} {'ステータス':<12} {'用途':<15} {'課題':<20}")
                print("-" * 110)
                for doc in documents:
                    filename = doc[1][:37] + "..." if len(doc[1]) > 40 else doc[1]
                    status_icon = "✓" if doc[3] == "completed" else "⏳" if doc[3] == "processing" else "✗"
                    application = (doc[5][:12] + "...") if doc[5] and len(doc[5]) > 15 else (doc[5] or "-")
                    issue = (doc[6][:17] + "...") if doc[6] and len(doc[6]) > 20 else (doc[6] or "-")
                    print(f"{doc[0]:<5} {filename:<40} {doc[2] or '-':<8} {status_icon} {doc[3]:<10} {application:<15} {issue:<20}")
                print(f"\n合計: {len(documents)}件")
                
                # ステータス別集計
                result = conn.execute(text("SELECT status, COUNT(*) FROM documents GROUP BY status"))
                status_counts = result.fetchall()
                print("\nステータス別:")
                for status, count in status_counts:
                    status_icon = "✓" if status == "completed" else "⏳" if status == "processing" else "✗"
                    print(f"  {status_icon} {status}: {count}件")
            else:
                print("データなし")
            print()
            
            # 検索履歴テーブル
            print("-" * 80)
            print("🔍 検索履歴 (search_histories)")
            print("-" * 80)
            result = conn.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT user_id) as unique_users
                FROM search_histories
            """))
            stats = result.fetchone()
            
            if stats and stats[0] > 0:
                print(f"総検索回数: {stats[0]}件")
                print(f"検索ユーザー数: {stats[1]}人")
                print()
                
                # 最近の検索
                result = conn.execute(text("""
                    SELECT query, user_id, created_at 
                    FROM search_histories 
                    ORDER BY created_at DESC 
                    LIMIT 10
                """))
                recent_searches = result.fetchall()
                
                if recent_searches:
                    print("最近の検索（最新10件）:")
                    print(f"{'検索クエリ':<60} {'ユーザーID':<12} {'検索日時'}")
                    print("-" * 100)
                    for search in recent_searches:
                        query = search[0][:57] + "..." if len(search[0]) > 60 else search[0]
                        print(f"{query:<60} {search[1]:<12} {search[2]}")
            else:
                print("データなし")
            print()
            
            # ドキュメントチャンクテーブル
            print("-" * 80)
            print("📦 ドキュメントチャンク (document_chunks)")
            print("-" * 80)
            result = conn.execute(text("""
                SELECT COUNT(*) as total_chunks,
                       COUNT(DISTINCT document_id) as documents_with_chunks
                FROM document_chunks
            """))
            chunk_stats = result.fetchone()
            
            if chunk_stats and chunk_stats[0] > 0:
                print(f"総チャンク数: {chunk_stats[0]}件")
                print(f"チャンクを持つドキュメント数: {chunk_stats[1]}件")
                
                # ドキュメント別チャンク数
                result = conn.execute(text("""
                    SELECT d.filename, COUNT(dc.id) as chunk_count
                    FROM documents d
                    LEFT JOIN document_chunks dc ON d.id = dc.document_id
                    GROUP BY d.id, d.filename
                    HAVING chunk_count > 0
                    ORDER BY chunk_count DESC
                    LIMIT 10
                """))
                doc_chunks = result.fetchall()
                
                if doc_chunks:
                    print("\nドキュメント別チャンク数（上位10件）:")
                    for i, (filename, count) in enumerate(doc_chunks, 1):
                        filename_short = filename[:50] + "..." if len(filename) > 53 else filename
                        print(f"  {i:2d}. {filename_short:<53} ({count}チャンク)")
            else:
                print("データなし")
            print()
            
            # システムログテーブル
            print("-" * 80)
            print("📋 システムログ (system_logs)")
            print("-" * 80)
            result = conn.execute(text("""
                SELECT COUNT(*) as total_logs,
                       SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) as errors,
                       SUM(CASE WHEN level = 'WARNING' THEN 1 ELSE 0 END) as warnings,
                       SUM(CASE WHEN level = 'INFO' THEN 1 ELSE 0 END) as info
                FROM system_logs
            """))
            log_stats = result.fetchone()
            
            if log_stats and log_stats[0] > 0:
                print(f"総ログ数: {log_stats[0]}件")
                print(f"  ❌ ERROR: {log_stats[1]}件")
                print(f"  ⚠️  WARNING: {log_stats[2]}件")
                print(f"  ℹ️  INFO: {log_stats[3]}件")
                
                # 最新のエラーログ
                if log_stats[1] > 0:
                    result = conn.execute(text("""
                        SELECT message, created_at
                        FROM system_logs
                        WHERE level = 'ERROR'
                        ORDER BY created_at DESC
                        LIMIT 5
                    """))
                    recent_errors = result.fetchall()
                    
                    if recent_errors:
                        print("\n最新のエラー（5件）:")
                        for i, (message, created_at) in enumerate(recent_errors, 1):
                            message_short = message[:70] + "..." if len(message) > 73 else message
                            print(f"  {i}. [{created_at}] {message_short}")
            else:
                print("データなし")
            print()
            
            print("=" * 80)
            print("✅ データベース確認完了")
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)



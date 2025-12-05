"""
処理中で止まっているドキュメントを修正するスクリプト
"""
from database import SessionLocal
from models import Document
from datetime import datetime, timedelta

db = SessionLocal()

try:
    # 10分以上 "processing" 状態のドキュメントを検索
    ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
    
    stuck_docs = db.query(Document).filter(
        Document.status.in_(["pending", "processing"]),
        Document.created_at < ten_minutes_ago
    ).all()
    
    if not stuck_docs:
        print("処理中で止まっているドキュメントはありません。")
    else:
        print(f"{len(stuck_docs)}件の止まっているドキュメントを見つけました。\n")
        
        for doc in stuck_docs:
            print(f"ID: {doc.id}")
            print(f"  ファイル名: {doc.original_filename}")
            print(f"  現在のステータス: {doc.status}")
            print(f"  登録日時: {doc.created_at}")
            
            # ステータスを "error" に更新
            doc.status = "error"
            doc.error_message = "処理がタイムアウトしました。Azure サービスの接続設定を確認してください。"
            print(f"  → ステータスを 'error' に更新しました\n")
        
        db.commit()
        print(f"✅ {len(stuck_docs)}件のドキュメントを修正しました。")
        
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
















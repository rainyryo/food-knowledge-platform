"""
管理者ユーザーのパスワードをリセットするスクリプト
"""
from database import SessionLocal, init_db
from models import User
from auth import get_password_hash

def reset_admin_password():
    # データベース初期化
    init_db()
    
    db = SessionLocal()
    try:
        # 管理者ユーザーを取得
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            print("✗ 管理者ユーザーが見つかりません")
            print("python create_admin.py を実行してください")
            return
        
        # パスワードを再ハッシュ化
        new_password = "admin123"
        admin.hashed_password = get_password_hash(new_password)
        db.commit()
        
        print("✓ 管理者パスワードをリセットしました")
        print(f"  ユーザー名: admin")
        print(f"  新しいパスワード: {new_password}")
        print(f"  メール: {admin.email}")
        
    except Exception as e:
        print(f"✗ エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()

















"""
一般ユーザーを作成するスクリプト
"""
from database import SessionLocal, init_db
from models import User
from auth import get_password_hash

def create_regular_user():
    # データベース初期化
    init_db()
    
    db = SessionLocal()
    try:
        # 既存のuserを確認
        user = db.query(User).filter(User.username == "user").first()
        
        if user:
            print("✓ ユーザー 'user' は既に存在します")
            print(f"  ユーザー名: {user.username}")
            print(f"  メール: {user.email}")
            print(f"  管理者権限: {user.is_admin}")
            print(f"  アクティブ: {user.is_active}")
        else:
            # 新しい一般ユーザーを作成
            user = User(
                username="user",
                email="user@unitecfoods.co.jp",
                hashed_password=get_password_hash("user123"),
                full_name="一般ユーザー",
                is_active=True,
                is_admin=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            print("✓ 一般ユーザーを作成しました")
            print(f"  ユーザー名: user")
            print(f"  パスワード: user123")
            print(f"  メール: {user.email}")
        
        # すべてのユーザーを表示
        all_users = db.query(User).all()
        print(f"\n登録ユーザー数: {len(all_users)}")
        for u in all_users:
            role = "管理者" if u.is_admin else "ユーザー"
            print(f"  - {u.username} ({u.email}) [{role}]")
            
    except Exception as e:
        print(f"✗ エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_regular_user()











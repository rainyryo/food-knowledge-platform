"""
初期管理者ユーザーを作成するスクリプト
"""
from database import SessionLocal, init_db
from models import User
from auth import get_password_hash

def create_admin_user():
    # データベース初期化
    init_db()
    
    db = SessionLocal()
    try:
        # 既存のadminユーザーを確認
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            print("✓ 管理者ユーザーは既に存在します")
            print(f"  ユーザー名: {admin.username}")
            print(f"  メール: {admin.email}")
            print(f"  管理者権限: {admin.is_admin}")
            print(f"  アクティブ: {admin.is_active}")
        else:
            # 新しい管理者ユーザーを作成
            admin = User(
                username="admin",
                email="admin@unitecfoods.co.jp",
                hashed_password=get_password_hash("admin123"),
                full_name="管理者",
                is_active=True,
                is_admin=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            
            print("✓ 管理者ユーザーを作成しました")
            print(f"  ユーザー名: admin")
            print(f"  パスワード: admin123")
            print(f"  メール: {admin.email}")
        
        # すべてのユーザーを表示
        all_users = db.query(User).all()
        print(f"\n登録ユーザー数: {len(all_users)}")
        for user in all_users:
            print(f"  - {user.username} ({user.email}) [管理者: {user.is_admin}]")
            
    except Exception as e:
        print(f"✗ エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()

















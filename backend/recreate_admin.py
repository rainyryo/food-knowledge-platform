"""
管理者ユーザーを削除してから再作成するスクリプト
"""
from database import SessionLocal, init_db
from models import User
from auth import get_password_hash

def recreate_admin():
    # データベース初期化
    init_db()
    
    db = SessionLocal()
    try:
        # 既存の管理者ユーザーを削除
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            db.delete(admin)
            db.commit()
            print("✓ 既存の管理者ユーザーを削除しました")
        
        # 新しい管理者ユーザーを作成（bcryptでハッシュ化）
        new_admin = User(
            username="admin",
            email="admin@unitecfoods.co.jp",
            hashed_password=get_password_hash("admin123"),
            full_name="管理者",
            is_active=True,
            is_admin=True
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        
        print("✓ 新しい管理者ユーザーを作成しました（bcryptハッシュ）")
        print(f"  ユーザー名: admin")
        print(f"  パスワード: admin123")
        print(f"  メール: {new_admin.email}")
        
        # すべてのユーザーを表示
        all_users = db.query(User).all()
        print(f"\n登録ユーザー数: {len(all_users)}")
        for user in all_users:
            print(f"  - {user.username} ({user.email}) [管理者: {user.is_admin}]")
            
    except Exception as e:
        print(f"✗ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    recreate_admin()

















"""
Initialize MySQL database with tables and initial data
"""
import sys
from database import engine, SessionLocal
from models import Base, User
from auth import get_password_hash

def init_database():
    """Initialize database tables"""
    print("=" * 80)
    print("MySQL Database Initialization")
    print("=" * 80)
    
    try:
        # Create all tables
        print("\n📦 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
        
        # Create initial users
        print("\n👤 Creating initial users...")
        db = SessionLocal()
        
        try:
            # Check if admin exists
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                admin = User(
                    username="admin",
                    email="admin@unitecfoods.co.jp",
                    hashed_password=get_password_hash("admin123"),
                    full_name="管理者",
                    is_active=True,
                    is_admin=True
                )
                db.add(admin)
                print("✅ Admin user created: admin / admin123")
            else:
                print("ℹ️  Admin user already exists")
            
            # Check if regular user exists
            user = db.query(User).filter(User.username == "user").first()
            if not user:
                user = User(
                    username="user",
                    email="user@unitecfoods.co.jp",
                    hashed_password=get_password_hash("user123"),
                    full_name="一般ユーザー",
                    is_active=True,
                    is_admin=False
                )
                db.add(user)
                print("✅ Regular user created: user / user123")
            else:
                print("ℹ️  Regular user already exists")
            
            db.commit()
            
        finally:
            db.close()
        
        print("\n✅ MySQL database initialization completed successfully!")
        print("\n初期アカウント:")
        print("  - admin / admin123 (管理者)")
        print("  - user / user123 (一般ユーザー)")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    init_database()








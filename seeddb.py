import os
import sys

# Ensure current directory is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from models.user import User
from werkzeug.security import generate_password_hash

def seed_admin():
    with app.app_context():
        print("=" * 60)
        print("[*] SEEDING ADMIN ACCOUNT...")
        print("=" * 60)

        admin_email = "admin@gmail.com"
        admin_pass = "admin123"
        admin_user = User.query.filter_by(email=admin_email).first()

        if not admin_user:
            admin_user = User(
                name="System Administrator",
                email=admin_email,
                password=generate_password_hash(admin_pass),
                role="Administrator",
                status="active",
                avatar=f"https://ui-avatars.com/api/?name=Admin&background=0D8ABC&color=fff"
            )
            db.session.add(admin_user)
            print(f"[OK] Created Admin User: {admin_email}")
        else:
            admin_user.password = generate_password_hash(admin_pass)
            admin_user.role = "Administrator"
            admin_user.status = "active"
            print(f"[OK] Updated Admin Password: {admin_email}")

        db.session.commit()

        print("\n" + "=" * 60)
        print("[SUCCESS] ADMIN SEED COMPLETED!")
        print("=" * 60)
        print(f"   Email:     {admin_email}")
        print(f"   Password: {admin_pass}")
        print(f"   Login at: http://127.0.0.1:9000/admin/login")
        print("=" * 60)

if __name__ == '__main__':
    seed_admin()
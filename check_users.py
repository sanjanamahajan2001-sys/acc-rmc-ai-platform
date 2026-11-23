import sys
import os

PLATFORM_DIR = "/home/sanjana/acc-rmc-ai-platform"
if PLATFORM_DIR not in sys.path:
    sys.path.insert(0, PLATFORM_DIR)
os.chdir(PLATFORM_DIR)

from src.database.session import get_session_factory
from src.database.models.user import User, Role, UserRole
from src.security.crypto import verify_password

def check():
    session = get_session_factory()()
    try:
        users = session.query(User).all()
        print(f"Total users in DB: {len(users)}")
        for u in users:
            roles = [r.role_id for r in u.role_assignments]
            print(f"User: {u.id} | username: {u.username} | email: {u.email} | roles: {roles} | status: {u.account_status} | must_change_pw: {u.must_change_password} | failed_attempts: {u.failed_login_attempts} | lockout_until: {u.lockout_until}")
            print(f"  -> Password 'Admin@123456' match: {verify_password('Admin@123456', u.password_hash)}")
    finally:
        session.close()

if __name__ == "__main__":
    check()

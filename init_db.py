# init_db.py (Enhanced for Debugging)
import os

print("--- [START] init_db.py script is running ---")

try:
    print("[1] Importing 'app', 'db', and 'User' from app.py...")
    from app import app, db, User, Customer, Payment
    print("[2] Imports successful.")
except ImportError as e:
    print(f"[ERROR] Failed to import from app.py. Make sure the file exists and has no syntax errors. Error: {e}")
    exit()

def create_database_and_admin():
    """Creates the database tables and the default admin user."""
    print("[3] Setting up the application context...")
    try:
        with app.app_context():
            print("[4] Application context is active. Now creating all database tables...")
            db.create_all()
            print("[5] db.create_all() command finished.")

            # Verify that the user table was created
            print("[6] Checking if 'user' table exists in database metadata...")
            if 'user' in db.metadata.tables:
                print("    'user' table confirmed in metadata.")
            else:
                print("    [CRITICAL ERROR] 'user' table was NOT created. Check your User model in app.py.")
                return

            print("[7] Checking if admin user already exists...")
            if User.query.filter_by(username='admin').first():
                print("    Admin user already exists. No action taken.")
            else:
                print("    Admin user not found. Creating a new one...")
                admin_user = User(username='admin', is_admin=True)
                admin_user.set_password('admin')
                db.session.add(admin_user)
                db.session.commit()
                print("    [SUCCESS] Default admin user created with username 'admin' and password 'admin'")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] An exception occurred during database setup: {e}\n")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("[INIT] Script's main block is being executed.")
    create_database_and_admin()
    print("--- [END] init_db.py script has finished. ---")
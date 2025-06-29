from app import app
from models import db, User, RoomPreference

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
        
        # Optional: Print table information
        print("Tables in database:")
        print("- users")
        print("- room_preferences")

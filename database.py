from app import app
from models import db, User, RoomPreference, SwapRequest

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database reset completed successfully!")
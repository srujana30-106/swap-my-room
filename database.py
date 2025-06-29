from app import app, db
from app import User, RoomPreference  # make sure models are imported

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Tables dropped and recreated successfully.")

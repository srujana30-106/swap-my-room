from app import app, db
from app import User, RoomPreference, SwapRequest  # make sure models are imported

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Tables dropped and recreated successfully.")

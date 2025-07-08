from app import app
from models import db, User, RoomPreference, SwapRequest  # make sure models are imported

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database tables created successfully!")
        
    
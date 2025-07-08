from app import app
from models import db, User, RoomPreference, SwapRequest  # make sure models are imported

if __name__ == '__main__':
    with app.app_context():
        
        db.create_all()
        print("Done.")
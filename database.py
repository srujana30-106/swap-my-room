from app import app
from models import db, User, RoomPreference, SwapRequest  # make sure models are imported

if __name__ == '__main__':
    with app.app_context():
        print("Dropping all tables...")
        db.reflect()
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Done.")
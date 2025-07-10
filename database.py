from app import app
from models import db, User, RoomPreference, SwapRequest
from add_swap_availability import add_swap_availability_column

if __name__ == '__main__':
    with app.app_context():
        print("Setting up database...")
        db.reflect()
        db.drop_all()
        
        # Create all tables
        db.create_all()
        print("✓ All tables created successfully!")
        
        # Add the swap availability column using the existing migration
        add_swap_availability_column()
        
        print("✓ Database setup completed successfully!")
        print("You can now run: python app.py")
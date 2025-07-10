from app import app
from models import db
import psycopg2
from config import Config

def add_swap_availability_column():
    """
    Migration script to add is_looking_to_swap column to users table
    """
    try:
        with app.app_context():
            # Get the database URL
            database_url = app.config['SQLALCHEMY_DATABASE_URI']
            
            # Connect directly to PostgreSQL to run ALTER TABLE command
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Add the is_looking_to_swap column
            alter_query = "ALTER TABLE users ADD COLUMN is_looking_to_swap BOOLEAN DEFAULT TRUE;"
            cursor.execute(alter_query)
            
            # Commit the changes
            conn.commit()
            cursor.close()
            conn.close()
            
            print("Successfully added is_looking_to_swap column to users table")
            print("All existing users are set to 'looking to swap' by default")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        print("This might be normal if the column was already added")

if __name__ == '__main__':
    add_swap_availability_column() 
from app import app
from models import db
import psycopg2
from config import Config

def migrate_phone_field():
    """
    Migration script to update phone field from VARCHAR(10) to VARCHAR(15)
    """
    try:
        with app.app_context():
            # Get the database URL
            database_url = app.config['SQLALCHEMY_DATABASE_URI']
            
            # Connect directly to PostgreSQL to run ALTER TABLE command
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Alter the phone column to allow 15 characters
            alter_query = "ALTER TABLE users ALTER COLUMN phone TYPE VARCHAR(15);"
            cursor.execute(alter_query)
            
            # Commit the changes
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ Successfully migrated phone field from VARCHAR(10) to VARCHAR(15)")
            print("📱 Phone numbers can now accommodate country codes!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("💡 This might be normal if the table was already updated")

if __name__ == '__main__':
    migrate_phone_field() 
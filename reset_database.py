#!/usr/bin/env python3
"""
Script to completely reset the PostgreSQL database
This will delete ALL data and create fresh tables
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def reset_database():
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("Error: DATABASE_URL not found in environment variables")
        return
    
    print(f"Connecting to database...")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        conn.autocommit = True  # Important for DDL operations
        cursor = conn.cursor()
        
        print("Dropping all tables and schema...")
        
        # Drop the entire public schema (this will remove all tables, data, etc.)
        cursor.execute("DROP SCHEMA IF EXISTS public CASCADE")
        
        # Recreate the public schema
        cursor.execute("CREATE SCHEMA public")
        
        # Grant permissions
        cursor.execute("GRANT ALL ON SCHEMA public TO postgres")
        cursor.execute("GRANT ALL ON SCHEMA public TO public")
        
        print("Schema reset completed successfully!")
        
        cursor.close()
        conn.close()
        
        print("Now creating new tables...")
        
        # Now run the Flask app to create new tables
        from app import app
        from models import db
        
        with app.app_context():
            db.create_all()
            print("New tables created successfully!")
            print("Database reset completed!")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Please check your database connection and try again.")

if __name__ == "__main__":
    print("WARNING: This will delete ALL existing data!")
    confirm = input("Are you sure you want to continue? (yes/no): ")
    
    if confirm.lower() == 'yes':
        reset_database()
    else:
        print("Database reset cancelled.") 
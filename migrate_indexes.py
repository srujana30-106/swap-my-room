from app import app, db
from sqlalchemy import text

def add_indexes():
    """Add database indexes for better query performance"""
    with app.app_context():
        try:
            # Check if indexes already exist and create them if they don't
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_college_id ON users(college_id);",
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);", 
                "CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);",
                "CREATE INDEX IF NOT EXISTS idx_room_preferences_user_id ON room_preferences(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_room_preferences_available ON room_preferences(available);",
                "CREATE INDEX IF NOT EXISTS idx_room_preferences_needed ON room_preferences(needed);",
                "CREATE INDEX IF NOT EXISTS idx_room_preferences_selected ON room_preferences(selected);",
                "CREATE INDEX IF NOT EXISTS idx_room_preferences_accepted_by ON room_preferences(accepted_by);",
                "CREATE INDEX IF NOT EXISTS idx_room_preferences_created_at ON room_preferences(created_at);"
            ]
            
            for index_sql in indexes:
                try:
                    db.session.execute(text(index_sql))
                    print(f"✅ Added index: {index_sql.split(' ON ')[1].split('(')[0]}")
                except Exception as e:
                    print(f"⚠️  Index may already exist or error: {e}")
            
            db.session.commit()
            print("\n🎉 Database index migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during migration: {e}")

if __name__ == "__main__":
    add_indexes() 
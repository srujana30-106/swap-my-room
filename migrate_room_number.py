#!/usr/bin/env python3
"""
Migration script to add room_number field to existing users.
This script will prompt for room numbers for existing users.
"""

import sqlite3
import os

def migrate_room_numbers():
    db_path = 'instance/local_dev.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if room_number column already exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'room_number' not in columns:
        print("Adding room_number column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN room_number TEXT")
        conn.commit()
        print("Column added successfully!")
    else:
        print("room_number column already exists.")
    
    # Get all users without room numbers
    cursor.execute("SELECT id, name FROM users WHERE room_number IS NULL OR room_number = ''")
    users_without_room = cursor.fetchall()
    
    if not users_without_room:
        print("All users already have room numbers assigned.")
        conn.close()
        return
    
    print(f"\nFound {len(users_without_room)} users without room numbers:")
    for user_id, name in users_without_room:
        print(f"  - {name} (ID: {user_id})")
    
    print("\nPlease provide room numbers for each user:")
    
    for user_id, name in users_without_room:
        while True:
            room_number = input(f"Enter room number for {name}: ").strip().upper()
            if room_number:
                cursor.execute("UPDATE users SET room_number = ? WHERE id = ?", (room_number, user_id))
                print(f"  ✓ Updated {name} with room number: {room_number}")
                break
            else:
                print("  Room number cannot be empty. Please try again.")
    
    conn.commit()
    conn.close()
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate_room_numbers() 
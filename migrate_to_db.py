#!/usr/bin/env python3
"""
Migration script to move from file-based storage to SQLite database
"""

import json
import os
from database import Database
from message_processor import MessageProcessor

def migrate_messages():
    """Migrate messages from JSON file to database"""
    filename = 'message_history.json'
    
    if not os.path.exists(filename):
        print(f"✅ No existing message file found: {filename}")
        return
    
    try:
        # Load messages from file
        with open(filename, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        if not messages:
            print("✅ No messages to migrate")
            return
        
        # Initialize database
        db = Database()
        
        # Migrate each message
        migrated_count = 0
        for message in messages:
            # Ensure all required fields are present
            if 'response' not in message:
                message['response'] = ''
            
            # Save to database
            db.save_message(message)
            migrated_count += 1
        
        print(f"✅ Successfully migrated {migrated_count} messages to database")
        
        # Create backup of original file
        backup_filename = f"{filename}.backup"
        os.rename(filename, backup_filename)
        print(f"✅ Original file backed up as: {backup_filename}")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")

def check_database():
    """Check database status"""
    try:
        db = Database()
        stats = db.get_statistics()
        db_size = db.get_database_size()
        
        print("📊 Database Status:")
        print(f"   Size: {db_size} bytes ({round(db_size / 1024, 2)} KB)")
        print(f"   Total messages: {stats['total_messages']}")
        print(f"   Pill confirmed: {stats['pill_confirmed']}")
        print(f"   Pill missed: {stats['pill_missed']}")
        print(f"   Help requests: {stats['help_requests']}")
        print(f"   Unknown commands: {stats['unknown_commands']}")
        print(f"   AI processed: {stats['ai_processed']}")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == '__main__':
    print("🔄 Starting migration to database...")
    
    # Check if database already has data
    db = Database()
    existing_stats = db.get_statistics()
    
    if existing_stats['total_messages'] > 0:
        print(f"⚠️  Database already contains {existing_stats['total_messages']} messages")
        response = input("Do you want to continue with migration? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled")
            exit(0)
    
    # Perform migration
    migrate_messages()
    
    # Check final status
    print("\n📊 Final Database Status:")
    check_database()
    
    print("\n✅ Migration completed!") 
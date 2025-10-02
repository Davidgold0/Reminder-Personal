#!/usr/bin/env python3
"""
Test script to verify MySQL database connectivity for Railway deployment
"""

import os
import sys
from config import Config

def test_config():
    """Test that configuration is loaded correctly"""
    print("🔧 Testing configuration...")
    
    print(f"USE_MYSQL: {Config.USE_MYSQL}")
    print(f"DATABASE_URL present: {'✅' if Config.DATABASE_URL else '❌'}")
    
    if not Config.USE_MYSQL:
        print("❌ USE_MYSQL is False - set USE_MYSQL=true in environment")
        return False
    
    return True

def test_mysql_connection():
    """Test MySQL database connection"""
    print("\n🗄️  Testing MySQL connection...")
    
    try:
        from database import Database
        
        # Try to create database instance
        print("Creating Database instance...")
        db = Database()
        print("✅ Database instance created successfully")
        
        # Try to get connection
        print("Testing database connection...")
        with db.get_connection() as conn:
            if conn.is_connected():
                print("✅ MySQL connection successful")
                
                # Get database info
                cursor = conn.cursor()
                cursor.execute("SELECT DATABASE() as db_name, VERSION() as version")
                result = cursor.fetchone()
                print(f"📊 Database: {result[0]}")
                print(f"🔧 MySQL Version: {result[1]}")
                
                return True
            else:
                print("❌ Connection failed")
                return False
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try installing mysql-connector-python: pip install mysql-connector-python")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Check that DATABASE_URL is set correctly")
        print("2. Verify MySQL service is running on Railway")
        print("3. Check network connectivity")
        return False

def test_table_creation():
    """Test that tables can be created"""
    print("\n📋 Testing table creation...")
    
    try:
        from database import Database
        
        db = Database()
        print("✅ Tables created successfully")
        
        # Test a simple query
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            expected_tables = ['messages', 'reminders', 'statistics', 'customers', 'daily_reminders']
            found_tables = [table[0] for table in tables]
            
            print(f"📊 Found tables: {found_tables}")
            
            all_tables_exist = all(table in found_tables for table in expected_tables)
            if all_tables_exist:
                print("✅ All required tables exist")
                return True
            else:
                missing = [t for t in expected_tables if t not in found_tables]
                print(f"❌ Missing tables: {missing}")
                return False
                
    except Exception as e:
        print(f"❌ Table creation error: {e}")
        return False

def test_basic_operations():
    """Test basic database operations"""
    print("\n🔄 Testing basic operations...")
    
    try:
        from database import Database
        
        db = Database()
        
        # Test saving a message
        test_message = {
            'sender': 'test_user',
            'message': 'Test message for MySQL migration',
            'timestamp': '2024-01-01T00:00:00',
            'action': 'test',
            'ai_processed': False,
            'response': 'Test response'
        }
        
        message_id = db.save_message(test_message)
        print(f"✅ Message saved with ID: {message_id}")
        
        # Test getting message history
        messages = db.get_message_history(limit=1)
        if messages and len(messages) > 0:
            print(f"✅ Retrieved {len(messages)} message(s)")
        else:
            print("⚠️  No messages found, but this might be expected for a new database")
        
        # Test statistics
        stats = db.get_statistics()
        print(f"✅ Statistics retrieved: {stats.get('total_messages', 0)} total messages")
        
        return True
        
    except Exception as e:
        print(f"❌ Operation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 MySQL Database Migration Test")
    print("=" * 50)
    
    # Set test environment if needed
    if not os.getenv('DATABASE_URL') and not os.getenv('MYSQL_HOST'):
        print("⚠️  No database configuration found.")
        print("For local testing, you can set these environment variables:")
        print("  - DATABASE_URL (Railway format)")
        print("  - Or MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD")
        print("\nFor Railway deployment, DATABASE_URL will be provided automatically.")
        
    tests = [
        ("Configuration", test_config),
        ("MySQL Connection", test_mysql_connection),
        ("Table Creation", test_table_creation),
        ("Basic Operations", test_basic_operations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"\n❌ {test_name} test failed")
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MySQL migration is ready for Railway deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Please fix the issues before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
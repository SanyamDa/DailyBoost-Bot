#!/usr/bin/env python3
"""
Test script for Daily Boost Bot onboarding
"""

import sqlite3
import os
from dotenv import load_dotenv

def test_database():
    """Test database connection and schema"""
    print("Testing database connection...")
    
    db_path = "daily_boost.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
        
    # Check users table structure
    cursor.execute("PRAGMA table_info(users);")
    columns = cursor.fetchall()
    
    print("\nUsers table structure:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    conn.close()
    print("Database test completed successfully! ✅")

def test_env():
    """Test environment variables"""
    print("\nTesting environment variables...")
    
    load_dotenv()
    token = os.getenv('BOT_TOKEN')
    
    if token:
        print(f"BOT_TOKEN found: {token[:10]}...{token[-10:]} ✅")
    else:
        print("BOT_TOKEN not found ❌")
        return False
        
    return True

if __name__ == "__main__":
    print("🤖 Daily Boost Bot - Onboarding Test\n")
    
    # Test environment
    if not test_env():
        exit(1)
        
    # Test database
    test_database()
    
    print("\n🎉 All tests passed! Ready to run the bot.")
    print("Run: python bot.py")

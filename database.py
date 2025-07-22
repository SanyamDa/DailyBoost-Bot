"""
Database module for Daily Boost Bot
Handles all SQLite database operations
"""

import sqlite3
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "daily_boost.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                preferred_name TEXT,
                timezone TEXT DEFAULT 'UTC',
                bedtime TEXT DEFAULT '22:00',
                waketime TEXT DEFAULT '07:00',
                water_target INTEGER DEFAULT 2500,
                spiritual_enabled BOOLEAN DEFAULT FALSE,
                reading_enabled BOOLEAN DEFAULT FALSE,
                habits_enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Mood journal table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mood_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date DATE,
                mood_score INTEGER,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Custom habits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                habit_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Habit logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                habit_id INTEGER,
                date DATE,
                completed BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (habit_id) REFERENCES habits (id)
            )
        ''')
        
        # Water intake table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS water_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date DATE,
                amount_ml INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Physical activity table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date DATE,
                activity_text TEXT,
                minutes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Spiritual check table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spiritual_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date DATE,
                prayer_done BOOLEAN DEFAULT FALSE,
                scripture_done BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Reading tracker table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reading_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date DATE,
                minutes INTEGER,
                book_title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Spiritual settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spiritual_settings (
                user_id INTEGER PRIMARY KEY,
                prayer_label TEXT DEFAULT 'Prayer',
                scripture_label TEXT DEFAULT 'Scripture',
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
        
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        return None
        
    def create_user(self, user_id: int, username: str = "", preferred_name: str = "") -> bool:
        """Create a new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, preferred_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, preferred_name))
            conn.commit()
            conn.close()
            logger.info(f"User {user_id} created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            return False
            
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information"""
        if not kwargs:
            return False
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Build dynamic update query
            set_clauses = []
            values = []
            for key, value in kwargs.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(user_id)  # For WHERE clause
            
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?"
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            logger.info(f"User {user_id} updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False

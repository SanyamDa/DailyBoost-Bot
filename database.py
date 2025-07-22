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
    
    # Mood tracking methods
    def add_mood_entry(self, user_id: int, mood_score: int, note: str = None, date: str = None) -> bool:
        """Add or update a mood entry"""
        if date is None:
            from datetime import date as dt
            date = dt.today().isoformat()
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if entry exists for today
            cursor.execute(
                "SELECT id FROM mood_logs WHERE user_id = ? AND date = ?",
                (user_id, date)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing entry
                cursor.execute(
                    "UPDATE mood_logs SET mood_score = ?, note = ? WHERE id = ?",
                    (mood_score, note, existing[0])
                )
            else:
                # Insert new entry
                cursor.execute(
                    "INSERT INTO mood_logs (user_id, date, mood_score, note) VALUES (?, ?, ?, ?)",
                    (user_id, date, mood_score, note)
                )
            
            conn.commit()
            conn.close()
            logger.info(f"Mood entry added for user {user_id}: {mood_score}/5")
            return True
        except Exception as e:
            logger.error(f"Error adding mood entry for user {user_id}: {e}")
            return False
    
    def get_mood_entry(self, user_id: int, date: str = None) -> Optional[Dict[str, Any]]:
        """Get mood entry for a specific date"""
        if date is None:
            from datetime import date as dt
            date = dt.today().isoformat()
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM mood_logs WHERE user_id = ? AND date = ?",
                (user_id, date)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            return None
        except Exception as e:
            logger.error(f"Error getting mood entry for user {user_id}: {e}")
            return None
    
    def get_mood_entries_for_month(self, user_id: int, year: int, month: int) -> List[Dict[str, Any]]:
        """Get all mood entries for a specific month"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM mood_logs 
                   WHERE user_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
                   ORDER BY date""",
                (user_id, str(year), f"{month:02d}")
            )
            results = cursor.fetchall()
            conn.close()
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting mood entries for user {user_id}: {e}")
            return []
    
    def get_mood_stats(self, user_id: int, year: int, month: int) -> Dict[str, Any]:
        """Get mood statistics for a specific month"""
        entries = self.get_mood_entries_for_month(user_id, year, month)
        if not entries:
            return {
                'total_entries': 0,
                'average_rating': 0,
                'highest_rating': 0,
                'lowest_rating': 0
            }
        
        ratings = [entry['mood_score'] for entry in entries]
        return {
            'total_entries': len(entries),
            'average_rating': sum(ratings) / len(ratings),
            'highest_rating': max(ratings),
            'lowest_rating': min(ratings)
        }
    
    # Habit tracking methods
    def add_habit(self, user_id: int, habit_name: str) -> bool:
        """Add a new habit for user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO habits (user_id, habit_name) VALUES (?, ?)",
                (user_id, habit_name)
            )
            conn.commit()
            conn.close()
            logger.info(f"Habit '{habit_name}' added for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding habit for user {user_id}: {e}")
            return False
    
    def get_user_habits(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all habits for a user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM habits WHERE user_id = ? ORDER BY habit_name",
                (user_id,)
            )
            results = cursor.fetchall()
            conn.close()
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting habits for user {user_id}: {e}")
            return []
    
    def delete_habit(self, user_id: int, habit_id: int) -> bool:
        """Delete a habit and all its logs"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Delete habit logs first
            cursor.execute(
                "DELETE FROM habit_logs WHERE user_id = ? AND habit_id = ?",
                (user_id, habit_id)
            )
            
            # Delete habit
            cursor.execute(
                "DELETE FROM habits WHERE user_id = ? AND id = ?",
                (user_id, habit_id)
            )
            
            conn.commit()
            conn.close()
            logger.info(f"Habit {habit_id} deleted for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting habit for user {user_id}: {e}")
            return False
    
    def log_habit(self, user_id: int, habit_id: int, completed: bool, date: str = None) -> bool:
        """Log habit completion for a date"""
        if date is None:
            from datetime import date as dt
            date = dt.today().isoformat()
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if log exists for today
            cursor.execute(
                "SELECT id FROM habit_logs WHERE user_id = ? AND habit_id = ? AND date = ?",
                (user_id, habit_id, date)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing log
                cursor.execute(
                    "UPDATE habit_logs SET completed = ? WHERE id = ?",
                    (completed, existing[0])
                )
            else:
                # Insert new log
                cursor.execute(
                    "INSERT INTO habit_logs (user_id, habit_id, date, completed) VALUES (?, ?, ?, ?)",
                    (user_id, habit_id, date, completed)
                )
            
            conn.commit()
            conn.close()
            logger.info(f"Habit {habit_id} logged as {'completed' if completed else 'not completed'} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error logging habit for user {user_id}: {e}")
            return False
    
    def get_habit_logs_for_date(self, user_id: int, date: str = None) -> List[Dict[str, Any]]:
        """Get all habit logs for a specific date"""
        if date is None:
            from datetime import date as dt
            date = dt.today().isoformat()
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT h.id, h.habit_name, hl.completed, hl.date
                   FROM habits h
                   LEFT JOIN habit_logs hl ON h.id = hl.habit_id AND hl.date = ? AND hl.user_id = ?
                   WHERE h.user_id = ?
                   ORDER BY h.habit_name""",
                (date, user_id, user_id)
            )
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'habit_id': row[0],
                    'habit_name': row[1],
                    'completed': bool(row[2]) if row[2] is not None else False,
                    'date': row[3] or date
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Error getting habit logs for user {user_id}: {e}")
            return []
    
    def get_habit_stats_weekly(self, user_id: int) -> Dict[str, Any]:
        """Get weekly habit completion statistics"""
        try:
            from datetime import date, timedelta
            
            # Get last 7 days
            today = date.today()
            week_start = today - timedelta(days=6)
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get all habits and their completion for the week
            cursor.execute(
                """SELECT h.habit_name, hl.date, hl.completed
                   FROM habits h
                   LEFT JOIN habit_logs hl ON h.id = hl.habit_id 
                       AND hl.date >= ? AND hl.date <= ? AND hl.user_id = ?
                   WHERE h.user_id = ?
                   ORDER BY h.habit_name, hl.date""",
                (week_start.isoformat(), today.isoformat(), user_id, user_id)
            )
            results = cursor.fetchall()
            conn.close()
            
            # Process results into habit completion percentages
            habit_stats = {}
            for row in results:
                habit_name = row[0]
                completed = bool(row[2]) if row[2] is not None else False
                
                if habit_name not in habit_stats:
                    habit_stats[habit_name] = {'completed': 0, 'total': 0}
                
                habit_stats[habit_name]['total'] += 1
                if completed:
                    habit_stats[habit_name]['completed'] += 1
            
            # Calculate percentages
            for habit in habit_stats:
                total = habit_stats[habit]['total']
                if total > 0:
                    habit_stats[habit]['percentage'] = (habit_stats[habit]['completed'] / total) * 100
                else:
                    habit_stats[habit]['percentage'] = 0
            
            return habit_stats
        except Exception as e:
            logger.error(f"Error getting weekly habit stats for user {user_id}: {e}")
            return {}
    
    def get_habit_streak(self, user_id: int) -> int:
        """Get current streak of days with all habits completed"""
        try:
            from datetime import date, timedelta
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get all habits for user
            cursor.execute("SELECT COUNT(*) FROM habits WHERE user_id = ?", (user_id,))
            total_habits = cursor.fetchone()[0]
            
            if total_habits == 0:
                return 0
            
            # Check each day going backwards from today
            current_date = date.today()
            streak = 0
            
            while True:
                date_str = current_date.isoformat()
                
                # Count completed habits for this date
                cursor.execute(
                    """SELECT COUNT(*) FROM habit_logs hl
                       JOIN habits h ON hl.habit_id = h.id
                       WHERE h.user_id = ? AND hl.date = ? AND hl.completed = 1""",
                    (user_id, date_str)
                )
                completed_today = cursor.fetchone()[0]
                
                # If all habits completed, increment streak
                if completed_today == total_habits:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break
            
            conn.close()
            return streak
        except Exception as e:
            logger.error(f"Error getting habit streak for user {user_id}: {e}")
            return 0
    
    def get_habit_overall_stats(self, user_id: int) -> Dict[str, Any]:
        """Get overall habit completion statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get total logs and completed logs
            cursor.execute(
                """SELECT COUNT(*) as total, 
                          SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed
                   FROM habit_logs hl
                   JOIN habits h ON hl.habit_id = h.id
                   WHERE h.user_id = ?""",
                (user_id,)
            )
            result = cursor.fetchone()
            conn.close()
            
            total_logs = result[0] or 0
            completed_logs = result[1] or 0
            
            if total_logs > 0:
                completion_percentage = (completed_logs / total_logs) * 100
            else:
                completion_percentage = 0
            
            return {
                'total_logs': total_logs,
                'completed_logs': completed_logs,
                'completion_percentage': completion_percentage
            }
        except Exception as e:
            logger.error(f"Error getting overall habit stats for user {user_id}: {e}")
            return {'total_logs': 0, 'completed_logs': 0, 'completion_percentage': 0}

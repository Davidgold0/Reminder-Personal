import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os
from contextlib import contextmanager

class Database:
    def __init__(self, db_path: str = '/data/reminder.db'):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_data_directory()
        self._create_tables()
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    action TEXT,
                    ai_processed BOOLEAN DEFAULT FALSE,
                    response TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Reminders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scheduled_time TEXT NOT NULL,
                    message TEXT NOT NULL,
                    sent BOOLEAN DEFAULT FALSE,
                    sent_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Statistics table for caching
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    total_messages INTEGER DEFAULT 0,
                    pill_confirmed INTEGER DEFAULT 0,
                    pill_missed INTEGER DEFAULT 0,
                    help_requests INTEGER DEFAULT 0,
                    unknown_commands INTEGER DEFAULT 0,
                    ai_processed INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            ''')
            
            conn.commit()
    
    def save_message(self, message_data: Dict) -> int:
        """
        Save a processed message to the database
        
        Args:
            message_data: Message data dictionary
            
        Returns:
            Message ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (sender, message, timestamp, action, ai_processed, response)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                message_data.get('sender', ''),
                message_data.get('message', ''),
                message_data.get('timestamp', ''),
                message_data.get('action', ''),
                message_data.get('ai_processed', False),
                message_data.get('response', '')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_message_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent message history
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM messages 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append(dict(row))
            
            return messages
    
    def get_statistics(self) -> Dict:
        """
        Get message processing statistics
        
        Returns:
            Dictionary with statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total counts
            cursor.execute('SELECT COUNT(*) as total FROM messages')
            total_messages = cursor.fetchone()['total']
            
            # Get action counts
            cursor.execute('''
                SELECT action, COUNT(*) as count 
                FROM messages 
                WHERE action IS NOT NULL 
                GROUP BY action
            ''')
            
            action_counts = {}
            for row in cursor.fetchall():
                action_counts[row['action']] = row['count']
            
            # Get AI processed count
            cursor.execute('SELECT COUNT(*) as count FROM messages WHERE ai_processed = 1')
            ai_processed = cursor.fetchone()['count']
            
            return {
                'total_messages': total_messages,
                'pill_confirmed': action_counts.get('pill_confirmed', 0),
                'pill_missed': action_counts.get('pill_missed', 0),
                'help_requests': action_counts.get('help_requested', 0),
                'unknown_commands': action_counts.get('unknown_command', 0),
                'ai_processed': ai_processed
            }
    
    def save_reminder(self, scheduled_time: str, message: str) -> int:
        """
        Save a scheduled reminder
        
        Args:
            scheduled_time: ISO format timestamp
            message: Reminder message
            
        Returns:
            Reminder ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reminders (scheduled_time, message)
                VALUES (?, ?)
            ''', (scheduled_time, message))
            conn.commit()
            return cursor.lastrowid
    
    def mark_reminder_sent(self, reminder_id: int):
        """
        Mark a reminder as sent
        
        Args:
            reminder_id: ID of the reminder to mark as sent
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE reminders 
                SET sent = 1, sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (reminder_id,))
            conn.commit()
    
    def get_pending_reminders(self) -> List[Dict]:
        """
        Get reminders that haven't been sent yet
        
        Returns:
            List of pending reminder dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM reminders 
                WHERE sent = 0 
                ORDER BY scheduled_time ASC
            ''')
            
            reminders = []
            for row in cursor.fetchall():
                reminders.append(dict(row))
            
            return reminders
    
    def cleanup_old_messages(self, days_to_keep: int = 90):
        """
        Clean up old messages to keep database size manageable
        
        Args:
            days_to_keep: Number of days to keep messages
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM messages 
                WHERE datetime(timestamp) < datetime('now', '-{} days')
            '''.format(days_to_keep))
            conn.commit()
    
    def get_database_size(self) -> int:
        """
        Get database file size in bytes
        
        Returns:
            Database file size
        """
        try:
            return os.path.getsize(self.db_path)
        except FileNotFoundError:
            return 0
    
    def backup_database(self, backup_path: str):
        """
        Create a backup of the database
        
        Args:
            backup_path: Path for the backup file
        """
        import shutil
        shutil.copy2(self.db_path, backup_path) 
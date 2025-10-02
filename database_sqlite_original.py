import sqlite3
import json
from datetime import datetime, timezone
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
                    is_missed_reminder BOOLEAN DEFAULT FALSE,
                    scheduled_date TEXT,
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
            
            # Customers table for managing recipient phone numbers
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT NOT NULL UNIQUE,
                    name TEXT,
                    reminder_time TEXT DEFAULT '20:00',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Daily reminders tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    reminder_date TEXT NOT NULL,
                    reminder_time TEXT NOT NULL,
                    message_sent TEXT NOT NULL,
                    confirmed BOOLEAN DEFAULT FALSE,
                    confirmation_message TEXT,
                    confirmation_time TEXT,
                    escalation_level INTEGER DEFAULT 0,
                    next_escalation_time TEXT,
                    escalation_messages_sent TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (id),
                    UNIQUE(customer_id, reminder_date)
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
    
    def get_last_reminder_date(self) -> Optional[str]:
        """
        Get the date of the last sent reminder
        
        Returns:
            Date string of last reminder or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT scheduled_date FROM reminders 
                WHERE sent = 1 
                ORDER BY sent_at DESC 
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            return result['scheduled_date'] if result else None
    
    def save_scheduled_reminder(self, scheduled_time: datetime, message: str = None):
        """
        Save a scheduled reminder for future reference
        
        Args:
            scheduled_time: When the reminder should be sent
            message: Optional message (will be generated if None)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reminders (scheduled_time, message, scheduled_date)
                VALUES (?, ?, ?)
            ''', (
                scheduled_time.isoformat(),
                message or "AI-generated reminder",
                scheduled_time.date().isoformat()
            ))
            conn.commit()
    
    def get_missed_reminders(self, days_back: int = 7) -> List[Dict]:
        """
        Get reminders that were missed in the last N days
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of missed reminder dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM reminders 
                WHERE sent = 0 
                AND scheduled_date >= date('now', '-{} days')
                ORDER BY scheduled_time DESC
            '''.format(days_back))
            
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
    
    # Customer management methods
    def add_customer(self, phone_number: str, name: str = None, reminder_time: str = '20:00') -> int:
        """
        Add a new customer to the database
        
        Args:
            phone_number: Phone number with country code (no +)
            name: Optional customer name
            reminder_time: Reminder time in HH:MM format (default: 20:00)
            
        Returns:
            Customer ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO customers (phone_number, name, reminder_time)
                VALUES (?, ?, ?)
            ''', (phone_number, name, reminder_time))
            conn.commit()
            return cursor.lastrowid
    
    def get_customers(self, active_only: bool = True) -> List[Dict]:
        """
        Get all customers
        
        Args:
            active_only: If True, only return active customers
            
        Returns:
            List of customer dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute('''
                    SELECT * FROM customers 
                    WHERE is_active = 1 
                    ORDER BY created_at DESC
                ''')
            else:
                cursor.execute('''
                    SELECT * FROM customers 
                    ORDER BY created_at DESC
                ''')
            
            customers = []
            for row in cursor.fetchall():
                customers.append(dict(row))
            
            return customers
    
    def get_customer_by_phone(self, phone_number: str) -> Optional[Dict]:
        """
        Get a customer by phone number
        
        Args:
            phone_number: Phone number to search for
            
        Returns:
            Customer dictionary or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM customers 
                WHERE phone_number = ?
            ''', (phone_number,))
            
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def update_customer(self, customer_id: int, name: str = None, is_active: bool = None, reminder_time: str = None) -> bool:
        """
        Update a customer's information
        
        Args:
            customer_id: ID of the customer to update
            name: New name (optional)
            is_active: New active status (optional)
            reminder_time: New reminder time in HH:MM format (optional)
            
        Returns:
            True if updated successfully, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build update query dynamically
            update_fields = []
            params = []
            
            if name is not None:
                update_fields.append('name = ?')
                params.append(name)
            
            if is_active is not None:
                update_fields.append('is_active = ?')
                params.append(is_active)
            
            if reminder_time is not None:
                update_fields.append('reminder_time = ?')
                params.append(reminder_time)
            
            if not update_fields:
                return False
            
            update_fields.append('updated_at = CURRENT_TIMESTAMP')
            params.append(customer_id)
            
            query = f'''
                UPDATE customers 
                SET {', '.join(update_fields)}
                WHERE id = ?
            '''
            
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_customer(self, customer_id: int) -> bool:
        """
        Delete a customer (soft delete by setting is_active to False)
        
        Args:
            customer_id: ID of the customer to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        return self.update_customer(customer_id, is_active=False)
    
    def get_active_phone_numbers(self) -> List[str]:
        """
        Get all active phone numbers for sending reminders
        
        Returns:
            List of active phone numbers
        """
        customers = self.get_customers(active_only=True)
        return [customer['phone_number'] for customer in customers]
    
    def get_customers_by_reminder_time(self, reminder_time: str) -> List[Dict]:
        """
        Get all active customers with a specific reminder time
        
        Args:
            reminder_time: Time in HH:MM format
            
        Returns:
            List of customer dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM customers 
                WHERE is_active = 1 AND reminder_time = ?
                ORDER BY created_at DESC
            ''', (reminder_time,))
            
            customers = []
            for row in cursor.fetchall():
                customers.append(dict(row))
            
            return customers
    
    def get_all_reminder_times(self) -> List[str]:
        """
        Get all unique reminder times from active customers
        
        Returns:
            List of unique reminder times
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT reminder_time FROM customers 
                WHERE is_active = 1 
                ORDER BY reminder_time
            ''')
            
            times = []
            for row in cursor.fetchall():
                times.append(row['reminder_time'])
            
            return times
    
    # Daily reminders tracking methods
    def create_daily_reminder(self, customer_id: int, reminder_date: str, reminder_time: str, message_sent: str) -> int:
        """
        Create a new daily reminder record
        
        Args:
            customer_id: ID of the customer
            reminder_date: Date in YYYY-MM-DD format
            reminder_time: Time in HH:MM format
            message_sent: The reminder message that was sent
            
        Returns:
            Daily reminder ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO daily_reminders (customer_id, reminder_date, reminder_time, message_sent)
                VALUES (?, ?, ?, ?)
            ''', (customer_id, reminder_date, reminder_time, message_sent))
            conn.commit()
            return cursor.lastrowid
    
    def get_daily_reminder(self, customer_id: int, reminder_date: str) -> Optional[Dict]:
        """
        Get a daily reminder record
        
        Args:
            customer_id: ID of the customer
            reminder_date: Date in YYYY-MM-DD format
            
        Returns:
            Daily reminder dictionary or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM daily_reminders 
                WHERE customer_id = ? AND reminder_date = ?
            ''', (customer_id, reminder_date))
            
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def update_daily_reminder_confirmation(self, customer_id: int, reminder_date: str, confirmed: bool, confirmation_message: str = None) -> bool:
        """
        Update the confirmation status of a daily reminder
        
        Args:
            customer_id: ID of the customer
            reminder_date: Date in YYYY-MM-DD format
            confirmed: Whether the reminder was confirmed
            confirmation_message: The message that confirmed it
            
        Returns:
            True if updated successfully, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE daily_reminders 
                SET confirmed = ?, confirmation_message = ?, confirmation_time = CURRENT_TIMESTAMP
                WHERE customer_id = ? AND reminder_date = ?
            ''', (confirmed, confirmation_message, customer_id, reminder_date))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_pending_confirmations(self, days_back: int = 7) -> List[Dict]:
        """
        Get daily reminders that haven't been confirmed yet
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of pending confirmation reminders
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT dr.*, c.name as customer_name, c.phone_number
                FROM daily_reminders dr
                JOIN customers c ON dr.customer_id = c.id
                WHERE dr.confirmed = 0 
                AND dr.reminder_date >= date('now', '-{} days')
                ORDER BY dr.reminder_date DESC, dr.reminder_time DESC
            '''.format(days_back))
            
            reminders = []
            for row in cursor.fetchall():
                reminders.append(dict(row))
            
            return reminders
    
    def get_confirmation_stats(self, days_back: int = 30) -> Dict:
        """
        Get confirmation statistics
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with confirmation statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total reminders
            cursor.execute('''
                SELECT COUNT(*) as total FROM daily_reminders 
                WHERE reminder_date >= date('now', '-{} days')
            '''.format(days_back))
            total = cursor.fetchone()['total']
            
            # Get confirmed reminders
            cursor.execute('''
                SELECT COUNT(*) as confirmed FROM daily_reminders 
                WHERE confirmed = 1 AND reminder_date >= date('now', '-{} days')
            '''.format(days_back))
            confirmed = cursor.fetchone()['confirmed']
            
            # Get pending reminders
            cursor.execute('''
                SELECT COUNT(*) as pending FROM daily_reminders 
                WHERE confirmed = 0 AND reminder_date >= date('now', '-{} days')
            '''.format(days_back))
            pending = cursor.fetchone()['pending']
            
            return {
                'total': total,
                'confirmed': confirmed,
                'pending': pending,
                'confirmation_rate': (confirmed / total * 100) if total > 0 else 0
            }
    
    # Escalation methods
    def get_reminders_needing_escalation(self) -> List[Dict]:
        """
        Get reminders that need escalation
        
        Returns:
            List of reminders that need escalation
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT dr.*, c.name as customer_name, c.phone_number
                FROM daily_reminders dr
                JOIN customers c ON dr.customer_id = c.id
                WHERE dr.confirmed = 0 
                AND dr.escalation_level < 4
                AND dr.next_escalation_time <= datetime('now')
                AND datetime(dr.created_at) >= datetime('now', '-2 hours')
                ORDER BY dr.next_escalation_time ASC
            ''')
            
            reminders = []
            for row in cursor.fetchall():
                reminders.append(dict(row))
            
            return reminders
    
    def update_escalation_level(self, reminder_id: int, escalation_level: int, escalation_message: str, next_escalation_time: str) -> bool:
        """
        Update escalation level and add message to sent list
        
        Args:
            reminder_id: ID of the reminder to update
            escalation_level: New escalation level
            escalation_message: Message that was sent
            next_escalation_time: When next escalation should be sent
            
        Returns:
            True if updated successfully, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current escalation messages
            cursor.execute('''
                SELECT escalation_messages_sent FROM daily_reminders WHERE id = ?
            ''', (reminder_id,))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            # Parse existing messages and add new one
            import json
            try:
                messages_sent = json.loads(result['escalation_messages_sent'])
            except (json.JSONDecodeError, TypeError):
                messages_sent = []
            
            messages_sent.append({
                'level': escalation_level,
                'message': escalation_message,
                'sent_at': datetime.now(timezone.utc).isoformat()
            })
            
            # Update escalation level and messages
            cursor.execute('''
                UPDATE daily_reminders 
                SET escalation_level = ?, 
                    next_escalation_time = ?,
                    escalation_messages_sent = ?
                WHERE id = ?
            ''', (escalation_level, next_escalation_time, json.dumps(messages_sent), reminder_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def stop_escalations_for_customer(self, customer_id: int, reminder_date: str) -> bool:
        """
        Stop escalations for a customer on a specific date (when they confirm)
        
        Args:
            customer_id: ID of the customer
            reminder_date: Date of the reminder
            
        Returns:
            True if updated successfully, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE daily_reminders 
                SET next_escalation_time = NULL
                WHERE customer_id = ? AND reminder_date = ?
            ''', (customer_id, reminder_date))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_escalation_stats(self, days_back: int = 30) -> Dict:
        """
        Get escalation statistics
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with escalation statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total escalations sent
            cursor.execute('''
                SELECT COUNT(*) as total_escalations FROM daily_reminders 
                WHERE escalation_level > 0 
                AND reminder_date >= date('now', '-{} days')
            '''.format(days_back))
            total_escalations = cursor.fetchone()['total_escalations']
            
            # Get escalations by level
            cursor.execute('''
                SELECT escalation_level, COUNT(*) as count 
                FROM daily_reminders 
                WHERE escalation_level > 0 
                AND reminder_date >= date('now', '-{} days')
                GROUP BY escalation_level
            '''.format(days_back))
            
            escalation_by_level = {}
            for row in cursor.fetchall():
                escalation_by_level[row['escalation_level']] = row['count']
            
            return {
                'total_escalations': total_escalations,
                'escalation_by_level': escalation_by_level
            } 
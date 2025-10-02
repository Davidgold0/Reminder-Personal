import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
import os
from contextlib import contextmanager
from config import Config
import urllib.parse

class Database:
    def __init__(self):
        """
        Initialize MySQL database connection for Railway deployment
        """
        try:
            self.connection_params = self._get_connection_params()
            print(f"🔗 Attempting database connection to {self.connection_params.get('host')}:{self.connection_params.get('port')}")
            self._create_tables()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            print(f"❌ Connection params: {self._redact_password(self.connection_params) if hasattr(self, 'connection_params') else 'Not set'}")
            raise e
    
    def _redact_password(self, params):
        """Return connection params with password redacted for logging"""
        redacted = params.copy()
        if 'password' in redacted:
            redacted['password'] = '***'
        return redacted
    
    def _get_connection_params(self):
        """Get MySQL connection parameters from Railway or individual config"""
        if Config.DATABASE_URL:
            # Parse DATABASE_URL (Railway format: mysql://user:password@host:port/database)
            url = urllib.parse.urlparse(Config.DATABASE_URL)
            return {
                'host': url.hostname,
                'port': url.port or 3306,
                'database': url.path[1:],  # Remove leading '/'
                'user': url.username,
                'password': url.password,
                'ssl_disabled': False,
                'autocommit': False
            }
        else:
            # Use individual config parameters
            return {
                'host': Config.MYSQL_HOST,
                'port': Config.MYSQL_PORT,
                'database': Config.MYSQL_DATABASE,
                'user': Config.MYSQL_USER,
                'password': Config.MYSQL_PASSWORD,
                'ssl_disabled': False,
                'autocommit': False
            }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = mysql.connector.connect(**self.connection_params)
            yield conn
        except Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn and conn.is_connected():
                conn.close()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sender VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    timestamp VARCHAR(255) NOT NULL,
                    action VARCHAR(255),
                    ai_processed TINYINT(1) DEFAULT 0,
                    response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Reminders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    scheduled_time VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    sent TINYINT(1) DEFAULT 0,
                    sent_at VARCHAR(255),
                    is_missed_reminder TINYINT(1) DEFAULT 0,
                    scheduled_date VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Statistics table for caching
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date VARCHAR(255) NOT NULL,
                    total_messages INT DEFAULT 0,
                    pill_confirmed INT DEFAULT 0,
                    pill_missed INT DEFAULT 0,
                    help_requests INT DEFAULT 0,
                    unknown_commands INT DEFAULT 0,
                    ai_processed INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_date (date)
                )
            ''')
            
            # Customers table for managing recipient phone numbers
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    phone_number VARCHAR(255) NOT NULL UNIQUE,
                    name VARCHAR(255),
                    reminder_time VARCHAR(255) DEFAULT '20:00',
                    is_active TINYINT(1) DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''')
            
            # Daily reminders tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_reminders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT NOT NULL,
                    reminder_date VARCHAR(255) NOT NULL,
                    reminder_time VARCHAR(255) NOT NULL,
                    message_sent TEXT NOT NULL,
                    confirmed TINYINT(1) DEFAULT 0,
                    confirmation_message TEXT,
                    confirmation_time VARCHAR(255),
                    escalation_level INT DEFAULT 0,
                    next_escalation_time VARCHAR(255),
                    escalation_messages_sent TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (id),
                    UNIQUE KEY unique_customer_date (customer_id, reminder_date)
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
                VALUES (%s, %s, %s, %s, %s, %s)
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
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT * FROM messages 
                ORDER BY timestamp DESC 
                LIMIT %s
            ''', (limit,))
            
            return cursor.fetchall()
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics
        
        Returns:
            Dictionary with various statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get total messages
            cursor.execute('SELECT COUNT(*) as total_messages FROM messages')
            total_messages = cursor.fetchone()['total_messages']
            
            # Get action counts
            cursor.execute('''
                SELECT action, COUNT(*) as count 
                FROM messages 
                WHERE action IS NOT NULL 
                GROUP BY action
            ''')
            action_counts = {row['action']: row['count'] for row in cursor.fetchall()}
            
            # Get AI processed count
            cursor.execute('SELECT COUNT(*) as ai_processed FROM messages WHERE ai_processed = 1')
            ai_processed = cursor.fetchone()['ai_processed']
            
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
                VALUES (%s, %s)
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
                SET sent = 1, sent_at = NOW()
                WHERE id = %s
            ''', (reminder_id,))
            conn.commit()
    
    def get_pending_reminders(self) -> List[Dict]:
        """
        Get reminders that haven't been sent yet
        
        Returns:
            List of pending reminder dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT * FROM reminders 
                WHERE sent = 0 
                ORDER BY scheduled_time ASC
            ''')
            
            return cursor.fetchall()
    
    def get_last_reminder_date(self) -> Optional[str]:
        """
        Get the date of the last sent reminder
        
        Returns:
            Date string of last reminder or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
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
        Save a scheduled reminder with date tracking
        
        Args:
            scheduled_time: datetime object for when to send
            message: Optional message, uses default if None
        """
        from config import Config
        
        message = message or Config.REMINDER_MESSAGE
        scheduled_date = scheduled_time.strftime('%Y-%m-%d')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reminders (scheduled_time, message, scheduled_date)
                VALUES (%s, %s, %s)
            ''', (
                scheduled_time.isoformat(),
                message,
                scheduled_date
            ))
            conn.commit()
    
    def get_missed_reminders(self, days_back: int = 7) -> List[Dict]:
        """
        Get reminders that were scheduled but never sent
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of missed reminder dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT * FROM reminders 
                WHERE sent = 0 
                AND scheduled_time < NOW() 
                AND scheduled_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY scheduled_time DESC
            ''', (days_back,))
            
            return cursor.fetchall()
    
    def cleanup_old_messages(self, days_to_keep: int = 90):
        """
        Remove old messages to keep database size manageable
        
        Args:
            days_to_keep: Number of days of messages to keep
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM messages 
                WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
            ''', (days_to_keep,))
            conn.commit()
    
    def get_database_size(self) -> int:
        """
        Get approximate database size in bytes
        
        Returns:
            Size in bytes
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(data_length + index_length) as size
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            ''')
            result = cursor.fetchone()
            return result[0] or 0
    
    def backup_database(self, backup_path: str):
        """
        Create a backup of the database
        Note: This is a placeholder - actual MySQL backup would require mysqldump
        
        Args:
            backup_path: Path where to save backup
        """
        # For MySQL, backup would typically use mysqldump command
        # This is a simplified version that exports data as JSON
        backup_data = {
            'messages': self.get_message_history(1000),
            'customers': self.get_customers(active_only=False),
            'statistics': self.get_statistics()
        }
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
    
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
                VALUES (%s, %s, %s)
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
            cursor = conn.cursor(dictionary=True)
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
            
            return cursor.fetchall()
    
    def get_customer_by_phone(self, phone_number: str) -> Optional[Dict]:
        """
        Get a customer by phone number
        
        Args:
            phone_number: Phone number to search for
            
        Returns:
            Customer dictionary or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT * FROM customers 
                WHERE phone_number = %s
            ''', (phone_number,))
            
            return cursor.fetchone()
    
    def update_customer(self, customer_id: int, name: str = None, is_active: bool = None, reminder_time: str = None) -> bool:
        """
        Update customer information
        
        Args:
            customer_id: ID of customer to update
            name: New name (optional)
            is_active: New active status (optional)
            reminder_time: New reminder time (optional)
            
        Returns:
            True if update successful
        """
        updates = []
        values = []
        
        if name is not None:
            updates.append("name = %s")
            values.append(name)
        
        if is_active is not None:
            updates.append("is_active = %s")
            values.append(is_active)
        
        if reminder_time is not None:
            updates.append("reminder_time = %s")
            values.append(reminder_time)
        
        if not updates:
            return False
        
        updates.append("updated_at = NOW()")
        values.append(customer_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = f"UPDATE customers SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, values)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def delete_customer(self, customer_id: int) -> bool:
        """
        Delete a customer (soft delete - mark as inactive)
        
        Args:
            customer_id: ID of customer to delete
            
        Returns:
            True if deletion successful
        """
        return self.update_customer(customer_id, is_active=False)
    
    def get_active_phone_numbers(self) -> List[str]:
        """
        Get list of all active customer phone numbers
        
        Returns:
            List of phone numbers
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT phone_number FROM customers 
                WHERE is_active = 1
            ''')
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_customers_by_reminder_time(self, reminder_time: str) -> List[Dict]:
        """
        Get customers who have reminders at a specific time
        
        Args:
            reminder_time: Time in HH:MM format
            
        Returns:
            List of customer dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT * FROM customers 
                WHERE is_active = 1 AND reminder_time = %s
                ORDER BY created_at DESC
            ''', (reminder_time,))
            
            return cursor.fetchall()
    
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
            
            return [row[0] for row in cursor.fetchall()]
    
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
                VALUES (%s, %s, %s, %s)
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
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT * FROM daily_reminders 
                WHERE customer_id = %s AND reminder_date = %s
            ''', (customer_id, reminder_date))
            
            return cursor.fetchone()
    
    def update_daily_reminder_confirmation(self, customer_id: int, reminder_date: str, confirmed: bool, confirmation_message: str = None) -> bool:
        """
        Update daily reminder confirmation status
        
        Args:
            customer_id: ID of the customer
            reminder_date: Date in YYYY-MM-DD format
            confirmed: Whether the reminder was confirmed
            confirmation_message: Optional confirmation message
            
        Returns:
            True if update successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE daily_reminders 
                SET confirmed = %s, confirmation_message = %s, confirmation_time = NOW()
                WHERE customer_id = %s AND reminder_date = %s
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
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT dr.*, c.name as customer_name, c.phone_number
                FROM daily_reminders dr
                JOIN customers c ON dr.customer_id = c.id
                WHERE dr.confirmed = 0 
                AND STR_TO_DATE(dr.reminder_date, '%Y-%m-%d') >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                ORDER BY dr.reminder_date DESC, dr.reminder_time DESC
            ''', (days_back,))
            
            return cursor.fetchall()
    
    def get_confirmation_stats(self, days_back: int = 30) -> Dict:
        """
        Get confirmation statistics
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with confirmation statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get total reminders
            cursor.execute('''
                SELECT COUNT(*) as total FROM daily_reminders 
                WHERE STR_TO_DATE(reminder_date, '%Y-%m-%d') >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ''', (days_back,))
            total = cursor.fetchone()['total']
            
            # Get confirmed reminders
            cursor.execute('''
                SELECT COUNT(*) as confirmed FROM daily_reminders 
                WHERE confirmed = 1 AND STR_TO_DATE(reminder_date, '%Y-%m-%d') >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ''', (days_back,))
            confirmed = cursor.fetchone()['confirmed']
            
            # Get pending reminders
            cursor.execute('''
                SELECT COUNT(*) as pending FROM daily_reminders 
                WHERE confirmed = 0 AND STR_TO_DATE(reminder_date, '%Y-%m-%d') >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ''', (days_back,))
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
        Get reminders that need escalation (unconfirmed past reminders)
        
        Returns:
            List of reminders needing escalation
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT dr.*, c.name as customer_name, c.phone_number
                FROM daily_reminders dr
                JOIN customers c ON dr.customer_id = c.id
                WHERE dr.confirmed = 0 
                AND STR_TO_DATE(dr.reminder_date, '%Y-%m-%d') < CURDATE()
                AND (dr.next_escalation_time IS NULL OR STR_TO_DATE(dr.next_escalation_time, '%Y-%m-%d %H:%i:%s') <= NOW())
                ORDER BY dr.reminder_date ASC
            ''')
            
            return cursor.fetchall()
    
    def update_escalation(self, reminder_id: int, escalation_level: int, next_escalation_time: str, escalation_message: str) -> bool:
        """
        Update escalation information for a reminder
        
        Args:
            reminder_id: ID of the daily reminder
            escalation_level: New escalation level
            next_escalation_time: When to send next escalation
            escalation_message: Message that was sent
            
        Returns:
            True if update successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current escalation messages
            cursor.execute('''
                SELECT escalation_messages_sent FROM daily_reminders WHERE id = %s
            ''', (reminder_id,))
            result = cursor.fetchone()
            
            if result:
                current_messages = json.loads(result[0] or '[]')
                current_messages.append({
                    'level': escalation_level,
                    'message': escalation_message,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
                cursor.execute('''
                    UPDATE daily_reminders 
                    SET escalation_level = %s, 
                        next_escalation_time = %s,
                        escalation_messages_sent = %s
                    WHERE id = %s
                ''', (escalation_level, next_escalation_time, json.dumps(current_messages), reminder_id))
                conn.commit()
                
                return cursor.rowcount > 0
            
            return False
    
    def get_escalation_stats(self, days_back: int = 30) -> Dict:
        """
        Get escalation statistics
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with escalation statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get total escalations sent
            cursor.execute('''
                SELECT COUNT(*) as total_escalations FROM daily_reminders 
                WHERE escalation_level > 0 
                AND STR_TO_DATE(reminder_date, '%Y-%m-%d') >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ''', (days_back,))
            total_escalations = cursor.fetchone()['total_escalations']
            
            # Get escalations by level
            cursor.execute('''
                SELECT escalation_level, COUNT(*) as count 
                FROM daily_reminders 
                WHERE escalation_level > 0 
                AND STR_TO_DATE(reminder_date, '%Y-%m-%d') >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY escalation_level
            ''', (days_back,))
            
            escalation_by_level = {}
            for row in cursor.fetchall():
                escalation_by_level[f"level_{row['escalation_level']}"] = row['count']
            
            return {
                'total_escalations': total_escalations,
                'by_level': escalation_by_level
            }
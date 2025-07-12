from flask import Blueprint, request, jsonify
from database import Database
from datetime import datetime

confirmation_routes = Blueprint('confirmation_routes', __name__)

# Global variables
db = None

def set_globals(database):
    """Set global variables for this route module"""
    global db
    db = database

@confirmation_routes.route('/api/confirmations/stats', methods=['GET'])
def get_confirmation_stats():
    """Get confirmation statistics"""
    try:
        days_back = request.args.get('days_back', 30, type=int)
        stats = db.get_confirmation_stats(days_back)
        
        return jsonify({
            'success': True,
            'stats': stats,
            'days_back': days_back
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@confirmation_routes.route('/api/confirmations/pending', methods=['GET'])
def get_pending_confirmations():
    """Get pending confirmations"""
    try:
        days_back = request.args.get('days_back', 7, type=int)
        pending = db.get_pending_confirmations(days_back)
        
        return jsonify({
            'success': True,
            'pending_confirmations': pending,
            'count': len(pending),
            'days_back': days_back
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@confirmation_routes.route('/api/confirmations/customer/<int:customer_id>', methods=['GET'])
def get_customer_confirmations(customer_id):
    """Get confirmation history for a specific customer"""
    try:
        days_back = request.args.get('days_back', 30, type=int)
        
        # Get customer info
        customer = None
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            result = cursor.fetchone()
            if result:
                customer = dict(result)
        
        if not customer:
            return jsonify({
                'success': False,
                'error': 'Customer not found'
            }), 404
        
        # Get confirmation history
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM daily_reminders 
                WHERE customer_id = ? 
                AND reminder_date >= date('now', '-{} days')
                ORDER BY reminder_date DESC
            '''.format(days_back), (customer_id,))
            
            confirmations = []
            for row in cursor.fetchall():
                confirmations.append(dict(row))
        
        return jsonify({
            'success': True,
            'customer': customer,
            'confirmations': confirmations,
            'count': len(confirmations),
            'days_back': days_back
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@confirmation_routes.route('/api/confirmations/date/<date>', methods=['GET'])
def get_confirmations_by_date(date):
    """Get all confirmations for a specific date"""
    try:
        # Validate date format (YYYY-MM-DD)
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT dr.*, c.name as customer_name, c.phone_number
                FROM daily_reminders dr
                JOIN customers c ON dr.customer_id = c.id
                WHERE dr.reminder_date = ?
                ORDER BY dr.reminder_time ASC
            ''', (date,))
            
            confirmations = []
            for row in cursor.fetchall():
                confirmations.append(dict(row))
        
        return jsonify({
            'success': True,
            'date': date,
            'confirmations': confirmations,
            'count': len(confirmations)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 
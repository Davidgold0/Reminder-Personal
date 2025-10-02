from flask import Blueprint, request, jsonify
from database import Database
import re

customer_routes = Blueprint('customer_routes', __name__)

# Global variables
db = None

def set_globals(database):
    """Set global variables for this route module"""
    global db
    db = database

def validate_phone_number(phone_number: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone_number: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Remove any spaces, dashes, or parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone_number)
    
    # Check if it starts with + and has 10-15 digits
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    
    # Should be 10-15 digits
    if not re.match(r'^\d{10,15}$', cleaned):
        return False
    
    return True

def validate_reminder_time(reminder_time: str) -> bool:
    """
    Validate reminder time format
    
    Args:
        reminder_time: Time in HH:MM format
        
    Returns:
        True if valid, False otherwise
    """
    # Check if it matches HH:MM format
    if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', reminder_time):
        return False
    
    return True

@customer_routes.route('/api/customers', methods=['GET'])
def get_customers():
    """Get all customers"""
    try:
        # Check if database is available
        if db is None:
            return jsonify({
                'success': False,
                'error': 'Database not initialized - check server configuration and database connection'
            }), 503
        
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        customers = db.get_customers(active_only=active_only)
        
        return jsonify({
            'success': True,
            'customers': customers,
            'count': len(customers)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customer_routes.route('/api/customers', methods=['POST'])
def add_customer():
    """Add a new customer"""
    try:
        # Check if database is available
        if db is None:
            return jsonify({
                'success': False,
                'error': 'Database not initialized - check server configuration and database connection'
            }), 503
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        phone_number = data.get('phone_number', '').strip()
        name = data.get('name', '').strip()
        reminder_time = data.get('reminder_time', '20:00').strip()
        
        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'Phone number is required'
            }), 400
        
        # Validate phone number
        if not validate_phone_number(phone_number):
            return jsonify({
                'success': False,
                'error': 'Invalid phone number format. Please use format: 1234567890 (with country code, no +)'
            }), 400
        
        # Validate reminder time
        if not validate_reminder_time(reminder_time):
            return jsonify({
                'success': False,
                'error': 'Invalid reminder time format. Please use HH:MM format (e.g., 20:00)'
            }), 400
        
        # Check if customer already exists
        existing_customer = db.get_customer_by_phone(phone_number)
        if existing_customer:
            return jsonify({
                'success': False,
                'error': 'Customer with this phone number already exists'
            }), 409
        
        # Add customer
        customer_id = db.add_customer(phone_number, name if name else None, reminder_time)
        
        # Get the added customer
        new_customer = db.get_customer_by_phone(phone_number)
        
        return jsonify({
            'success': True,
            'message': 'Customer added successfully',
            'customer': new_customer
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customer_routes.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update a customer"""
    try:
        # Check if database is available
        if db is None:
            return jsonify({
                'success': False,
                'error': 'Database not initialized - check server configuration and database connection'
            }), 503
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        name = data.get('name')
        is_active = data.get('is_active')
        reminder_time = data.get('reminder_time')
        
        # Validate reminder time if provided
        if reminder_time and not validate_reminder_time(reminder_time):
            return jsonify({
                'success': False,
                'error': 'Invalid reminder time format. Please use HH:MM format (e.g., 20:00)'
            }), 400
        
        # Update customer
        success = db.update_customer(customer_id, name=name, is_active=is_active, reminder_time=reminder_time)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Customer not found or no changes made'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Customer updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customer_routes.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete a customer (soft delete)"""
    try:
        # Check if database is available
        if db is None:
            return jsonify({
                'success': False,
                'error': 'Database not initialized - check server configuration and database connection'
            }), 503
        
        success = db.delete_customer(customer_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Customer not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Customer deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customer_routes.route('/api/customers/active-phones', methods=['GET'])
def get_active_phone_numbers():
    """Get all active phone numbers for sending reminders"""
    try:
        # Check if database is available
        if db is None:
            return jsonify({
                'success': False,
                'error': 'Database not initialized - check server configuration and database connection'
            }), 503
        
        phone_numbers = db.get_active_phone_numbers()
        
        return jsonify({
            'success': True,
            'phone_numbers': phone_numbers,
            'count': len(phone_numbers)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customer_routes.route('/api/customers/by-time/<reminder_time>', methods=['GET'])
def get_customers_by_time(reminder_time):
    """Get all active customers with a specific reminder time"""
    try:
        # Check if database is available
        if db is None:
            return jsonify({
                'success': False,
                'error': 'Database not initialized - check server configuration and database connection'
            }), 503
        
        # Validate time format
        if not validate_reminder_time(reminder_time):
            return jsonify({
                'success': False,
                'error': 'Invalid time format. Please use HH:MM format (e.g., 20:00)'
            }), 400
        
        customers = db.get_customers_by_reminder_time(reminder_time)
        
        return jsonify({
            'success': True,
            'customers': customers,
            'reminder_time': reminder_time,
            'count': len(customers)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customer_routes.route('/api/customers/reminder-times', methods=['GET'])
def get_all_reminder_times():
    """Get all unique reminder times from active customers"""
    try:
        # Check if database is available
        if db is None:
            return jsonify({
                'success': False,
                'error': 'Database not initialized - check server configuration and database connection'
            }), 503
        
        reminder_times = db.get_all_reminder_times()
        
        return jsonify({
            'success': True,
            'reminder_times': reminder_times,
            'count': len(reminder_times)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 
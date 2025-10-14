"""
Database models and functions for customer management and travel bookings
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
import json

DB_PATH = "../database/customers.db"

def init_database():
    """Initialize database tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            password_salt TEXT,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add password columns to existing customers table if they don't exist
    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN password_salt TEXT")
        cursor.execute("ALTER TABLE customers ADD COLUMN password_hash TEXT")
    except sqlite3.OperationalError:
        # Columns already exist
        pass
    
    # Travel bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            customer_email TEXT NOT NULL,
            service_type TEXT NOT NULL,
            destination TEXT,
            departure_date DATE NOT NULL,
            return_date DATE,
            num_travelers INTEGER DEFAULT 1,
            service_details TEXT,
            special_requests TEXT,
            total_amount REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)
    
    # Conversation history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_email TEXT NOT NULL,
            session_id TEXT NOT NULL,
            message_type TEXT NOT NULL,
            message_text TEXT NOT NULL,
            language TEXT DEFAULT 'en-US',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def get_or_create_customer(email: str, name: str = None) -> Dict:
    """Get existing customer or create new one (legacy function for backward compatibility)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if customer exists
    cursor.execute("SELECT * FROM customers WHERE email = ?", (email,))
    customer = cursor.fetchone()
    
    if customer:
        # Update last login
        cursor.execute("UPDATE customers SET last_login = ? WHERE email = ?", 
                      (datetime.now(), email))
        conn.commit()
        
        # Handle both old and new schema
        if len(customer) >= 6:  # New schema with password fields
            customer_data = {
                'id': customer[0],
                'email': customer[1],
                'name': customer[2],
                'created_at': customer[5],
                'last_login': customer[6]
            }
        else:  # Old schema without password fields
            customer_data = {
                'id': customer[0],
                'email': customer[1],
                'name': customer[2],
                'created_at': customer[3],
                'last_login': customer[4]
            }
    else:
        # Create new customer (without password for legacy compatibility)
        cursor.execute("""
            INSERT INTO customers (email, name, created_at, last_login)
            VALUES (?, ?, ?, ?)
        """, (email, name, datetime.now(), datetime.now()))
        conn.commit()
        
        customer_id = cursor.lastrowid
        customer_data = {
            'id': customer_id,
            'email': email,
            'name': name,
            'created_at': datetime.now(),
            'last_login': datetime.now()
        }
    
    conn.close()
    return customer_data

# Keep the old function name for backward compatibility
def get_or_create_guest(email: str, name: str = None) -> Dict:
    return get_or_create_customer(email, name)

def create_travel_booking(customer_email: str, service_type: str, destination: str, 
                         departure_date: str, return_date: str = None, num_travelers: int = 1, 
                         service_details: str = None, special_requests: str = None, total_amount: float = 0) -> Dict:
    """Create a new travel booking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get customer ID
    cursor.execute("SELECT id FROM customers WHERE email = ?", (customer_email,))
    customer = cursor.fetchone()
    
    if not customer:
        conn.close()
        return {"error": "Customer not found"}
    
    customer_id = customer[0]
    
    # Create travel booking
    cursor.execute("""
        INSERT INTO travel_bookings 
        (customer_id, customer_email, service_type, destination, departure_date, return_date,
         num_travelers, service_details, special_requests, total_amount, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'confirmed', ?)
    """, (customer_id, customer_email, service_type, destination, departure_date, return_date,
          num_travelers, service_details, special_requests, total_amount, datetime.now()))
    
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        'booking_id': booking_id,
        'customer_email': customer_email,
        'service_type': service_type,
        'destination': destination,
        'departure_date': departure_date,
        'return_date': return_date,
        'num_travelers': num_travelers,
        'total_amount': total_amount,
        'status': 'confirmed'
    }

# Keep the old function name for backward compatibility
def create_booking(guest_email: str, room_type: str, check_in: str, check_out: str, 
                  num_guests: int = 1, special_requests: str = None, total_amount: float = 0) -> Dict:
    """Legacy booking function - maps to travel booking"""
    # Parse service type from room_type field (format: "Service Type - Details")
    if ' - ' in room_type:
        service_type, service_details = room_type.split(' - ', 1)
    else:
        service_type = room_type
        service_details = None
    
    return create_travel_booking(
        customer_email=guest_email,
        service_type=service_type,
        destination="Various",  # Default destination
        departure_date=check_in,
        return_date=check_out if check_out != check_in else None,
        num_travelers=num_guests,
        service_details=service_details,
        special_requests=special_requests,
        total_amount=total_amount
    )

def get_customer_bookings(email: str) -> List[Dict]:
    """Get all travel bookings for a customer"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, service_type, destination, departure_date, return_date, num_travelers,
               service_details, total_amount, status, created_at
        FROM travel_bookings
        WHERE customer_email = ?
        ORDER BY created_at DESC
    """, (email,))
    
    bookings = []
    for row in cursor.fetchall():
        bookings.append({
            'booking_id': row[0],
            'service_type': row[1],
            'destination': row[2],
            'departure_date': row[3],
            'return_date': row[4],
            'num_travelers': row[5],
            'service_details': row[6],
            'total_amount': row[7],
            'status': row[8],
            'created_at': row[9]
        })
    
    conn.close()
    return bookings

# Keep the old function name for backward compatibility
def get_guest_bookings(email: str) -> List[Dict]:
    """Legacy function - maps to customer bookings"""
    bookings = get_customer_bookings(email)
    # Convert to old format for compatibility
    legacy_bookings = []
    for booking in bookings:
        legacy_bookings.append({
            'booking_id': booking['booking_id'],
            'room_type': f"{booking['service_type']} - {booking['service_details'] or 'Standard'}",
            'check_in': booking['departure_date'],
            'check_out': booking['return_date'] or booking['departure_date'],
            'num_guests': booking['num_travelers'],
            'total_amount': booking['total_amount'],
            'status': booking['status'],
            'created_at': booking['created_at']
        })
    return legacy_bookings

def save_conversation(customer_email: str, session_id: str, message_type: str, 
                     message_text: str, language: str = 'en-US'):
    """Save conversation message to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO conversations 
        (customer_email, session_id, message_type, message_text, language, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (customer_email, session_id, message_type, message_text, language, datetime.now()))
    
    conn.commit()
    conn.close()

# Keep the old function name for backward compatibility
def save_conversation_legacy(guest_email: str, session_id: str, message_type: str, 
                           message_text: str, language: str = 'en-US'):
    return save_conversation(guest_email, session_id, message_type, message_text, language)

def get_conversation_history(customer_email: str, limit: int = 50) -> List[Dict]:
    """Get conversation history for a customer - pairs user messages with AI responses"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT message_type, message_text, language, created_at
        FROM conversations
        WHERE customer_email = ?
        ORDER BY created_at ASC
    """, (customer_email,))
    
    all_messages = cursor.fetchall()
    conn.close()
    
    # Group messages into conversation pairs
    conversations = []
    i = 0
    while i < len(all_messages):
        msg = all_messages[i]
        message_type = msg[0]
        message_text = msg[1]
        created_at = msg[3]
        
        if message_type == 'user':
            # Look for the next AI response
            ai_response = "No response"
            duration = "N/A"
            
            if i + 1 < len(all_messages) and all_messages[i + 1][0] == 'assistant':
                ai_response = all_messages[i + 1][1]
                i += 1  # Skip the AI response in next iteration
            
            conversations.append({
                'user_message': message_text,
                'ai_response': ai_response,
                'created_at': created_at,
                'duration': duration
            })
        
        i += 1
    
    # Return most recent conversations first, limited
    conversations.reverse()
    return conversations[:limit]

# Keep the old function name for backward compatibility
def get_conversation_history_legacy(guest_email: str, limit: int = 50) -> List[Dict]:
    return get_conversation_history(guest_email, limit)

def cancel_booking(booking_id: int, customer_email: str) -> Dict:
    """Cancel a booking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verify booking belongs to customer
        cursor.execute("""
            SELECT tb.id, c.email, tb.status 
            FROM travel_bookings tb
            JOIN customers c ON tb.customer_id = c.id
            WHERE tb.id = ? AND c.email = ?
        """, (booking_id, customer_email))
        
        booking = cursor.fetchone()
        
        if not booking:
            conn.close()
            return {'success': False, 'message': 'Booking not found or access denied'}
        
        if booking[2] == 'cancelled':
            conn.close()
            return {'success': False, 'message': 'Booking is already cancelled'}
        
        # Update booking status to cancelled
        cursor.execute("""
            UPDATE travel_bookings 
            SET status = 'cancelled' 
            WHERE id = ?
        """, (booking_id,))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True, 
            'message': 'Booking cancelled successfully',
            'booking_id': booking_id
        }
    
    except Exception as e:
        conn.close()
        return {'success': False, 'message': str(e)}

def reschedule_booking(booking_id: int, customer_email: str, 
                      new_departure_date: str = None, new_return_date: str = None) -> Dict:
    """Reschedule a booking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verify booking belongs to customer
        cursor.execute("""
            SELECT tb.id, c.email, tb.status 
            FROM travel_bookings tb
            JOIN customers c ON tb.customer_id = c.id
            WHERE tb.id = ? AND c.email = ?
        """, (booking_id, customer_email))
        
        booking = cursor.fetchone()
        
        if not booking:
            conn.close()
            return {'success': False, 'message': 'Booking not found or access denied'}
        
        if booking[2] == 'cancelled':
            conn.close()
            return {'success': False, 'message': 'Cannot reschedule a cancelled booking'}
        
        # Update booking dates
        updates = []
        params = []
        
        if new_departure_date:
            updates.append("departure_date = ?")
            params.append(new_departure_date)
        
        if new_return_date:
            updates.append("return_date = ?")
            params.append(new_return_date)
        
        if not updates:
            conn.close()
            return {'success': False, 'message': 'No new dates provided'}
        
        # Add booking_id to params
        params.append(booking_id)
        
        query = f"UPDATE travel_bookings SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        
        conn.commit()
        conn.close()
        
        return {
            'success': True, 
            'message': 'Booking rescheduled successfully',
            'booking_id': booking_id,
            'new_departure_date': new_departure_date,
            'new_return_date': new_return_date
        }
    
    except Exception as e:
        conn.close()
        return {'success': False, 'message': str(e)}

# Initialize database on import
init_database()


# 📊 Database Module

Central database storage for AI Travel Agent

## 📁 Structure

```
database/
├── __init__.py          # Module exports
├── database.py          # Database operations
├── customers.db         # SQLite database file
└── README.md           # This file
```

## 🗄️ Database Tables

### 1. customers
Stores customer information and authentication
```sql
- id (PRIMARY KEY)
- email (UNIQUE)
- name
- password_salt
- password_hash
- created_at
- last_login
```

### 2. travel_bookings
Stores travel bookings (flights, hotels, packages)
```sql
- id (PRIMARY KEY)
- customer_email (FOREIGN KEY)
- service_type
- destination
- departure_date
- return_date
- num_travelers
- service_details
- special_requests
- total_amount
- status
- created_at
```

### 3. conversations
Stores chat history
```sql
- id (PRIMARY KEY)
- customer_email (FOREIGN KEY)
- session_id
- role (user/assistant)
- message_text
- language_code
- created_at
```

## 🔧 Available Functions

### Customer Management
```python
from database import get_or_create_customer

customer = get_or_create_customer(email, name)
```

### Booking Management
```python
from database import (
    create_travel_booking,
    get_customer_bookings,
    cancel_booking,
    reschedule_booking
)

# Create booking
booking = create_travel_booking(
    customer_email="user@example.com",
    service_type="Flight",
    destination="Riyadh",
    departure_date="2025-01-15",
    return_date="2025-01-22",
    num_travelers=2,
    service_details="Economy",
    total_amount=50000
)

# Get bookings
bookings = get_customer_bookings(email)

# Cancel booking
result = cancel_booking(booking_id, email)

# Reschedule booking
result = reschedule_booking(
    booking_id, 
    email, 
    new_departure="2025-02-01",
    new_return="2025-02-08"
)
```

### Conversation Management
```python
from database import (
    save_conversation,
    get_conversation_history
)

# Save conversation
save_conversation(
    customer_email="user@example.com",
    session_id="session_123",
    role="user",
    message_text="Hello Alex",
    language_code="en-US"
)

# Get history
history = get_conversation_history(email)
```

## 📦 Database Initialization

Database tables are automatically created on first use:

```python
from database import init_database

init_database()  # Creates all tables if they don't exist
```

## 🔒 Security

- **Password Hashing**: PBKDF2 with salt
- **SQL Injection Protection**: Parameterized queries
- **Input Validation**: All inputs validated
- **Database Backup**: Regular backups recommended

## 📊 Database Size

Current size can be checked:
```bash
ls -lh customers.db
```

## 🔄 Migration

If schema changes are needed:
1. Create migration script
2. Backup database
3. Apply schema changes
4. Test thoroughly

## 🧪 Testing

Test database operations:
```python
from database import init_database, get_or_create_customer

# Initialize
init_database()

# Test customer creation
customer = get_or_create_customer("test@example.com", "Test User")
print(f"Customer created: {customer}")
```

## 📝 Notes

- Database file: `customers.db`
- Format: SQLite 3
- Encoding: UTF-8
- Location: `/voice/database/`

## 🔧 Maintenance

### Backup Database
```bash
cp customers.db customers_backup_$(date +%Y%m%d).db
```

### View Database
```bash
sqlite3 customers.db
.tables
.schema customers
SELECT * FROM customers LIMIT 5;
```

### Database Size Optimization
```bash
sqlite3 customers.db "VACUUM;"
```

---

**Last Updated**: October 10, 2025  
**Version**: 2.0


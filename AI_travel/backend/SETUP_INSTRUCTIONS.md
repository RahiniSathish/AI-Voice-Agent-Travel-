# Attar Travel - Complete Backend Setup

## 🚀 Quick Start

### 1. Run the Complete Backend
```bash
cd backend
python complete_backend.py
```

### 2. Setup Email (Optional)
Create a `.env` file in the backend directory with your email settings:

```env
# Gmail SMTP Settings (Recommended)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
SMTP_FROM_EMAIL=your_email@gmail.com
```

### 3. Gmail App Password Setup
1. Go to Google Account settings
2. Enable 2-Factor Authentication
3. Generate App Password for "Mail"
4. Use the 16-character app password in .env file

## 📁 File Structure

### Essential Files:
- `complete_backend.py` - **Main backend server with all features**
- `.env` - Email configuration (create this)
- `SETUP_INSTRUCTIONS.md` - This file

### Features Included:
- ✅ User Registration
- ✅ User Login  
- ✅ Password Reset (with email)
- ✅ Travel Booking
- ✅ Email Notifications
- ✅ Password Hashing & Security
- ✅ CORS Support for Frontend

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/register` | POST | Register new user |
| `/login` | POST | User login |
| `/forgot_password` | POST | Send reset email |
| `/reset_password` | POST | Reset password with token |
| `/book_travel` | POST | Book travel + send confirmation |
| `/check_customer/{email}` | GET | Check if user exists |

## 🎯 Testing

### Test Registration:
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123", "full_name": "Test User"}'
```

### Test Login:
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123"}'
```

### Test Password Reset:
```bash
curl -X POST "http://localhost:8000/forgot_password" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## 📧 Email Features

- **Password Reset Emails**: Professional Attar Travel branded emails
- **Booking Confirmations**: Detailed booking information with next steps
- **Security**: Secure token-based password reset system
- **Fallback**: Works without SMTP (logs reset tokens for manual use)

## 🔒 Security Features

- **Password Hashing**: PBKDF2 with random salt
- **Reset Tokens**: Cryptographically secure, time-limited tokens
- **Input Validation**: All inputs validated and sanitized
- **Error Handling**: Comprehensive error handling and logging

## 🚀 Production Ready

This backend includes:
- Professional email templates
- Comprehensive error handling
- Security best practices
- CORS support for web frontend
- Detailed logging
- Modular, maintainable code

**Ready to use with your Streamlit frontend on port 8506!**

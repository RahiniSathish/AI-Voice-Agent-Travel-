"""
Utility Functions for AI Travel Agent
"""

import hashlib
import secrets
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SERVICE_PRICES, USD_TO_INR_RATE

logger = logging.getLogger(__name__)

# Password hashing functions
def hash_password(password: str) -> tuple:
    """Hash a password with a random salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt, password_hash.hex()

def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """Verify a password against its stored hash"""
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return password_hash.hex() == stored_hash

# Flight class options
def get_flight_class_options():
    """Get flight class options with pricing in both USD and INR"""
    flight_classes = SERVICE_PRICES['Flight']
    options = []
    
    for class_name, usd_price in flight_classes.items():
        inr_price = usd_price * USD_TO_INR_RATE
        options.append({
            'class': class_name,
            'usd_price': usd_price,
            'inr_price': round(inr_price, 2),
            'description': get_class_description(class_name)
        })
    
    return options

def get_class_description(class_name):
    """Get description for each flight class"""
    descriptions = {
        'Economy': 'Standard seating with meals and entertainment',
        'Business': 'Premium seating with extra legroom, priority boarding, and enhanced meals',
        'First': 'Luxury seating with full flat beds, premium dining, and exclusive lounge access'
    }
    return descriptions.get(class_name, 'Standard service')

# Email notification
def send_booking_confirmation_email(customer_email, booking_data):
    """Send booking confirmation email to customer"""
    try:
        # Get SMTP settings from environment
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT", "587")
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("SMTP_FROM_EMAIL", smtp_username)
        
        subject = "✈️ Travel Booking Confirmation - Attar Travel"
        
        # HTML Email body with Attar Travel branding
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 2rem; font-weight: bold;">✈️ ATTAR TRAVEL</h1>
                <p style="color: white; margin: 10px 0; font-size: 1.1rem;">عطار للسياحة</p>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0; font-size: 1rem;">Travel Booking Confirmation</p>
            </div>
            
            <div style="padding: 30px; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #1e40af; margin-top: 0;">Dear Valued Customer,</h2>
                <p style="font-size: 1.1rem;">Your travel booking with <strong>Attar Travel</strong> has been <strong style="color: #059669;">CONFIRMED</strong>!</p>
                
                <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 25px; border-radius: 15px; margin: 25px 0; border-left: 5px solid #1e40af;">
                    <h3 style="color: #1e40af; margin-top: 0; font-size: 1.3rem;">📋 Booking Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #374151;">Booking ID:</td>
                            <td style="padding: 8px 0; color: #1e40af; font-weight: bold;">#{booking_data['booking_id']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #374151;">Service Type:</td>
                            <td style="padding: 8px 0;">{booking_data.get('service_type', 'Travel Service')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #374151;">Destination:</td>
                            <td style="padding: 8px 0;">{booking_data.get('destination', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #374151;">Departure Date:</td>
                            <td style="padding: 8px 0;">{booking_data.get('departure_date', booking_data.get('check_in', 'N/A'))}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #374151;">Return Date:</td>
                            <td style="padding: 8px 0;">{booking_data.get('return_date', booking_data.get('check_out', 'N/A'))}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #374151;">Number of Travelers:</td>
                            <td style="padding: 8px 0;">{booking_data.get('num_travelers', booking_data.get('num_guests', 'N/A'))}</td>
                        </tr>
                        <tr style="border-top: 2px solid #e2e8f0;">
                            <td style="padding: 12px 0; font-weight: bold; color: #374151; font-size: 1.1rem;">Total Amount:</td>
                            <td style="padding: 12px 0; color: #1e40af; font-size: 1.3rem; font-weight: bold;">₹{booking_data['total_amount']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #374151;">Status:</td>
                            <td style="padding: 8px 0;"><span style="color: #059669; font-weight: bold; text-transform: uppercase;">{booking_data['status'].upper()}</span></td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: #f0f9ff; padding: 20px; border-radius: 10px; margin: 25px 0; border: 1px solid #0ea5e9;">
                    <h4 style="color: #0c4a6e; margin-top: 0;">📞 Next Steps:</h4>
                    <ul style="color: #0c4a6e; margin: 0; padding-left: 20px;">
                        <li>Payment details will be sent separately</li>
                        <li>Travel documents will be provided 24-48 hours before departure</li>
                        <li>Contact us for any special requests or modifications</li>
                    </ul>
                </div>
                
                <p style="font-size: 1.1rem; color: #374151;">We look forward to making your travel dreams come true with <strong>Attar Travel</strong>!</p>
                <p style="color: #6b7280;">If you have any questions, please don't hesitate to contact our customer support team.</p>
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e2e8f0; text-align: center;">
                    <p style="margin: 0; color: #1e40af; font-weight: bold;">Happy Travels! ✈️</p>
                    <p style="margin: 5px 0 0 0; color: #6b7280;">Alex & Attar Travel Team</p>
                    <p style="margin: 10px 0 0 0; font-size: 0.9rem; color: #9ca3af;">Saudi Arabia Airlines & Travel Specialist</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # If SMTP is configured, send email
        if smtp_server and smtp_username and smtp_password:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = from_email
                msg['To'] = customer_email
                
                msg.attach(MIMEText(html_body, 'html'))
                
                with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
                
                logger.info(f"📧 Travel booking confirmation email SENT to {customer_email}")
                return True
                
            except Exception as email_err:
                logger.warning(f"⚠️ Email sending failed: {email_err}")
                logger.info(f"📧 Booking confirmation prepared (email not sent)")
                return False
        else:
            logger.info(f"📧 Travel booking confirmation prepared for {customer_email}")
            logger.info(f"   Booking ID: #{booking_data['booking_id']}")
            logger.info(f"   Service: {booking_data.get('service_type', 'Travel Service')}")
            logger.info(f"   Total: ₹{booking_data['total_amount']}")
            logger.info(f"   ⚠️ Email NOT sent - Configure SMTP in .env to enable")
            return False
        
    except Exception as e:
        logger.warning(f"⚠️ Email notification failed: {e}")
        return False


def send_password_reset_email(customer_email, reset_token):
    """Send password reset email to customer"""
    try:
        # Get SMTP settings from environment
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT", "587")
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("SMTP_FROM_EMAIL", smtp_username)
        
        subject = "🔐 Password Reset Request - Attar Travel"
        
        # Create reset link (you can customize this URL)
        reset_link = f"http://localhost:8506/reset-password?token={reset_token}&email={customer_email}"
        
        # HTML Email body with Attar Travel branding
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 2rem; font-weight: bold;">✈️ ATTAR TRAVEL</h1>
                <p style="color: white; margin: 10px 0; font-size: 1.1rem;">عطار للسياحة</p>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0; font-size: 1rem;">Password Reset Request</p>
            </div>
            
            <div style="padding: 30px; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #1e40af; margin-top: 0;">Password Reset Request</h2>
                <p style="font-size: 1.1rem;">We received a request to reset your password for your Attar Travel account.</p>
                
                <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 25px; border-radius: 15px; margin: 25px 0; border-left: 5px solid #1e40af;">
                    <h3 style="color: #1e40af; margin-top: 0; font-size: 1.3rem;">🔐 Reset Your Password</h3>
                    <p style="margin: 15px 0;">Click the button below to reset your password:</p>
                    <div style="text-align: center; margin: 25px 0;">
                        <a href="{reset_link}" style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 1.1rem; display: inline-block;">Reset Password</a>
                    </div>
                    <p style="font-size: 0.9rem; color: #6b7280; margin: 15px 0;">Or copy and paste this link in your browser:</p>
                    <p style="font-size: 0.9rem; color: #1e40af; word-break: break-all; background: #f1f5f9; padding: 10px; border-radius: 5px;">{reset_link}</p>
                </div>
                
                <div style="background: #fef3c7; padding: 20px; border-radius: 10px; margin: 25px 0; border: 1px solid #f59e0b;">
                    <h4 style="color: #92400e; margin-top: 0;">⚠️ Important Security Information:</h4>
                    <ul style="color: #92400e; margin: 0; padding-left: 20px;">
                        <li>This link will expire in 24 hours for security reasons</li>
                        <li>If you didn't request this reset, please ignore this email</li>
                        <li>Your password will remain unchanged until you click the link</li>
                        <li>For security, never share this link with anyone</li>
                    </ul>
                </div>
                
                <p style="font-size: 1.1rem; color: #374151;">If you have any questions or need assistance, please contact our customer support team.</p>
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e2e8f0; text-align: center;">
                    <p style="margin: 0; color: #1e40af; font-weight: bold;">Secure Travels! ✈️</p>
                    <p style="margin: 5px 0 0 0; color: #6b7280;">Alex & Attar Travel Team</p>
                    <p style="margin: 10px 0 0 0; font-size: 0.9rem; color: #9ca3af;">Saudi Arabia Airlines & Travel Specialist</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # If SMTP is configured, send email
        if smtp_server and smtp_username and smtp_password:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = from_email
                msg['To'] = customer_email
                
                msg.attach(MIMEText(html_body, 'html'))
                
                with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
                
                logger.info(f"📧 Password reset email SENT to {customer_email}")
                return True
                
            except Exception as email_err:
                logger.warning(f"⚠️ Password reset email sending failed: {email_err}")
                logger.info(f"📧 Password reset email prepared (email not sent)")
                return False
        else:
            logger.info(f"📧 Password reset email prepared for {customer_email}")
            logger.info(f"   Reset Token: {reset_token}")
            logger.info(f"   Reset Link: {reset_link}")
            logger.info(f"   ⚠️ Email NOT sent - Configure SMTP in .env to enable")
            return False
        
    except Exception as e:
        logger.warning(f"⚠️ Password reset email notification failed: {e}")
        return False


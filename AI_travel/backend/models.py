"""
Pydantic Models for API Requests and Responses
"""

from pydantic import BaseModel, EmailStr
from typing import Optional

class VoiceRequest(BaseModel):
    text: str
    session_id: str = None
    customer_email: str = None
    detected_language: str = 'en'

class CustomerLogin(BaseModel):
    email: EmailStr
    password: str
    name: str = None

class CustomerRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class TravelBookingRequest(BaseModel):
    customer_email: EmailStr
    service_type: str  # Flight, Hotel, Package
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    num_travelers: int = 1
    service_details: Optional[str] = None  # Class, room type, package type
    special_requests: Optional[str] = None


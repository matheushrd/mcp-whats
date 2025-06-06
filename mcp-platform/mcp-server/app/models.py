from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class BusinessType(str, Enum):
    BARBERSHOP = "barbershop"
    SALON = "salon"
    CLINIC = "clinic"
    SPA = "spa"
    SHOP = "shop" 
    OTHER = "other"

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class MessageIntent(str, Enum):
    SCHEDULE = "schedule"
    CHECK_AVAILABILITY = "check_availability"
    CANCEL = "cancel"
    RESCHEDULE = "reschedule"
    LIST_APPOINTMENTS = "list_appointments"
    UNKNOWN = "unknown"

# Client Models
class ClientEnvironments(BaseModel): 
    development: bool = True
    staging: bool = False
    production: bool = False

class ClientResources(BaseModel):
    limits: Dict[str, str] = Field(default_factory=lambda: {"cpu": "500m", "memory": "512Mi"})
    requests: Dict[str, str] = Field(default_factory=lambda: {"cpu": "250m", "memory": "256Mi"})

class ClientCreate(BaseModel): 
    client_name: str = Field(..., pattern="^[a-z0-9-]+$") # MUDANÇA: regex para pattern
    business_name: str
    business_type: BusinessType
    environments: ClientEnvironments 
    resources: Optional[ClientResources] = None
    
    @validator('client_name')
    def validate_client_name(cls, v):
        if len(v) < 3:
            raise ValueError('Client name must be at least 3 characters long')
        return v

class ClientCredentials(BaseModel): 
    GOOGLE_CALENDAR_ID: str
    GOOGLE_PROJECT_ID: str
    GOOGLE_CLIENT_EMAIL: str
    GOOGLE_PRIVATE_KEY: str
    GEMINI_API_KEY: str
    WHATSAPP_API_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = "mcp_webhook_verify_token"
    DATABASE_USER: str
    DATABASE_PASSWORD: str

# Appointment Models
class AppointmentBase(BaseModel):
    customer_name: str
    customer_phone: str
    service_type: str
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    start_time: datetime
    end_time: datetime
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[AppointmentStatus] = None

class AppointmentResponse(AppointmentBase):
    id: str 
    start_time: datetime 
    end_time: datetime
    status: AppointmentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

class AppointmentListResponse(BaseModel):
    appointments: List[AppointmentResponse]
    total: int
    page: int = 1
    page_size: int = 20

# Message Models
class MessageBase(BaseModel):
    user_id: str
    message_content: str
    message_type: str = "text"

class MessageCreate(MessageBase):
    client_name: str

class MessageResponse(MessageBase):
    id: int 
    response_content: Optional[str] = None
    intent: MessageIntent
    created_at: datetime

class WhatsAppMessage(BaseModel): 
    message: str
    user_id: str
    send_whatsapp: bool = False
    whatsapp_number: Optional[str] = None

class WhatsAppWebhookData(BaseModel): 
    entry: List[Dict]

# Chat Models
class ChatRequest(BaseModel): 
    message: str
    user_id: str
    session_id: Optional[str] = None 
    send_whatsapp: Optional[bool] = False
    whatsapp_number: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: Optional[str] = None 
    intent: Optional[MessageIntent] = None 
    suggested_actions: Optional[List[str]] = None
    processed: Optional[bool] = True


# Health Check Models
class HealthStatus(BaseModel):
    status: str
    services: Dict[str, str]
    timestamp: datetime = Field(default_factory=datetime.now)

# User Models (for web interface)
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool 
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

# --- NOVOS MODELOS PARA ONBOARDING API ---
class ClientOnboardUiEnvironments(BaseModel): 
    development: bool = True
    staging: bool = False
    production: bool = False

class ClientOnboardUiCredentials(BaseModel): 
    GOOGLE_CALENDAR_ID: str
    GOOGLE_PROJECT_ID: str
    GOOGLE_CLIENT_EMAIL: str
    GOOGLE_PRIVATE_KEY: str 
    GEMINI_API_KEY: str
    WHATSAPP_API_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str

class ClientOnboardData(BaseModel):
    client_name: str = Field(..., min_length=3, pattern="^[a-z0-9-]+$") # MUDANÇA: regex para pattern
    business_name: str
    business_type: BusinessType 
    environments: ClientOnboardUiEnvironments 
    credentials: ClientOnboardUiCredentials 
    # resources: Optional[ClientResources] = None

class OnboardResponse(BaseModel):
    message: str
    client_name: str

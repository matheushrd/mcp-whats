from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Pydantic models
class AppointmentCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    customer_name: str
    customer_phone: str
    service_type: str
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: str
    start: str
    end: str
    customer_name: str
    service_type: str
    status: str = "confirmed"

class AvailableSlot(BaseModel):
    start: str
    end: str
    available: bool = True

@router.get("/available", response_model=List[AvailableSlot])
async def get_available_slots(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    duration: int = Query(30, description="Duration in minutes"),
    credentials = Depends(security)
):
    """Get available appointment slots for a specific date"""
    try:
        from app.main import app
        
        # Parse date
        appointment_date = datetime.strptime(date, "%Y-%m-%d")
        
        # Get available slots from calendar service
        available_slots = await app.state.calendar_service.get_available_slots(
            appointment_date, 
            duration
        )
        
        return [
            AvailableSlot(start=slot['start'], end=slot['end'])
            for slot in available_slots
        ]
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error getting available slots: {e}")
        raise HTTPException(status_code=500, detail="Error fetching available slots")

@router.post("/create", response_model=AppointmentResponse)
async def create_appointment(
    appointment: AppointmentCreate,
    credentials = Depends(security)
):
    """Create a new appointment"""
    try:
        from app.main import app
        
        # Create appointment in Google Calendar
        result = await app.state.calendar_service.create_appointment(
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            customer_name=appointment.customer_name,
            customer_phone=appointment.customer_phone,
            service_type=appointment.service_type,
            notes=appointment.notes
        )
        
        # Send confirmation message via WhatsApp
        confirmation_message = await app.state.gemini_service.generate_confirmation_message(
            appointment_details={
                'start': result['start'],
                'service': appointment.service_type,
                'customer_name': appointment.customer_name
            },
            client_name=app.state.calendar_service.calendar_id.split('@')[0]
        )
        
        await app.state.whatsapp_service.send_message(
            to=appointment.customer_phone,
            message=confirmation_message
        )
        
        return AppointmentResponse(
            id=result['id'],
            start=result['start'],
            end=result['end'],
            customer_name=appointment.customer_name,
            service_type=appointment.service_type
        )
        
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(status_code=500, detail="Error creating appointment")

@router.get("/list")
async def list_appointments(
    phone: Optional[str] = Query(None, description="Filter by phone number"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    credentials = Depends(security)
):
    """List appointments with optional filters"""
    try:
        from app.main import app
        
        if phone:
            # Get appointments by phone number
            appointments = await app.state.calendar_service.get_appointment_by_phone(phone)
            return {"appointments": appointments}
        
        # For now, return empty list if no phone filter
        # In production, you'd implement date filtering
        return {"appointments": []}
        
    except Exception as e:
        logger.error(f"Error listing appointments: {e}")
        raise HTTPException(status_code=500, detail="Error fetching appointments")

@router.patch("/{appointment_id}")
async def update_appointment(
    appointment_id: str,
    update: AppointmentUpdate,
    credentials = Depends(security)
):
    """Update an existing appointment"""
    try:
        from app.main import app
        
        result = await app.state.calendar_service.update_appointment(
            event_id=appointment_id,
            start_time=update.start_time,
            end_time=update.end_time,
            notes=update.notes
        )
        
        return {"message": "Appointment updated successfully", "appointment": result}
        
    except Exception as e:
        logger.error(f"Error updating appointment: {e}")
        raise HTTPException(status_code=500, detail="Error updating appointment")

@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: str,
    credentials = Depends(security)
):
    """Cancel an appointment"""
    try:
        from app.main import app
        
        success = await app.state.calendar_service.cancel_appointment(appointment_id)
        
        if success:
            return {"message": "Appointment cancelled successfully"}
        else:
            raise HTTPException(status_code=404, detail="Appointment not found")
            
    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        raise HTTPException(status_code=500, detail="Error cancelling appointment")
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self):
        self.calendar_id = settings.GOOGLE_CALENDAR_ID
        self.timezone = pytz.timezone('America/Sao_Paulo')
        self.service = self._initialize_service()
        
    def _initialize_service(self):
        """Initialize Google Calendar API service"""
        try:
            # Use service account credentials from environment
            credentials = service_account.Credentials.from_service_account_info(
                {
                    "type": "service_account",
                    "project_id": settings.GOOGLE_PROJECT_ID,
                    "private_key": settings.GOOGLE_PRIVATE_KEY.replace('\\n', '\n'),
                    "client_email": settings.GOOGLE_CLIENT_EMAIL,
                    "token_uri": "https://oauth2.googleapis.com/token"
                },
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            service = build('calendar', 'v3', credentials=credentials)
            logger.info("Google Calendar service initialized successfully")
            return service
            
        except Exception as e:
            logger.error(f"Failed to initialize Calendar service: {e}")
            raise
    
    async def get_available_slots(
        self, 
        date: datetime, 
        duration_minutes: int = 30
    ) -> List[Dict[str, str]]:
        """Get available time slots for a specific date"""
        try:
            # Set time range for the day
            start_time = date.replace(hour=8, minute=0, second=0, microsecond=0)
            end_time = date.replace(hour=18, minute=0, second=0, microsecond=0)
            
            # Convert to RFC3339 format
            time_min = start_time.isoformat() + 'Z'
            time_max = end_time.isoformat() + 'Z'
            
            # Get events for the day
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Calculate available slots
            available_slots = []
            current_time = start_time
            
            for event in events:
                event_start = datetime.fromisoformat(
                    event['start'].get('dateTime', event['start'].get('date'))
                ).replace(tzinfo=None)
                
                # Check if there's a gap before this event
                if current_time + timedelta(minutes=duration_minutes) <= event_start:
                    available_slots.append({
                        'start': current_time.strftime('%H:%M'),
                        'end': (current_time + timedelta(minutes=duration_minutes)).strftime('%H:%M')
                    })
                
                # Move current time to end of this event
                event_end = datetime.fromisoformat(
                    event['end'].get('dateTime', event['end'].get('date'))
                ).replace(tzinfo=None)
                current_time = max(current_time, event_end)
            
            # Check if there's time at the end of the day
            while current_time + timedelta(minutes=duration_minutes) <= end_time:
                available_slots.append({
                    'start': current_time.strftime('%H:%M'),
                    'end': (current_time + timedelta(minutes=duration_minutes)).strftime('%H:%M')
                })
                current_time += timedelta(minutes=duration_minutes)
            
            return available_slots
            
        except HttpError as e:
            logger.error(f"Calendar API error: {e}")
            return []
    
    async def create_appointment(
        self,
        start_time: datetime,
        end_time: datetime,
        customer_name: str,
        customer_phone: str,
        service_type: str,
        notes: Optional[str] = None
    ) -> Dict[str, str]:
        """Create a new appointment"""
        try:
            event = {
                'summary': f'{service_type} - {customer_name}',
                'description': f'Cliente: {customer_name}\nTelefone: {customer_phone}\n{notes or ""}',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            logger.info(f"Appointment created: {event.get('id')}")
            
            return {
                'id': event.get('id'),
                'htmlLink': event.get('htmlLink'),
                'start': start_time.strftime('%d/%m/%Y %H:%M'),
                'end': end_time.strftime('%d/%m/%Y %H:%M')
            }
            
        except HttpError as e:
            logger.error(f"Error creating appointment: {e}")
            raise
    
    async def cancel_appointment(self, event_id: str) -> bool:
        """Cancel an existing appointment"""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Appointment cancelled: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Error cancelling appointment: {e}")
            return False
    
    async def update_appointment(
        self,
        event_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> Dict[str, str]:
        """Update an existing appointment"""
        try:
            # Get current event
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields if provided
            if start_time:
                event['start']['dateTime'] = start_time.isoformat()
            if end_time:
                event['end']['dateTime'] = end_time.isoformat()
            if notes:
                event['description'] = event.get('description', '') + f'\n\nAtualização: {notes}'
            
            # Update event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Appointment updated: {event_id}")
            
            return {
                'id': updated_event.get('id'),
                'htmlLink': updated_event.get('htmlLink'),
                'updated': True
            }
            
        except HttpError as e:
            logger.error(f"Error updating appointment: {e}")
            raise
    
    async def get_appointment_by_phone(self, phone_number: str) -> List[Dict]:
        """Get appointments by customer phone number"""
        try:
            now = datetime.now(self.timezone)
            time_min = now.isoformat()
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                q=phone_number,  # Search in event description
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            appointments = []
            for event in events:
                if phone_number in event.get('description', ''):
                    appointments.append({
                        'id': event['id'],
                        'summary': event['summary'],
                        'start': event['start'].get('dateTime', event['start'].get('date')),
                        'end': event['end'].get('dateTime', event['end'].get('date'))
                    })
            
            return appointments
            
        except HttpError as e:
            logger.error(f"Error searching appointments: {e}")
            return []
    
    async def health_check(self) -> str:
        """Check Calendar service health"""
        try:
            # Try to list calendars
            self.service.calendarList().list().execute()
            return "healthy"
        except:
            return "unhealthy"
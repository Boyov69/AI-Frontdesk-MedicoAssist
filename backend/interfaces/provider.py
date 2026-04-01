"""Abstract interface for appointment providers (Crossuite, external systems, etc.)"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class AppointmentProvider(ABC):
    """Base interface for external appointment system providers"""

    @abstractmethod
    async def get_availability(self, date: str) -> List[Dict[str, Any]]:
        """Get available slots. Returns list of dicts: start, end, fisioterapista, source"""
        pass

    @abstractmethod
    async def create_appointment(self, slot_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Book appointment in external system. Returns dict with ID and status."""
        pass

    @abstractmethod
    async def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment in the external system."""
        pass

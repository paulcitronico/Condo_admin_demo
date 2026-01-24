# Importar todos los modelos para que estén disponibles
from app.models.user import User, Role, Module, ModulePermission
from app.models.booking import Facility, Booking
from app.models.parking import ParkingSpot, ParkingLog
from app.models.financial import FinancialAccount, FinancialTransaction, ServicePayment
from app.models.announcement import Announcement, AnnouncementAcknowledgment, AnnouncementComment

__all__ = [
    'User', 'Role', 'Module', 'ModulePermission',
    'Facility', 'Booking',
    'ParkingSpot', 'ParkingLog',
    'FinancialAccount', 'FinancialTransaction', 'ServicePayment',
    'Announcement', 'AnnouncementAcknowledgment', 'AnnouncementComment'
]

"""
Proxy models for restaurant staff administration.
These models allow us to organize the admin interface into separate sections
without duplicating database tables.
"""
from apps.scheduling.models import RestaurantStaff as BaseRestaurantStaff
from apps.scheduling.models import StaffAvailability as BaseStaffAvailability


class RestaurantStaff(BaseRestaurantStaff):
    """Proxy model for Restaurant Staff to appear in 'Kitchen and serving staff' admin section."""

    class Meta:
        proxy = True
        verbose_name = 'Kitchen and serving staff'
        verbose_name_plural = 'Kitchen and serving staff'


class StaffAvailability(BaseStaffAvailability):
    """Proxy model for Staff Availability to appear in 'Kitchen and serving staff' admin section."""

    class Meta:
        proxy = True
        verbose_name = 'Kitchen and serving staff availability'
        verbose_name_plural = 'Kitchen and serving staff availabilities'

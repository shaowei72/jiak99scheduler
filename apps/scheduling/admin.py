from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from apps.scheduling.models import TourTimeSlot, TourSession, DailySchedule, ShiftSwapRequest
from apps.scheduling.services import SchedulingService


# ============================================================================
# SCHEDULING ADMIN CONFIGURATION
# ============================================================================
#
# SIMPLIFIED ADMIN: Only "Tour sessions" is visible
#
# Hidden from admin (managed via Schedule Manager or commands):
# - Daily schedules
# - Tour time slots
# - Shift swap requests
#
# Managers use this admin to enter tour booking details.
# Guide assignments are done via Schedule Manager interface.
# ============================================================================


@admin.register(TourSession)
class TourSessionAdmin(admin.ModelAdmin):
    """
    Tour Sessions - Manager enters tour booking details here.

    Guide assignment should be done via Schedule Manager interface at:
    /schedule/manager/
    """

    list_display = [
        'date',
        'time_slot',
        'booking_summary_display',
        'assigned_guide',
        'status'
    ]

    list_filter = [
        'status',
        'daily_schedule__date',
        'visitor_type',
        'booking_channel'
    ]

    search_fields = [
        'daily_schedule__date',
        'assigned_guide__user__username',
        'assigned_guide__user__first_name',
        'assigned_guide__user__last_name',
        'notes'
    ]

    date_hierarchy = 'daily_schedule__date'

    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        ('Tour Information', {
            'fields': ['daily_schedule', 'time_slot', 'status']
        }),
        ('Booking Details', {
            'fields': ['visitor_count', 'visitor_type', 'booking_channel'],
            'description': 'Enter the tour booking information here'
        }),
        ('Guide Assignment', {
            'fields': ['assigned_guide'],
            'description': 'For guide assignment, use the Schedule Manager interface'
        }),
        ('Additional Notes', {
            'fields': ['notes'],
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    actions = ['clear_booking_details', 'mark_completed', 'mark_scheduled']

    def booking_summary_display(self, obj):
        """Display booking details in list view."""
        if not obj.visitor_count:
            return format_html('<span style="color: gray;">-</span>')

        parts = []
        parts.append(f'<strong>{obj.visitor_count} 👥</strong>')

        if obj.visitor_type:
            type_color = '#0d6efd' if obj.visitor_type == 'international' else '#198754'
            parts.append(f'<span style="color: {type_color};">{obj.get_visitor_type_display()}</span>')

        if obj.booking_channel:
            channel_icons = {
                'online': '💻',
                'walkin': '🚶',
                'direct': '📞'
            }
            icon = channel_icons.get(obj.booking_channel, '')
            parts.append(f'{icon} {obj.get_booking_channel_display()}')

        return format_html(' | '.join(parts))

    booking_summary_display.short_description = 'Booking Details'

    def date(self, obj):
        """Display the date for this session."""
        return obj.daily_schedule.date

    date.admin_order_field = 'daily_schedule__date'
    date.short_description = 'Date'

    @admin.action(description='Clear booking details from selected sessions')
    def clear_booking_details(self, request, queryset):
        """Clear booking information from selected sessions."""
        count = queryset.update(
            visitor_count=None,
            visitor_type=None,
            booking_channel=None
        )
        self.message_user(
            request,
            f"Cleared booking details from {count} session(s)",
            level=messages.SUCCESS
        )

    @admin.action(description='Mark selected sessions as Completed')
    def mark_completed(self, request, queryset):
        """Mark sessions as completed."""
        count = queryset.update(status='completed')
        self.message_user(
            request,
            f"Marked {count} session(s) as completed",
            level=messages.SUCCESS
        )

    @admin.action(description='Mark selected sessions as Scheduled')
    def mark_scheduled(self, request, queryset):
        """Mark sessions as scheduled."""
        count = queryset.update(status='scheduled')
        self.message_user(
            request,
            f"Marked {count} session(s) as scheduled",
            level=messages.SUCCESS
        )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('daily_schedule', 'time_slot', 'assigned_guide__user')


# ============================================================================
# OTHER MODELS (Not registered - hidden from admin)
# ============================================================================
#
# The following models exist but are NOT shown in admin:
#
# - TourTimeSlot: Managed via management command (generate_tour_slots)
# - DailySchedule: Managed via Schedule Manager interface
# - ShiftSwapRequest: Removed from MVP (future feature)
#
# To access Schedule Manager: /schedule/manager/
# ============================================================================

from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from apps.scheduling.models import (
    TourTimeSlot, TourSession, DailySchedule, ShiftSwapRequest,
    RestaurantStaff, StaffAvailability, DailyRestaurantSchedule, StaffShift
)
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
    /schedule/guide/
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
# To access Schedule Manager: /schedule/guide/
# ============================================================================


# ============================================================================
# RESTAURANT STAFF SCHEDULING ADMIN
# ============================================================================

# RestaurantStaff and StaffAvailability admin moved to apps.restaurant_staff
# to appear under "Kitchen and serving staff" section in admin.
# See apps/restaurant_staff/admin.py for the admin configuration.


@admin.register(DailyRestaurantSchedule)
class DailyRestaurantScheduleAdmin(admin.ModelAdmin):
    """Daily restaurant schedule management."""

    list_display = [
        'date',
        'staff_count_display',
        'is_published_badge',
        'published_at'
    ]

    list_filter = [
        'is_published',
        'date'
    ]

    search_fields = [
        'date',
        'notes'
    ]

    date_hierarchy = 'date'

    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        ('Schedule Information', {
            'fields': ['date', 'is_published', 'published_at']
        }),
        ('Notes', {
            'fields': ['notes']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    actions = ['open_restaurant_manager']

    def staff_count_display(self, obj):
        """Display staff count breakdown."""
        kitchen = obj.get_kitchen_staff_count()
        serving = obj.get_serving_staff_count()
        total = obj.get_total_staff_count()
        return format_html(
            '🍳 {} | 🍽️ {} | <strong>Total: {}</strong>',
            kitchen, serving, total
        )

    staff_count_display.short_description = 'Staff Count'

    def is_published_badge(self, obj):
        """Display publish status with badge."""
        if obj.is_published:
            return format_html(
                '<span style="background-color: #198754; color: white; padding: 3px 8px; border-radius: 3px;">Published</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 3px;">Draft</span>'
            )

    is_published_badge.short_description = 'Status'
    is_published_badge.admin_order_field = 'is_published'

    @admin.action(description='Open Restaurant Schedule Manager')
    def open_restaurant_manager(self, request, queryset):
        """Redirect to restaurant schedule manager."""
        from django.shortcuts import redirect
        if queryset.count() == 1:
            schedule = queryset.first()
            return redirect(f'/schedule/restaurant/?date={schedule.date}')
        else:
            self.message_user(
                request,
                "Please select only one schedule to open in the manager.",
                level=messages.WARNING
            )


@admin.register(StaffShift)
class StaffShiftAdmin(admin.ModelAdmin):
    """Staff shift management."""

    list_display = [
        'date_display',
        'staff',
        'staff_type_display',
        'shift_time_display',
        'duration_badge'
    ]

    list_filter = [
        'duration_hours',
        'staff__staff_type',
        'daily_schedule__date'
    ]

    search_fields = [
        'staff__user__username',
        'staff__user__first_name',
        'staff__user__last_name',
        'daily_schedule__date',
        'notes'
    ]

    date_hierarchy = 'daily_schedule__date'

    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        ('Shift Information', {
            'fields': ['daily_schedule', 'staff', 'duration_hours']
        }),
        ('Timing', {
            'fields': ['start_time', 'end_time']
        }),
        ('Notes', {
            'fields': ['notes']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def date_display(self, obj):
        """Display the shift date."""
        return obj.daily_schedule.date

    date_display.short_description = 'Date'
    date_display.admin_order_field = 'daily_schedule__date'

    def staff_type_display(self, obj):
        """Display staff type."""
        if obj.staff:
            colors = {
                'kitchen': '#dc3545',
                'serving': '#0d6efd',
            }
            color = colors.get(obj.staff.staff_type, '#6c757d')
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color,
                obj.staff.get_staff_type_display()
            )
        return '-'

    staff_type_display.short_description = 'Type'

    def shift_time_display(self, obj):
        """Display shift time range."""
        return f"{obj.start_time.strftime('%I:%M %p')} - {obj.end_time.strftime('%I:%M %p')}"

    shift_time_display.short_description = 'Shift Time'

    def duration_badge(self, obj):
        """Display shift duration with badge."""
        if obj.is_full_day:
            return format_html(
                '<span style="background-color: #0d6efd; color: white; padding: 3px 8px; border-radius: 3px;">8h Full</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 3px;">4h Half</span>'
            )

    duration_badge.short_description = 'Duration'
    duration_badge.admin_order_field = 'duration_hours'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('daily_schedule', 'staff__user')

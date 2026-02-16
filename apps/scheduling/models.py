from django.db import models
from django.core.exceptions import ValidationError
from apps.guides.models import Guide
from datetime import datetime, timedelta


class TourTimeSlot(models.Model):
    """Predefined tour time slots (e.g., 8:30am-10:30am)."""
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.IntegerField()

    class Meta:
        ordering = ['start_time']
        unique_together = ['start_time', 'end_time']

    def __str__(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"

    def clean(self):
        """Validate that end_time is after start_time."""
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError("End time must be after start time.")

            # Calculate duration
            start_dt = datetime.combine(datetime.today(), self.start_time)
            end_dt = datetime.combine(datetime.today(), self.end_time)
            calculated_duration = int((end_dt - start_dt).total_seconds() / 60)

            if self.duration_minutes and self.duration_minutes != calculated_duration:
                raise ValidationError(
                    f"Duration mismatch: calculated {calculated_duration} minutes "
                    f"but {self.duration_minutes} provided."
                )

    def save(self, *args, **kwargs):
        # Auto-calculate duration if not provided
        if not self.duration_minutes and self.start_time and self.end_time:
            start_dt = datetime.combine(datetime.today(), self.start_time)
            end_dt = datetime.combine(datetime.today(), self.end_time)
            self.duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        self.full_clean()
        super().save(*args, **kwargs)


class DailySchedule(models.Model):
    """Metadata for a day's schedule."""
    date = models.DateField(unique=True)
    standby_guide = models.ForeignKey(
        Guide,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='standby_days'
    )
    is_published = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date']
        verbose_name_plural = 'Daily schedules'

    def __str__(self):
        status = "Published" if self.is_published else "Draft"
        return f"Schedule for {self.date} ({status})"

    def get_coverage_percentage(self):
        """Calculate percentage of sessions with assigned guides."""
        total_sessions = self.sessions.count()
        if total_sessions == 0:
            return 0
        assigned_sessions = self.sessions.exclude(assigned_guide__isnull=True).count()
        return round((assigned_sessions / total_sessions) * 100)

    def get_validation_errors(self):
        """Get all validation errors for this schedule."""
        from apps.scheduling.services import SchedulingService
        service = SchedulingService()
        return service.validate_daily_schedule(self)


class TourSession(models.Model):
    """A specific tour instance on a specific date."""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    daily_schedule = models.ForeignKey(
        DailySchedule,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    time_slot = models.ForeignKey(TourTimeSlot, on_delete=models.PROTECT)
    assigned_guide = models.ForeignKey(
        Guide,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tour_sessions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Booking details (NEW - Phase 0)
    visitor_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of visitors for this tour"
    )

    VISITOR_TYPE_CHOICES = [
        ('local', 'Local'),
        ('international', 'International'),
    ]
    visitor_type = models.CharField(
        max_length=20,
        choices=VISITOR_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="Type of visitors (Local or International)"
    )

    BOOKING_CHANNEL_CHOICES = [
        ('online', 'Online Platform'),
        ('walkin', 'Walk-in'),
        ('direct', 'Direct Sales'),
    ]
    booking_channel = models.CharField(
        max_length=20,
        choices=BOOKING_CHANNEL_CHOICES,
        null=True,
        blank=True,
        help_text="How the tour was booked"
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['daily_schedule__date', 'time_slot__start_time']
        unique_together = ['daily_schedule', 'time_slot']

    def __str__(self):
        guide_name = self.assigned_guide.user.get_full_name() if self.assigned_guide else "Unassigned"
        return f"{self.daily_schedule.date} {self.time_slot} - {guide_name}"

    @property
    def date(self):
        """Convenience property to get the session date."""
        return self.daily_schedule.date

    def get_validation_errors(self):
        """Get validation errors for this session assignment."""
        if not self.assigned_guide:
            return []

        from apps.scheduling.services import SchedulingService
        service = SchedulingService()
        return service.validate_session_assignment(self)

    def get_booking_summary(self):
        """Get a one-line summary of booking details."""
        if not self.visitor_count:
            return "No booking details"

        parts = [f"{self.visitor_count} visitors"]
        if self.visitor_type:
            parts.append(self.get_visitor_type_display())
        if self.booking_channel:
            parts.append(f"via {self.get_booking_channel_display()}")

        return ", ".join(parts)

    def has_booking_details(self):
        """Check if any booking details are filled."""
        return bool(
            self.visitor_count or
            self.visitor_type or
            self.booking_channel
        )


class ShiftSwapRequest(models.Model):
    """Track shift swap requests between guides."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    requesting_guide = models.ForeignKey(
        Guide,
        on_delete=models.CASCADE,
        related_name='swap_requests_made'
    )
    target_guide = models.ForeignKey(
        Guide,
        on_delete=models.CASCADE,
        related_name='swap_requests_received'
    )
    original_session = models.ForeignKey(
        TourSession,
        on_delete=models.CASCADE,
        related_name='swap_requests_from'
    )
    target_session = models.ForeignKey(
        TourSession,
        on_delete=models.CASCADE,
        related_name='swap_requests_to',
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField()
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Swap request from {self.requesting_guide} ({self.status})"


# ============================================================================
# RESTAURANT STAFF SCHEDULING MODELS
# ============================================================================

class RestaurantStaff(models.Model):
    """Kitchen or Serving staff member."""

    STAFF_TYPE_CHOICES = [
        ('kitchen', 'Kitchen Staff'),
        ('serving', 'Serving Staff'),
    ]

    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='restaurant_staff'
    )
    staff_type = models.CharField(
        max_length=20,
        choices=STAFF_TYPE_CHOICES,
        help_text="Type of staff: Kitchen or Serving"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this staff member is currently active"
    )
    hire_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when staff was hired"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['staff_type', 'user__first_name', 'user__last_name']
        verbose_name = 'Restaurant Staff'
        verbose_name_plural = 'Restaurant Staff'

    def __str__(self):
        staff_type_display = self.get_staff_type_display()
        name = self.user.get_full_name() or self.user.username
        return f"{name} ({staff_type_display})"

    def clean(self):
        """Validate that user doesn't already have a Guide profile."""
        from django.core.exceptions import ValidationError
        from apps.guides.models import Guide

        if self.user_id:
            try:
                Guide.objects.get(user=self.user)
                raise ValidationError(
                    f"User '{self.user.get_full_name() or self.user.username}' already has a Guide profile. "
                    "A user cannot be both a Tour Guide and Restaurant Staff. "
                    "Please remove the Guide profile first or choose a different user."
                )
            except Guide.DoesNotExist:
                pass  # Good, no conflict

    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_full_name(self):
        """Get staff member's full name."""
        return self.user.get_full_name() or self.user.username


class StaffAvailability(models.Model):
    """Track which days staff members are available to work."""

    staff = models.ForeignKey(
        RestaurantStaff,
        on_delete=models.CASCADE,
        related_name='availability'
    )
    date = models.DateField()
    is_available = models.BooleanField(
        default=True,
        help_text="Whether staff is available on this date"
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes (e.g., reason for unavailability)"
    )

    class Meta:
        unique_together = ['staff', 'date']
        ordering = ['date', 'staff']
        verbose_name = 'Staff Availability'
        verbose_name_plural = 'Staff Availability'

    def __str__(self):
        status = "Available" if self.is_available else "Unavailable"
        return f"{self.staff.user.get_full_name()} - {self.date} ({status})"


class DailyRestaurantSchedule(models.Model):
    """Container for all restaurant staff shifts on a specific date."""

    date = models.DateField(
        unique=True,
        help_text="Date for this restaurant schedule"
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Whether this schedule has been published to staff"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this schedule was published"
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes for this day's schedule"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date']
        verbose_name = 'Daily Restaurant Schedule'
        verbose_name_plural = 'Daily Restaurant Schedules'

    def __str__(self):
        status = "Published" if self.is_published else "Draft"
        return f"Restaurant Schedule for {self.date} ({status})"

    def get_kitchen_staff_count(self):
        """Get number of kitchen staff assigned for this day."""
        return self.shifts.filter(
            staff__staff_type='kitchen',
            staff__isnull=False
        ).values('staff').distinct().count()

    def get_serving_staff_count(self):
        """Get number of serving staff assigned for this day."""
        return self.shifts.filter(
            staff__staff_type='serving',
            staff__isnull=False
        ).values('staff').distinct().count()

    def get_total_staff_count(self):
        """Get total number of staff assigned for this day."""
        return self.get_kitchen_staff_count() + self.get_serving_staff_count()

    def get_coverage_valid(self):
        """Check if minimum coverage is met at all times (2 kitchen + 2 serving)."""
        # This will be implemented in the service layer
        from apps.scheduling.services import RestaurantSchedulingService
        service = RestaurantSchedulingService()
        return service.validate_coverage(self)


class StaffShift(models.Model):
    """Individual shift assignment (4 or 8 hours)."""

    SHIFT_DURATION_CHOICES = [
        (4, '4 hours (Half-day)'),
        (8, '8 hours (Full-day)'),
    ]

    daily_schedule = models.ForeignKey(
        DailyRestaurantSchedule,
        on_delete=models.CASCADE,
        related_name='shifts'
    )
    staff = models.ForeignKey(
        RestaurantStaff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shifts',
        help_text="Assigned staff member (or None if unassigned)"
    )

    # Shift timing
    start_time = models.TimeField(
        help_text="Shift start time (e.g., 10:00 AM)"
    )
    end_time = models.TimeField(
        help_text="Shift end time (e.g., 6:00 PM)"
    )
    duration_hours = models.IntegerField(
        choices=SHIFT_DURATION_CHOICES,
        default=8,
        help_text="Shift duration: 4 hours (half-day) or 8 hours (full-day)"
    )

    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['daily_schedule__date', 'start_time', 'staff__staff_type']
        verbose_name = 'Staff Shift'
        verbose_name_plural = 'Staff Shifts'

    def __str__(self):
        staff_name = self.staff.user.get_full_name() if self.staff else "Unassigned"
        staff_type = f"({self.staff.get_staff_type_display()})" if self.staff else ""
        return f"{self.daily_schedule.date} {self.start_time}-{self.end_time} - {staff_name} {staff_type}"

    @property
    def is_full_day(self):
        """Returns True if 8-hour shift."""
        return self.duration_hours == 8

    @property
    def is_half_day(self):
        """Returns True if 4-hour shift."""
        return self.duration_hours == 4

    @property
    def staff_type(self):
        """Kitchen or Serving."""
        return self.staff.staff_type if self.staff else None

    @property
    def date(self):
        """Convenience property to get the shift date."""
        return self.daily_schedule.date

    def clean(self):
        """Validate shift duration matches start/end times."""
        if self.start_time and self.end_time:
            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)
            actual_hours = (end - start).total_seconds() / 3600

            if abs(actual_hours - self.duration_hours) > 0.1:
                raise ValidationError(
                    f"Duration mismatch: {actual_hours:.1f} hours between "
                    f"start and end, but duration_hours is {self.duration_hours}"
                )

            # Validate operating hours (10:00 AM - 9:30 PM)
            operating_start = datetime.combine(datetime.today(), datetime.strptime('10:00', '%H:%M').time())
            operating_end = datetime.combine(datetime.today(), datetime.strptime('21:30', '%H:%M').time())

            if start < operating_start or end > operating_end:
                raise ValidationError(
                    "Shift must be within operating hours (10:00 AM - 9:30 PM)"
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

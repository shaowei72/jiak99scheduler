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

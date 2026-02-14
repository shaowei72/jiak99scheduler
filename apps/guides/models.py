from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date, timedelta


class Guide(models.Model):
    GUIDE_TYPE_CHOICES = [
        ('FT', 'Full-time'),
        ('PTM', 'Part-time Morning'),
        ('PTA', 'Part-time Afternoon'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guide_profile')
    guide_type = models.CharField(max_length=3, choices=GUIDE_TYPE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_guide_type_display()})"

    def can_work_timeslot(self, timeslot):
        """Check if guide type is compatible with time slot."""
        from datetime import time

        if self.guide_type == 'FT':
            return True
        elif self.guide_type == 'PTM':
            # Can only work slots ending by 2:30pm
            cutoff_time = time(14, 30)
            return timeslot.end_time <= cutoff_time
        elif self.guide_type == 'PTA':
            # Can only work slots starting from 2:30pm
            cutoff_time = time(14, 30)
            return timeslot.start_time >= cutoff_time
        return False


class GuideAvailability(models.Model):
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    is_available = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date']
        unique_together = ['guide', 'date']
        verbose_name_plural = 'Guide availabilities'

    def __str__(self):
        status = "Available" if self.is_available else "Unavailable"
        return f"{self.guide.user.get_full_name()} - {self.date} ({status})"

    def clean(self):
        """Validate that availability can only be marked up to 3 months ahead."""
        if self.date:
            max_date = date.today() + timedelta(days=90)
            if self.date > max_date:
                raise ValidationError(
                    f"Availability can only be marked up to 3 months ahead (until {max_date})."
                )
            if self.date < date.today():
                raise ValidationError("Cannot mark availability for past dates.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

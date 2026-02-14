from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from apps.guides.models import GuideAvailability


class AvailabilityForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Start Date'
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='End Date'
    )
    is_available = forms.ChoiceField(
        choices=[
            (True, 'Available'),
            (False, 'Unavailable')
        ],
        widget=forms.RadioSelect,
        label='Availability Status',
        initial=True
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label='Notes (optional)'
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            # Validate dates are not in the past
            if start_date < date.today():
                raise ValidationError("Start date cannot be in the past.")

            # Validate end date is after start date
            if end_date < start_date:
                raise ValidationError("End date must be after start date.")

            # Validate within 3 months
            max_date = date.today() + timedelta(days=90)
            if end_date > max_date:
                raise ValidationError(
                    f"Availability can only be marked up to 3 months ahead (until {max_date})."
                )

            # Validate date range is not too long (e.g., max 30 days)
            date_range = (end_date - start_date).days + 1
            if date_range > 60:
                raise ValidationError("Date range cannot exceed 60 days. Please split into smaller ranges.")

        return cleaned_data

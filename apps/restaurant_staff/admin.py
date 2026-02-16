"""
Admin configuration for Kitchen and Serving Staff.
Uses proxy models to organize the admin interface into a separate section.
"""
from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.contrib import messages
from datetime import date, timedelta
from apps.restaurant_staff.models import RestaurantStaff, StaffAvailability


class StaffAvailabilityForm(forms.ModelForm):
    """Custom form for staff availability with date range support."""

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Start date of availability period'
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='End date of availability period (leave empty for single day)'
    )

    class Meta:
        model = StaffAvailability
        fields = ['staff', 'start_date', 'end_date', 'is_available', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing existing record, populate start_date with the date value
        if self.instance and self.instance.pk:
            self.fields['start_date'].initial = self.instance.date
            self.fields['end_date'].widget = forms.HiddenInput()  # Hide end_date when editing
            self.fields['end_date'].required = False

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date:
            # Validate start date is not in the past
            if start_date < date.today():
                raise forms.ValidationError("Start date cannot be in the past.")

            # Validate date range
            if end_date:
                if end_date < start_date:
                    raise forms.ValidationError("End date must be on or after start date.")

                # Limit range to 90 days
                days_diff = (end_date - start_date).days
                if days_diff > 90:
                    raise forms.ValidationError("Date range cannot exceed 90 days.")

                # Limit to 3 months ahead
                max_date = date.today() + timedelta(days=90)
                if end_date > max_date:
                    raise forms.ValidationError(f"End date cannot be more than 3 months ahead (until {max_date}).")

        return cleaned_data

    def save(self, commit=True):
        """Override save to handle single date, but date range is handled in admin."""
        # If editing existing record, just update it
        if self.instance.pk:
            self.instance.date = self.cleaned_data['start_date']
            if commit:
                self.instance.save()
            return self.instance

        # For new records, set the date from start_date
        self.instance.date = self.cleaned_data['start_date']

        if commit:
            self.instance.save()

        return self.instance

    def save_m2m(self):
        """Required method for Django admin compatibility."""
        pass


@admin.register(RestaurantStaff)
class RestaurantStaffAdmin(admin.ModelAdmin):
    """Restaurant Staff (Kitchen and Serving) management."""

    list_display = [
        'get_full_name',
        'staff_type_badge',
        'is_active',
        'hire_date',
        'created_at'
    ]

    list_filter = [
        'staff_type',
        'is_active',
        'hire_date'
    ]

    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email'
    ]

    date_hierarchy = 'hire_date'

    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        ('Staff Information', {
            'description': 'Add kitchen or serving staff. First create a User account if one doesn\'t exist, then select it here. Note: A user cannot be both a Tour Guide and Restaurant Staff.',
            'fields': ['user', 'staff_type', 'is_active']
        }),
        ('Employment Details', {
            'fields': ['hire_date']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def get_full_name(self, obj):
        """Display the staff member's full name."""
        return obj.user.get_full_name() or obj.user.username

    get_full_name.short_description = 'Name'
    get_full_name.admin_order_field = 'user__first_name'

    def staff_type_badge(self, obj):
        """Display staff type with color badge."""
        colors = {
            'kitchen': '#dc3545',  # red
            'serving': '#0d6efd',  # blue
        }
        color = colors.get(obj.staff_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_staff_type_display()
        )

    staff_type_badge.short_description = 'Type'
    staff_type_badge.admin_order_field = 'staff_type'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(StaffAvailability)
class StaffAvailabilityAdmin(admin.ModelAdmin):
    """Staff availability management with date range support."""

    form = StaffAvailabilityForm

    list_display = [
        'date',
        'staff',
        'staff_type_display',
        'is_available_badge',
        'notes_preview'
    ]

    list_filter = [
        'is_available',
        'staff__staff_type',
        'date'
    ]

    search_fields = [
        'staff__user__username',
        'staff__user__first_name',
        'staff__user__last_name',
        'notes'
    ]

    date_hierarchy = 'date'

    def get_fieldsets(self, request, obj=None):
        """Return different fieldsets for add vs edit."""
        if obj:  # Editing existing record
            return [
                ('Availability Information', {
                    'fields': ['staff', 'start_date', 'is_available']
                }),
                ('Notes', {
                    'fields': ['notes']
                }),
            ]
        else:  # Adding new record
            return [
                ('Date Range', {
                    'description': 'Select a date range to mark availability for multiple days at once. Leave end date empty for a single day.',
                    'fields': ['staff', 'start_date', 'end_date', 'is_available']
                }),
                ('Notes', {
                    'fields': ['notes']
                }),
            ]

    def staff_type_display(self, obj):
        """Display staff type."""
        return obj.staff.get_staff_type_display()

    staff_type_display.short_description = 'Staff Type'
    staff_type_display.admin_order_field = 'staff__staff_type'

    def is_available_badge(self, obj):
        """Display availability with color badge."""
        if obj.is_available:
            return format_html(
                '<span style="background-color: #198754; color: white; padding: 3px 8px; border-radius: 3px;">Available</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px;">Unavailable</span>'
            )

    is_available_badge.short_description = 'Status'
    is_available_badge.admin_order_field = 'is_available'

    def notes_preview(self, obj):
        """Display first 50 characters of notes."""
        if obj.notes:
            preview = obj.notes[:50]
            if len(obj.notes) > 50:
                preview += '...'
            return preview
        return '-'

    notes_preview.short_description = 'Notes'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('staff__user')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize the foreign key field to show better labels."""
        if db_field.name == "staff":
            kwargs["queryset"] = RestaurantStaff.objects.select_related('user').order_by('user__first_name', 'user__last_name', 'user__username')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """Override to handle date range creation."""
        if not change:
            # Adding new record(s)
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data.get('end_date')
            staff = form.cleaned_data['staff']
            is_available = form.cleaned_data['is_available']
            notes = form.cleaned_data.get('notes', '')

            if end_date and end_date != start_date:
                # Creating records for date range
                days_count = (end_date - start_date).days + 1
                current_date = start_date
                first_obj = None

                while current_date <= end_date:
                    # Create or update existing availability record
                    availability, created = StaffAvailability.objects.update_or_create(
                        staff=staff,
                        date=current_date,
                        defaults={
                            'is_available': is_available,
                            'notes': notes
                        }
                    )
                    if first_obj is None:
                        first_obj = availability
                    current_date += timedelta(days=1)

                # Store info for response_add method
                request._staff_availability_range = {
                    'staff_name': staff.user.get_full_name() or staff.user.username,
                    'status': "available" if is_available else "unavailable",
                    'days_count': days_count,
                    'start_date': start_date,
                    'end_date': end_date
                }

                # Update obj to point to the first created record for redirect
                if first_obj:
                    obj.pk = first_obj.pk
                    obj.date = first_obj.date
            else:
                # Single date - just save normally
                super().save_model(request, obj, form, change)
        else:
            # Editing existing - just save normally
            super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        """Override to show custom success message for date ranges."""
        if hasattr(request, '_staff_availability_range'):
            info = request._staff_availability_range
            self.message_user(
                request,
                f"Successfully marked {info['staff_name']} as {info['status']} for {info['days_count']} days "
                f"({info['start_date']} to {info['end_date']}). Existing records were updated.",
                messages.SUCCESS
            )
        return super().response_add(request, obj, post_url_continue)

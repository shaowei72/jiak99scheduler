from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from apps.scheduling.models import TourTimeSlot, TourSession, DailySchedule, ShiftSwapRequest
from apps.scheduling.services import SchedulingService


@admin.register(TourTimeSlot)
class TourTimeSlotAdmin(admin.ModelAdmin):
    list_display = ['start_time', 'end_time', 'duration_minutes']
    ordering = ['start_time']
    readonly_fields = ['duration_minutes']


class TourSessionInline(admin.TabularInline):
    model = TourSession
    extra = 0
    fields = ['time_slot', 'assigned_guide', 'status', 'validation_status', 'notes']
    readonly_fields = ['validation_status']
    autocomplete_fields = ['assigned_guide']

    def validation_status(self, obj):
        if not obj.assigned_guide:
            return format_html('<span style="color: gray;">-</span>')

        errors = obj.get_validation_errors()
        if errors:
            error_list = '<br>'.join(f'• {err}' for err in errors)
            return format_html(
                '<span style="color: red;" title="{}">\u2717 Invalid</span>',
                error_list
            )
        return format_html('<span style="color: green;">\u2713 Valid</span>')

    validation_status.short_description = 'Validation'


@admin.register(TourSession)
class TourSessionAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'time_slot',
        'assigned_guide',
        'status',
        'validation_status_display'
    ]
    list_filter = ['status', 'daily_schedule__date', 'time_slot']
    search_fields = [
        'assigned_guide__user__username',
        'assigned_guide__user__first_name',
        'assigned_guide__user__last_name'
    ]
    autocomplete_fields = ['assigned_guide']
    readonly_fields = ['validation_status_display', 'created_at', 'updated_at']
    date_hierarchy = 'daily_schedule__date'
    actions = ['validate_sessions', 'unassign_guides']

    fieldsets = [
        (None, {
            'fields': ['daily_schedule', 'time_slot', 'assigned_guide', 'status']
        }),
        ('Validation', {
            'fields': ['validation_status_display'],
        }),
        ('Additional Info', {
            'fields': ['notes'],
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def validation_status_display(self, obj):
        if not obj.assigned_guide:
            return format_html('<span style="color: gray;">No guide assigned</span>')

        errors = obj.get_validation_errors()
        if errors:
            error_html = '<ul style="margin: 0; padding-left: 20px;">'
            for err in errors:
                error_html += f'<li>{err}</li>'
            error_html += '</ul>'
            return format_html(
                '<div style="color: red;"><strong>\u2717 Validation Failed</strong>{}</div>',
                error_html
            )
        return format_html(
            '<div style="color: green;"><strong>\u2713 Valid Assignment</strong></div>'
        )

    validation_status_display.short_description = 'Validation Status'

    def date(self, obj):
        return obj.daily_schedule.date
    date.admin_order_field = 'daily_schedule__date'

    @admin.action(description='Validate selected sessions')
    def validate_sessions(self, request, queryset):
        invalid_count = 0
        valid_count = 0

        for session in queryset:
            if session.assigned_guide:
                errors = session.get_validation_errors()
                if errors:
                    invalid_count += 1
                    error_msg = '; '.join(errors)
                    self.message_user(
                        request,
                        f"Session {session}: {error_msg}",
                        level=messages.ERROR
                    )
                else:
                    valid_count += 1

        if valid_count:
            self.message_user(
                request,
                f"{valid_count} session(s) validated successfully",
                level=messages.SUCCESS
            )
        if invalid_count:
            self.message_user(
                request,
                f"{invalid_count} session(s) have validation errors",
                level=messages.WARNING
            )

    @admin.action(description='Unassign guides from selected sessions')
    def unassign_guides(self, request, queryset):
        count = queryset.update(assigned_guide=None)
        self.message_user(
            request,
            f"Unassigned guides from {count} session(s)",
            level=messages.SUCCESS
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('daily_schedule', 'time_slot', 'assigned_guide__user')


@admin.register(DailySchedule)
class DailyScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'standby_guide',
        'coverage_status',
        'is_published',
        'created_at'
    ]
    list_filter = ['is_published', 'date']
    search_fields = ['standby_guide__user__username', 'standby_guide__user__first_name']
    date_hierarchy = 'date'
    readonly_fields = ['coverage_status', 'validation_summary', 'created_at', 'updated_at']
    autocomplete_fields = ['standby_guide']
    inlines = [TourSessionInline]
    actions = ['auto_schedule_days', 'publish_schedules', 'unpublish_schedules', 'validate_schedules']

    fieldsets = [
        (None, {
            'fields': ['date', 'standby_guide', 'is_published']
        }),
        ('Status', {
            'fields': ['coverage_status', 'validation_summary'],
        }),
        ('Notes', {
            'fields': ['notes'],
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def coverage_status(self, obj):
        percentage = obj.get_coverage_percentage()
        total = obj.sessions.count()
        assigned = obj.sessions.exclude(assigned_guide__isnull=True).count()

        if percentage == 100:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'red'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/{} ({}%)</span>',
            color, assigned, total, percentage
        )
    coverage_status.short_description = 'Coverage'

    def validation_summary(self, obj):
        errors = obj.get_validation_errors()

        html = '<div>'

        if errors['general']:
            html += '<div style="margin-bottom: 10px;"><strong>General Issues:</strong><ul style="margin: 5px 0; padding-left: 20px;">'
            for err in errors['general']:
                html += f'<li style="color: red;">{err}</li>'
            html += '</ul></div>'

        if errors['sessions']:
            html += '<div><strong>Session Issues:</strong><ul style="margin: 5px 0; padding-left: 20px;">'
            for session_id, session_errors in errors['sessions'].items():
                try:
                    session = TourSession.objects.get(id=session_id)
                    html += f'<li><strong>{session.time_slot}:</strong><ul style="padding-left: 20px;">'
                    for err in session_errors:
                        html += f'<li style="color: red;">{err}</li>'
                    html += '</ul></li>'
                except TourSession.DoesNotExist:
                    pass
            html += '</ul></div>'

        if not errors['general'] and not errors['sessions']:
            html += '<div style="color: green; font-weight: bold;">\u2713 All validations passed</div>'

        html += '</div>'
        return format_html(html)

    validation_summary.short_description = 'Validation Summary'

    @admin.action(description='Publish selected schedules')
    def publish_schedules(self, request, queryset):
        service = SchedulingService()
        published_count = 0
        error_count = 0

        for schedule in queryset:
            can_publish, errors = service.can_publish_schedule(schedule)

            if can_publish:
                schedule.is_published = True
                schedule.save()
                published_count += 1
            else:
                error_count += 1
                error_msg = '; '.join(errors[:3])  # Show first 3 errors
                self.message_user(
                    request,
                    f"Cannot publish {schedule.date}: {error_msg}",
                    level=messages.ERROR
                )

        if published_count:
            self.message_user(
                request,
                f"Published {published_count} schedule(s)",
                level=messages.SUCCESS
            )
        if error_count:
            self.message_user(
                request,
                f"{error_count} schedule(s) could not be published due to validation errors",
                level=messages.WARNING
            )

    @admin.action(description='Unpublish selected schedules')
    def unpublish_schedules(self, request, queryset):
        count = queryset.update(is_published=False)
        self.message_user(
            request,
            f"Unpublished {count} schedule(s)",
            level=messages.SUCCESS
        )

    @admin.action(description='Validate selected schedules')
    def validate_schedules(self, request, queryset):
        valid_count = 0
        invalid_count = 0

        for schedule in queryset:
            errors = schedule.get_validation_errors()
            if not errors['general'] and not errors['sessions']:
                valid_count += 1
            else:
                invalid_count += 1
                error_msg = '; '.join(errors['general'][:2])  # Show first 2 errors
                self.message_user(
                    request,
                    f"Schedule {schedule.date}: {error_msg}",
                    level=messages.ERROR
                )

        if valid_count:
            self.message_user(
                request,
                f"{valid_count} schedule(s) are valid",
                level=messages.SUCCESS
            )
        if invalid_count:
            self.message_user(
                request,
                f"{invalid_count} schedule(s) have validation errors",
                level=messages.WARNING
            )

    @admin.action(description='Auto-schedule guides for selected days')
    def auto_schedule_days(self, request, queryset):
        service = SchedulingService()
        total_assigned = 0
        total_unfillable = 0
        schedules_processed = 0

        for schedule in queryset:
            results = service.auto_schedule_day(schedule, assign_standby=True)

            total_assigned += results['assigned_count']
            total_unfillable += results['unfillable_count']
            schedules_processed += 1

            if results['unfillable_count'] > 0:
                self.message_user(
                    request,
                    f"{schedule.date}: Could not fill {results['unfillable_count']} session(s)",
                    level=messages.WARNING
                )

        if total_assigned > 0:
            self.message_user(
                request,
                f"Successfully auto-assigned {total_assigned} session(s) across {schedules_processed} day(s)",
                level=messages.SUCCESS
            )

        if total_unfillable > 0:
            self.message_user(
                request,
                f"Warning: {total_unfillable} session(s) could not be filled (no eligible guides available)",
                level=messages.ERROR
            )

        if total_assigned == 0 and total_unfillable == 0:
            self.message_user(
                request,
                "No sessions were assigned. All sessions may already be assigned.",
                level=messages.INFO
            )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('standby_guide__user').prefetch_related('sessions')


@admin.register(ShiftSwapRequest)
class ShiftSwapRequestAdmin(admin.ModelAdmin):
    list_display = [
        'requesting_guide',
        'target_guide',
        'original_session',
        'status',
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'requesting_guide__user__username',
        'target_guide__user__username'
    ]
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_swaps', 'reject_swaps']

    fieldsets = [
        ('Request Details', {
            'fields': [
                'requesting_guide',
                'target_guide',
                'original_session',
                'target_session',
                'reason'
            ]
        }),
        ('Status', {
            'fields': ['status', 'admin_notes']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    @admin.action(description='Approve selected swap requests')
    def approve_swaps(self, request, queryset):
        count = queryset.filter(status='pending').update(status='approved')
        self.message_user(
            request,
            f"Approved {count} swap request(s)",
            level=messages.SUCCESS
        )

    @admin.action(description='Reject selected swap requests')
    def reject_swaps(self, request, queryset):
        count = queryset.filter(status='pending').update(status='rejected')
        self.message_user(
            request,
            f"Rejected {count} swap request(s)",
            level=messages.SUCCESS
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'requesting_guide__user',
            'target_guide__user',
            'original_session__daily_schedule',
            'original_session__time_slot'
        )

"""
API views for Schedule Manager AJAX operations.
Phase 2: Editing and validation
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
import json

from apps.scheduling.models import TourSession, DailySchedule, TourTimeSlot, DailyRestaurantSchedule, StaffShift, RestaurantStaff
from apps.guides.models import Guide
from apps.scheduling.services import SchedulingService, RestaurantSchedulingService


@staff_member_required
@require_http_methods(["POST"])
def assign_guide(request):
    """
    Assign or update guide for a tour session.
    Also handles booking details.
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        guide_id = data.get('guide_id')
        visitor_count = data.get('visitor_count')
        visitor_type = data.get('visitor_type')
        booking_channel = data.get('booking_channel')

        session = TourSession.objects.get(id=session_id)

        # Update assignment
        if guide_id:
            session.assigned_guide = Guide.objects.get(id=guide_id)
        else:
            session.assigned_guide = None

        # Update booking details
        session.visitor_count = visitor_count if visitor_count else None
        session.visitor_type = visitor_type if visitor_type else None
        session.booking_channel = booking_channel if booking_channel else None

        session.save()

        # Validate
        service = SchedulingService()
        errors = service.validate_session_assignment(session)

        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'errors': errors,
            'booking_summary': session.get_booking_summary() if session.assigned_guide else None
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["POST"])
def unassign_guide(request):
    """Unassign guide from a tour session."""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')

        session = TourSession.objects.get(id=session_id)
        session.assigned_guide = None
        session.save()

        return JsonResponse({
            'success': True,
            'session_id': session.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["GET"])
def get_eligible_guides(request, session_id):
    """
    Get list of guides eligible to work a specific session.
    Filters by guide type, availability, and current assignments.
    """
    try:
        session = TourSession.objects.get(id=session_id)
        service = SchedulingService()

        eligible_guides = service.get_available_guides_for_session(session)

        guides_data = [{
            'id': guide.id,
            'name': guide.user.get_full_name() or guide.user.username,
            'type': guide.get_guide_type_display(),
            'type_code': guide.guide_type
        } for guide in eligible_guides]

        return JsonResponse({
            'success': True,
            'guides': guides_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["GET"])
def get_session_data(request, session_id):
    """Get full data for a session including current assignment and booking details."""
    try:
        session = TourSession.objects.get(id=session_id)

        data = {
            'success': True,
            'session_id': session.id,
            'time_slot': str(session.time_slot),
            'assigned_guide_id': session.assigned_guide.id if session.assigned_guide else None,
            'assigned_guide_name': session.assigned_guide.user.get_full_name() if session.assigned_guide else None,
            'visitor_count': session.visitor_count,
            'visitor_type': session.visitor_type,
            'booking_channel': session.booking_channel,
            'notes': session.notes
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["POST"])
def update_standby(request):
    """Update standby guide for a daily schedule."""
    try:
        data = json.loads(request.body)
        date_str = data.get('date')
        guide_id = data.get('guide_id')

        schedule = DailySchedule.objects.get(date=date_str)

        if guide_id:
            schedule.standby_guide = Guide.objects.get(id=guide_id)
        else:
            schedule.standby_guide = None

        schedule.save()

        return JsonResponse({
            'success': True,
            'standby_guide_id': schedule.standby_guide.id if schedule.standby_guide else None
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["GET"])
def get_schedule_stats(request, date_str):
    """Get statistics for a daily schedule."""
    try:
        schedule = DailySchedule.objects.get(date=date_str)

        total = schedule.sessions.count()
        assigned = schedule.sessions.exclude(assigned_guide__isnull=True).count()
        unassigned = total - assigned

        # Count validation errors
        service = SchedulingService()
        errors = service.validate_daily_schedule(schedule)
        error_count = len(errors.get('sessions', {}))

        return JsonResponse({
            'success': True,
            'total_slots': total,
            'assigned_count': assigned,
            'unassigned_count': unassigned,
            'error_count': error_count,
            'has_standby': schedule.standby_guide is not None,
            'is_published': schedule.is_published
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["POST"])
def auto_assign_day(request):
    """
    Run auto-assignment algorithm for a specific date.
    Phase 3: Auto-assignment integration.
    """
    try:
        data = json.loads(request.body)
        date_str = data.get('date')
        assign_standby = data.get('assign_standby', True)

        schedule = DailySchedule.objects.get(date=date_str)
        service = SchedulingService()

        # Run auto-scheduler
        results = service.auto_schedule_day(schedule, assign_standby=assign_standby)

        return JsonResponse({
            'success': True,
            'assigned_count': results['assigned_count'],
            'unfillable_count': results['unfillable_count'],
            'unfillable_sessions': results['unfillable_sessions'],
            'errors': results.get('errors', [])
        })

    except DailySchedule.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'No schedule found for {date_str}'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["POST"])
def clear_all_assignments(request):
    """
    Clear all guide assignments for a specific date.
    """
    try:
        data = json.loads(request.body)
        date_str = data.get('date')

        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Get daily schedule
        daily_schedule = DailySchedule.objects.get(date=date_obj)

        # Clear all assignments
        TourSession.objects.filter(daily_schedule=daily_schedule).update(
            assigned_guide=None,
            visitor_count=None,
            visitor_type=None,
            booking_channel=None
        )

        # Clear standby guide
        daily_schedule.standby_guide = None
        daily_schedule.is_published = False
        daily_schedule.save()

        return JsonResponse({
            'success': True,
            'message': 'All assignments cleared'
        })

    except DailySchedule.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Schedule not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["GET"])
def export_schedule_csv(request, date_str):
    """
    Export daily schedule as CSV in grid format.
    Phase 4: CSV export with multi-line cells.
    """
    import csv
    from django.http import HttpResponse

    try:
        schedule = DailySchedule.objects.get(date=date_str)
        guides = Guide.objects.filter(is_active=True).order_by('user__first_name')
        time_slots = TourTimeSlot.objects.all().order_by('start_time')

        # Create CSV response
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="schedule_{date_str}.csv"'

        # Add BOM for Excel
        response.write('\ufeff')

        writer = csv.writer(response)

        # Header row
        header = ['Time Slot'] + [
            f"{g.user.get_full_name() or g.user.username} ({g.get_guide_type_display()})"
            for g in guides
        ]
        writer.writerow(header)

        # Data rows
        for time_slot in time_slots:
            row = [f"{time_slot.start_time.strftime('%I:%M %p')} - {time_slot.end_time.strftime('%I:%M %p')}"]

            for guide in guides:
                # Check compatibility
                if not guide.can_work_timeslot(time_slot):
                    row.append("N/A")
                    continue

                # Find session
                try:
                    session = TourSession.objects.get(
                        daily_schedule=schedule,
                        time_slot=time_slot,
                        assigned_guide=guide
                    )

                    # Build multi-line cell content
                    cell_lines = [
                        guide.get_guide_type_display(),
                        str(session.visitor_count) if session.visitor_count else "",
                        session.get_visitor_type_display() if session.visitor_type else "",
                        session.get_booking_channel_display() if session.booking_channel else "",
                        session.notes if session.notes else ""
                    ]
                    cell_content = ";\n".join(cell_lines)
                    row.append(cell_content)

                except TourSession.DoesNotExist:
                    row.append("")

            writer.writerow(row)

        return response

    except DailySchedule.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'No schedule found for {date_str}'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["POST"])
def publish_schedule(request):
    """
    Publish a daily schedule (make visible to guides).
    Phase 4: Publish workflow with validation.
    """
    try:
        data = json.loads(request.body)
        date_str = data.get('date')

        schedule = DailySchedule.objects.get(date=date_str)
        service = SchedulingService()

        # Validate before publishing
        can_publish, errors = service.can_publish_schedule(schedule)

        if can_publish:
            schedule.is_published = True
            schedule.save()
            return JsonResponse({
                'success': True,
                'message': 'Schedule published successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Cannot publish: ' + '; '.join(errors),
                'errors': errors
            }, status=400)

    except DailySchedule.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'No schedule found for {date_str}'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ============================================================================
# Restaurant Staff Scheduling API Endpoints (Phase 5)
# ============================================================================

@staff_member_required
@require_http_methods(["POST"])
def restaurant_auto_assign(request):
    """
    Run auto-assignment algorithm for restaurant staff.
    Generates optimal shift pattern for a specific date.
    """
    try:
        data = json.loads(request.body)
        date_str = data.get('date')
        pattern = data.get('pattern', 'mixed')  # 'mixed' or 'all_8h'

        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Get or create daily schedule
        daily_schedule, created = DailyRestaurantSchedule.objects.get_or_create(date=date_obj)

        # Run auto-scheduler
        service = RestaurantSchedulingService()
        results = service.auto_schedule_day(daily_schedule, pattern=pattern)

        total_assigned = results['kitchen_assigned'] + results['serving_assigned']

        return JsonResponse({
            'success': True,
            'assigned_count': total_assigned,
            'kitchen_assigned': results['kitchen_assigned'],
            'serving_assigned': results['serving_assigned'],
            'total_staff': results['total_staff'],
            'unfillable_count': results['unfillable_count'],
            'errors': results.get('errors', []),
            'message': f"Assigned {results['kitchen_assigned']} kitchen and {results['serving_assigned']} serving staff (total: {results['total_staff']} staff)"
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["POST"])
def restaurant_clear_all(request):
    """
    Clear all staff shift assignments for a specific date.
    """
    try:
        data = json.loads(request.body)
        date_str = data.get('date')

        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Get daily schedule
        daily_schedule = DailyRestaurantSchedule.objects.get(date=date_obj)

        # Delete all shifts
        StaffShift.objects.filter(daily_schedule=daily_schedule).delete()

        # Unpublish
        daily_schedule.is_published = False
        daily_schedule.save()

        return JsonResponse({
            'success': True,
            'message': 'All shift assignments cleared'
        })

    except DailyRestaurantSchedule.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Schedule not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["POST"])
def restaurant_publish(request):
    """
    Publish restaurant schedule after validation.
    Makes schedule visible to staff.
    """
    try:
        data = json.loads(request.body)
        date_str = data.get('date')

        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        daily_schedule = DailyRestaurantSchedule.objects.get(date=date_obj)
        service = RestaurantSchedulingService()

        # Validate before publishing
        can_publish, errors = service.can_publish_schedule(daily_schedule)

        if can_publish:
            from django.utils import timezone
            daily_schedule.is_published = True
            daily_schedule.published_at = timezone.now()
            daily_schedule.save()

            return JsonResponse({
                'success': True,
                'message': 'Schedule published successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Cannot publish: ' + '; '.join(errors),
                'errors': errors
            }, status=400)

    except DailyRestaurantSchedule.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Schedule not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["POST"])
def restaurant_assign_shift(request):
    """
    Assign or update staff member for a specific shift.
    """
    try:
        data = json.loads(request.body)
        shift_id = data.get('shift_id')
        staff_id = data.get('staff_id')  # Can be None to unassign

        shift = StaffShift.objects.get(id=shift_id)

        if staff_id:
            staff = RestaurantStaff.objects.get(id=staff_id)

            # Validate: Check if staff is already assigned on this day
            existing_shifts = StaffShift.objects.filter(
                daily_schedule=shift.daily_schedule,
                staff=staff
            ).exclude(id=shift_id)

            if existing_shifts.exists():
                return JsonResponse({
                    'success': False,
                    'error': f'{staff.user.get_full_name()} is already assigned to another shift on this day'
                }, status=400)

            shift.staff = staff
        else:
            shift.staff = None

        shift.save()

        return JsonResponse({
            'success': True,
            'shift_id': shift.id,
            'staff_name': shift.staff.user.get_full_name() if shift.staff else None
        })

    except StaffShift.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Shift not found'
        }, status=404)
    except RestaurantStaff.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Staff member not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["GET"])
def restaurant_schedule_data(request, date_str):
    """
    Get full schedule data as JSON for a specific date.
    """
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        daily_schedule = DailyRestaurantSchedule.objects.get(date=date_obj)
        service = RestaurantSchedulingService()

        # Get shifts
        shifts = StaffShift.objects.filter(daily_schedule=daily_schedule).select_related('staff__user')

        # Get summary
        summary = service.get_schedule_summary(daily_schedule)

        # Get validation
        validation = service.validate_coverage(daily_schedule)

        shifts_data = []
        for shift in shifts:
            shifts_data.append({
                'id': shift.id,
                'staff_id': shift.staff.id if shift.staff else None,
                'staff_name': shift.staff.user.get_full_name() if shift.staff else None,
                'staff_type': shift.staff.staff_type if shift.staff else None,
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
                'duration_hours': shift.duration_hours,
                'is_full_day': shift.is_full_day
            })

        return JsonResponse({
            'success': True,
            'date': date_str,
            'is_published': daily_schedule.is_published,
            'shifts': shifts_data,
            'summary': summary,
            'validation': validation
        })

    except DailyRestaurantSchedule.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Schedule not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["GET"])
def restaurant_export_csv(request, date_str):
    """
    Export restaurant staff schedule as CSV.
    """
    import csv
    from django.http import HttpResponse

    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        daily_schedule = DailyRestaurantSchedule.objects.get(date=date_obj)
        shifts = StaffShift.objects.filter(daily_schedule=daily_schedule).select_related('staff__user').order_by('start_time')

        # Create CSV response
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="restaurant_schedule_{date_str}.csv"'

        # Add BOM for Excel
        response.write('\ufeff')

        writer = csv.writer(response)

        # Header
        writer.writerow(['Staff Name', 'Staff Type', 'Start Time', 'End Time', 'Duration (hours)', 'Shift Type'])

        # Data rows
        for shift in shifts:
            writer.writerow([
                shift.staff.user.get_full_name() if shift.staff else 'Unassigned',
                shift.staff.get_staff_type_display() if shift.staff else '',
                shift.start_time.strftime('%I:%M %p'),
                shift.end_time.strftime('%I:%M %p'),
                shift.duration_hours,
                'Full-day (8h)' if shift.is_full_day else 'Half-day (4h)'
            ])

        return response

    except DailyRestaurantSchedule.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Schedule not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

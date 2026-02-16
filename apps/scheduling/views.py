from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta, datetime, time
from apps.scheduling.models import DailySchedule, TourSession, TourTimeSlot, DailyRestaurantSchedule, StaffShift, RestaurantStaff
from apps.guides.models import Guide
from apps.scheduling.services import SchedulingService


@staff_member_required
def schedule_dashboard(request):
    """Main scheduling dashboard with links to all scheduling modules."""
    today = date.today()

    # Get today's schedules for quick stats
    tour_schedule = DailySchedule.objects.filter(date=today).first()
    restaurant_schedule = DailyRestaurantSchedule.objects.filter(date=today).first()

    # Tour guide stats
    tour_stats = {}
    if tour_schedule:
        total_sessions = TourSession.objects.filter(daily_schedule=tour_schedule).count()
        assigned_sessions = TourSession.objects.filter(
            daily_schedule=tour_schedule,
            assigned_guide__isnull=False
        ).count()
        tour_stats = {
            'total': total_sessions,
            'assigned': assigned_sessions,
            'unassigned': total_sessions - assigned_sessions,
            'published': tour_schedule.is_published
        }

    # Restaurant staff stats
    restaurant_stats = {}
    if restaurant_schedule:
        total_shifts = StaffShift.objects.filter(daily_schedule=restaurant_schedule).count()
        assigned_shifts = StaffShift.objects.filter(
            daily_schedule=restaurant_schedule,
            staff__isnull=False
        ).count()
        restaurant_stats = {
            'total': total_shifts,
            'assigned': assigned_shifts,
            'unassigned': total_shifts - assigned_shifts,
            'published': restaurant_schedule.is_published
        }

    context = {
        'today': today,
        'tour_stats': tour_stats,
        'restaurant_stats': restaurant_stats,
        'tour_schedule': tour_schedule,
        'restaurant_schedule': restaurant_schedule,
    }

    return render(request, 'scheduling/schedule_dashboard.html', context)


@staff_member_required
def schedule_overview(request):
    """Calendar-style overview of guide assignments for a specific date."""
    # Get date from query parameter or default to today
    date_str = request.GET.get('date')
    if date_str:
        try:
            view_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            view_date = date.today()
    else:
        view_date = date.today()

    # Get or create daily schedule for this date
    try:
        daily_schedule = DailySchedule.objects.get(date=view_date)
    except DailySchedule.DoesNotExist:
        daily_schedule = None

    # Get all active guides
    guides = Guide.objects.filter(is_active=True).select_related('user').order_by('user__first_name', 'user__last_name')

    # Get all time slots
    time_slots = TourTimeSlot.objects.all().order_by('start_time')

    # Build schedule grid
    # Structure: {time_slot_id: {guide_id: session_or_none}}
    schedule_grid = {}

    if daily_schedule:
        sessions = TourSession.objects.filter(
            daily_schedule=daily_schedule
        ).select_related('time_slot', 'assigned_guide')

        # Initialize grid
        for time_slot in time_slots:
            schedule_grid[time_slot.id] = {}
            for guide in guides:
                schedule_grid[time_slot.id][guide.id] = None

        # Fill in assigned sessions
        for session in sessions:
            if session.assigned_guide:
                schedule_grid[session.time_slot.id][session.assigned_guide.id] = session

    # Get feasibility information if schedule exists
    service = SchedulingService()
    feasibility_map = {}
    time_slot_feasibility = {}

    if daily_schedule:
        feasibility_map = service.get_daily_feasibility(daily_schedule)

        # For each time slot, check if it can be filled by anyone
        for time_slot in time_slots:
            # Find the session for this time slot
            session = sessions.filter(time_slot=time_slot).first()
            if session:
                can_fill, eligible = service.check_session_feasibility(session)
                time_slot_feasibility[time_slot.id] = {
                    'can_fill': can_fill,
                    'eligible_count': len(eligible),
                    'is_assigned': session.assigned_guide is not None
                }

    # Build rows for template (guides as rows, time slots as columns)
    guide_rows = []
    for guide in guides:
        row = {
            'guide': guide,
            'cells': []
        }

        for time_slot in time_slots:
            session = schedule_grid.get(time_slot.id, {}).get(guide.id) if daily_schedule else None

            # Determine cell status
            if session:
                # Guide is working this slot
                cell_status = 'working'
                cell_class = 'table-success'
                cell_text = time_slot.start_time.strftime('%I:%M %p')
            elif daily_schedule:
                # Check if guide has a break requirement or is incompatible
                if not guide.can_work_timeslot(time_slot):
                    cell_status = 'incompatible'
                    cell_class = 'table-secondary'
                    cell_text = '-'
                else:
                    # Guide could work but isn't assigned (resting)
                    cell_status = 'resting'
                    cell_class = 'table-light'
                    cell_text = '-'
            else:
                cell_status = 'no_schedule'
                cell_class = 'table-light'
                cell_text = '-'

            row['cells'].append({
                'time_slot': time_slot,
                'session': session,
                'status': cell_status,
                'class': cell_class,
                'text': cell_text,
                'feasibility': time_slot_feasibility.get(time_slot.id, {})
            })

        guide_rows.append(row)

    # Navigation dates
    prev_date = view_date - timedelta(days=1)
    next_date = view_date + timedelta(days=1)

    context = {
        'view_date': view_date,
        'daily_schedule': daily_schedule,
        'guides': guides,
        'time_slots': time_slots,
        'guide_rows': guide_rows,
        'prev_date': prev_date,
        'next_date': next_date,
        'today': date.today(),
    }

    return render(request, 'scheduling/schedule_overview.html', context)


def _calculate_cell_status(guide, slot_start_time, slot_end_time, guide_sessions):
    """
    Calculate the status of a 30-minute cell for visualization.
    Returns: (status, detail, session)

    Status can be:
    - 'tour_start': Guide starts a tour in this 30-min slot
    - 'tour_active': Guide is conducting a tour during this 30-min slot
    - 'buffer': Mandatory 30-min buffer after a tour
    - 'resting': Guide is available but not assigned

    Note: Guide type compatibility is checked separately
    """
    # Check all of this guide's tour sessions
    for session in guide_sessions:
        tour_start_time = session.time_slot.start_time
        tour_end_time = session.time_slot.end_time

        # Check if tour starts in this 30-min slot
        if tour_start_time == slot_start_time:
            return ('tour_start', 'Tour Start', session)

        # Check if this 30-min slot is during the tour
        # Tour is active if: tour_start < slot_start < tour_end
        if tour_start_time < slot_start_time < tour_end_time:
            return ('tour_active', 'On Tour', session)

        # Check if this 30-min slot is the buffer after the tour
        # Buffer is: tour_end == slot_start
        if tour_end_time == slot_start_time:
            return ('buffer', 'Buffer', session)

    # Otherwise, guide is resting
    return ('resting', 'Available', None)


@staff_member_required
def schedule_manager(request):
    """
    Unified Schedule Manager interface - editable grid view.
    Grid shows 30-minute time slots (not tour slots).
    Each tour assignment spans 4 cells: 3 for tour (1.5h) + 1 for buffer (30min).
    """
    # Get date from query parameter or default to today
    date_str = request.GET.get('date')
    if date_str:
        try:
            view_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            view_date = date.today()
    else:
        view_date = date.today()

    # Get or create daily schedule
    daily_schedule, created = DailySchedule.objects.get_or_create(date=view_date)

    # Get all active guides
    guides = Guide.objects.filter(is_active=True).select_related('user').order_by('user__first_name')

    # Get all tour time slots (for creating sessions)
    tour_time_slots = TourTimeSlot.objects.all().order_by('start_time')

    # Get all sessions for this day
    all_sessions = TourSession.objects.filter(
        daily_schedule=daily_schedule
    ).select_related('time_slot', 'assigned_guide')

    # Create sessions if they don't exist
    for time_slot in tour_time_slots:
        TourSession.objects.get_or_create(
            daily_schedule=daily_schedule,
            time_slot=time_slot
        )

    # Refresh sessions after creation
    all_sessions = TourSession.objects.filter(
        daily_schedule=daily_schedule
    ).select_related('time_slot', 'assigned_guide')

    # Build guide sessions map for quick lookup
    guide_sessions_map = {}
    for guide in guides:
        guide_sessions_map[guide.id] = list(all_sessions.filter(
            assigned_guide=guide
        ).order_by('time_slot__start_time'))

    # Generate 30-minute display slots from 10:00 AM to 10:00 PM
    # These are for display only, not actual tour slots
    # Tours start on the hour, but we show 30-min increments for buffer visualization
    display_slots = []
    current_time = time(10, 0)  # 10:00 AM (first tour starts)
    end_time = time(22, 0)  # 10:00 PM (covers last tour ending at 9:30 PM + buffer)

    while current_time < end_time:
        # Calculate slot end time (30 minutes later)
        start_dt = datetime.combine(date.today(), current_time)
        end_dt = start_dt + timedelta(minutes=30)

        display_slots.append({
            'start_time': current_time,
            'end_time': end_dt.time()
        })

        # Move to next 30-minute slot
        current_time = end_dt.time()

    # Build schedule grid with 30-minute rows
    schedule_rows = []

    for slot in display_slots:
        slot_start = slot['start_time']
        slot_end = slot['end_time']

        row = {
            'time_slot': slot,
            'cells': []
        }

        for guide in guides:
            # Get guide's sessions for the day
            guide_sessions = guide_sessions_map.get(guide.id, [])

            # Calculate cell status for this 30-min slot
            cell_status, cell_detail, related_session = _calculate_cell_status(
                guide, slot_start, slot_end, guide_sessions
            )

            # Check guide type compatibility for this slot
            # We need to check if guide can work tours that overlap this 30-min slot
            if cell_status == 'resting':  # Only check if not already assigned
                # Create a dummy time slot to check compatibility
                dummy_slot = TourTimeSlot(start_time=slot_start, end_time=slot_end)
                if not guide.can_work_timeslot(dummy_slot):
                    cell_status = 'incompatible'
                    cell_detail = 'N/A'

            # Find the session to edit (session that starts at this time)
            editable_session = None
            for session in all_sessions:
                if session.time_slot.start_time == slot_start:
                    editable_session = session
                    break

            row['cells'].append({
                'guide': guide,
                'session': editable_session,  # Session if tour starts here, else None
                'status': cell_status,
                'detail': cell_detail,
                'related_session': related_session  # The tour this cell is part of
            })

        schedule_rows.append(row)

    # Calculate statistics based on actual tour sessions
    assigned_count = all_sessions.filter(assigned_guide__isnull=False).count()
    guides_used = set(all_sessions.filter(assigned_guide__isnull=False).values_list('assigned_guide_id', flat=True))
    unassigned_count = all_sessions.filter(assigned_guide__isnull=True).count()

    # Navigation dates
    prev_date = view_date - timedelta(days=1)
    next_date = view_date + timedelta(days=1)

    context = {
        'view_date': view_date,
        'daily_schedule': daily_schedule,
        'guides': guides,
        'schedule_rows': schedule_rows,
        'prev_date': prev_date,
        'next_date': next_date,
        'today': date.today(),
        'assigned_count': assigned_count,
        'total_slots': len(tour_time_slots),  # Total tour slots (21)
        'unassigned_count': unassigned_count,
        'guides_used_count': len(guides_used),
    }

    return render(request, 'scheduling/schedule_manager.html', context)


@staff_member_required
def restaurant_schedule_manager(request):
    """
    Restaurant Staff Schedule Manager - interactive grid view.
    Shows kitchen and serving staff shifts with coverage indicators.
    """
    from apps.scheduling.models import (
        RestaurantStaff, DailyRestaurantSchedule, StaffShift
    )
    from apps.scheduling.services import RestaurantSchedulingService

    # Get date from query parameter or default to today
    date_str = request.GET.get('date')
    if date_str:
        try:
            view_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            view_date = date.today()
    else:
        view_date = date.today()

    # Get or create daily restaurant schedule
    daily_schedule, created = DailyRestaurantSchedule.objects.get_or_create(
        date=view_date
    )

    # Get all active staff
    kitchen_staff = RestaurantStaff.objects.filter(
        is_active=True,
        staff_type='kitchen'
    ).select_related('user').order_by('user__first_name')

    serving_staff = RestaurantStaff.objects.filter(
        is_active=True,
        staff_type='serving'
    ).select_related('user').order_by('user__first_name')

    # Get all shifts for this day
    all_shifts = StaffShift.objects.filter(
        daily_schedule=daily_schedule
    ).select_related('staff__user').order_by('start_time')

    kitchen_shifts = all_shifts.filter(staff__staff_type='kitchen')
    serving_shifts = all_shifts.filter(staff__staff_type='serving')

    # Get schedule summary
    service = RestaurantSchedulingService()
    summary = service.get_schedule_summary(daily_schedule)
    validation = service.validate_coverage(daily_schedule)

    # Calculate statistics
    total_shifts = all_shifts.count()
    assigned_shifts = all_shifts.filter(staff__isnull=False).count()
    unassigned_shifts = all_shifts.filter(staff__isnull=True).count()

    # Navigation dates
    prev_date = view_date - timedelta(days=1)
    next_date = view_date + timedelta(days=1)

    context = {
        'view_date': view_date,
        'daily_schedule': daily_schedule,
        'kitchen_staff': kitchen_staff,
        'serving_staff': serving_staff,
        'kitchen_shifts': kitchen_shifts,
        'serving_shifts': serving_shifts,
        'all_shifts': all_shifts,
        'prev_date': prev_date,
        'next_date': next_date,
        'today': date.today(),
        'summary': summary,
        'validation': validation,
        'total_shifts': total_shifts,
        'assigned_shifts': assigned_shifts,
        'unassigned_shifts': unassigned_shifts,
        'coverage_valid': validation['is_valid'],
    }

    return render(request, 'scheduling/restaurant_schedule_manager.html', context)


@staff_member_required
def kitchen_staff_grid(request):
    """
    Grid view for kitchen/serving staff schedule.
    Time axis: hourly from 10am to 10pm (13 hours).
    Shows which staff members are working during each hour.
    """
    # Get date from query parameter or default to today
    date_str = request.GET.get('date')
    if date_str:
        try:
            view_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            view_date = date.today()
    else:
        view_date = date.today()

    # Get or create daily restaurant schedule for this date
    try:
        daily_schedule = DailyRestaurantSchedule.objects.get(date=view_date)
    except DailyRestaurantSchedule.DoesNotExist:
        daily_schedule = None

    # Get all active restaurant staff
    kitchen_staff = RestaurantStaff.objects.filter(
        is_active=True,
        staff_type='kitchen'
    ).select_related('user').order_by('user__first_name', 'user__last_name')

    serving_staff = RestaurantStaff.objects.filter(
        is_active=True,
        staff_type='serving'
    ).select_related('user').order_by('user__first_name', 'user__last_name')

    # Generate hourly time slots from 10am to 10pm (10:00 to 22:00)
    time_slots = []
    for hour in range(10, 23):  # 10am to 10pm inclusive
        time_slots.append({
            'hour': hour,
            'display': f"{hour:02d}:00",
            'display_12h': time(hour, 0).strftime('%I:00 %p')
        })

    # Build schedule grid
    # Structure: {staff_id: {hour: shift_or_none}}
    schedule_grid = {'kitchen': {}, 'serving': {}}

    if daily_schedule:
        shifts = StaffShift.objects.filter(
            daily_schedule=daily_schedule
        ).select_related('staff')

        # Initialize grid
        for staff in kitchen_staff:
            schedule_grid['kitchen'][staff.id] = {}
            for slot in time_slots:
                schedule_grid['kitchen'][staff.id][slot['hour']] = None

        for staff in serving_staff:
            schedule_grid['serving'][staff.id] = {}
            for slot in time_slots:
                schedule_grid['serving'][staff.id][slot['hour']] = None

        # Fill in shifts
        for shift in shifts:
            if not shift.staff:
                continue

            staff_type = shift.staff.staff_type
            staff_id = shift.staff.id

            # Determine which hours this shift covers
            start_hour = shift.start_time.hour
            end_hour = shift.end_time.hour
            if shift.end_time.minute > 0:
                end_hour += 1  # Include partial hour

            # Mark all hours covered by this shift
            for hour in range(start_hour, end_hour):
                if 10 <= hour <= 22:  # Only within our display range
                    if staff_id in schedule_grid[staff_type]:
                        schedule_grid[staff_type][staff_id][hour] = shift

    # Build rows for template (Kitchen staff)
    kitchen_rows = []
    for staff in kitchen_staff:
        row = {
            'staff': staff,
            'cells': []
        }

        for slot in time_slots:
            hour = slot['hour']
            shift = schedule_grid['kitchen'].get(staff.id, {}).get(hour)

            if shift:
                # Staff is working this hour
                cell_status = 'working'
                cell_class = 'table-danger'  # Red for kitchen
                # Show shift details only at start hour
                if shift.start_time.hour == hour:
                    cell_text = f"{shift.start_time.strftime('%I:%M %p')}"
                else:
                    cell_text = '●'  # Continued shift
            elif daily_schedule:
                # Staff is not working (resting)
                cell_status = 'resting'
                cell_class = 'table-light'
                cell_text = '-'
            else:
                cell_status = 'no_schedule'
                cell_class = 'table-light'
                cell_text = '-'

            row['cells'].append({
                'status': cell_status,
                'class': cell_class,
                'text': cell_text,
                'shift': shift
            })

        kitchen_rows.append(row)

    # Build rows for template (Serving staff)
    serving_rows = []
    for staff in serving_staff:
        row = {
            'staff': staff,
            'cells': []
        }

        for slot in time_slots:
            hour = slot['hour']
            shift = schedule_grid['serving'].get(staff.id, {}).get(hour)

            if shift:
                # Staff is working this hour
                cell_status = 'working'
                cell_class = 'table-primary'  # Blue for serving
                # Show shift details only at start hour
                if shift.start_time.hour == hour:
                    cell_text = f"{shift.start_time.strftime('%I:%M %p')}"
                else:
                    cell_text = '●'  # Continued shift
            elif daily_schedule:
                # Staff is not working (resting)
                cell_status = 'resting'
                cell_class = 'table-light'
                cell_text = '-'
            else:
                cell_status = 'no_schedule'
                cell_class = 'table-light'
                cell_text = '-'

            row['cells'].append({
                'status': cell_status,
                'class': cell_class,
                'text': cell_text,
                'shift': shift
            })

        serving_rows.append(row)

    # Navigation dates
    prev_date = view_date - timedelta(days=1)
    next_date = view_date + timedelta(days=1)

    context = {
        'view_date': view_date,
        'daily_schedule': daily_schedule,
        'time_slots': time_slots,
        'kitchen_rows': kitchen_rows,
        'serving_rows': serving_rows,
        'prev_date': prev_date,
        'next_date': next_date,
        'today': date.today(),
    }

    return render(request, 'scheduling/kitchen_staff_grid.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta, datetime, time
from apps.scheduling.models import DailySchedule, TourSession, TourTimeSlot
from apps.guides.models import Guide
from apps.scheduling.services import SchedulingService


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

    # Build rows for template
    schedule_rows = []
    for time_slot in time_slots:
        row = {
            'time_slot': time_slot,
            'cells': [],
            'feasibility': time_slot_feasibility.get(time_slot.id, {})
        }

        for guide in guides:
            session = schedule_grid.get(time_slot.id, {}).get(guide.id)

            # Determine cell status
            if session:
                # Guide is working this slot
                cell_status = 'working'
                cell_class = 'table-success'
                cell_text = '✓ Working'
            elif daily_schedule:
                # Check if guide has a break requirement or is incompatible
                if not guide.can_work_timeslot(time_slot):
                    cell_status = 'incompatible'
                    cell_class = 'table-secondary'
                    cell_text = 'N/A'
                else:
                    # Guide could work but isn't assigned (resting)
                    cell_status = 'resting'
                    cell_class = 'table-light'
                    cell_text = 'Rest'
            else:
                cell_status = 'no_schedule'
                cell_class = 'table-light'
                cell_text = '-'

            row['cells'].append({
                'guide': guide,
                'session': session,
                'status': cell_status,
                'class': cell_class,
                'text': cell_text
            })

        schedule_rows.append(row)

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

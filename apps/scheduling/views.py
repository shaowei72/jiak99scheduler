from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import date, timedelta
from apps.guides.models import Guide, GuideAvailability
from apps.guides.forms import AvailabilityForm
from apps.scheduling.models import TourSession, DailySchedule


@login_required
def guide_dashboard(request):
    """Dashboard showing upcoming shifts and standby days."""
    try:
        guide = request.user.guide_profile
    except Guide.DoesNotExist:
        messages.error(request, "You are not registered as a guide.")
        return redirect('/admin/')

    today = date.today()
    next_30_days = today + timedelta(days=30)

    # Get upcoming assigned sessions (published only)
    upcoming_sessions = TourSession.objects.filter(
        assigned_guide=guide,
        daily_schedule__date__gte=today,
        daily_schedule__date__lte=next_30_days,
        daily_schedule__is_published=True
    ).select_related('daily_schedule', 'time_slot').order_by('daily_schedule__date', 'time_slot__start_time')

    # Get standby days (published only)
    standby_days = DailySchedule.objects.filter(
        standby_guide=guide,
        date__gte=today,
        date__lte=next_30_days,
        is_published=True
    ).order_by('date')

    # Get recent availability entries
    recent_availability = GuideAvailability.objects.filter(
        guide=guide,
        date__gte=today
    ).order_by('date')[:10]

    context = {
        'guide': guide,
        'upcoming_sessions': upcoming_sessions,
        'standby_days': standby_days,
        'recent_availability': recent_availability,
        'today': today,
    }

    return render(request, 'guides/dashboard.html', context)


@login_required
def mark_availability(request):
    """Form to mark availability for date ranges."""
    try:
        guide = request.user.guide_profile
    except Guide.DoesNotExist:
        messages.error(request, "You are not registered as a guide.")
        return redirect('/admin/')

    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            is_available = form.cleaned_data['is_available'] == 'True'
            notes = form.cleaned_data['notes']

            # Create or update availability for each date in range
            created_count = 0
            updated_count = 0
            current_date = start_date

            while current_date <= end_date:
                availability, created = GuideAvailability.objects.update_or_create(
                    guide=guide,
                    date=current_date,
                    defaults={
                        'is_available': is_available,
                        'notes': notes
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

                current_date += timedelta(days=1)

            status = "available" if is_available else "unavailable"
            messages.success(
                request,
                f"Marked as {status} for {created_count + updated_count} day(s) "
                f"({created_count} new, {updated_count} updated)"
            )
            return redirect('guide_dashboard')
    else:
        form = AvailabilityForm()

    # Get existing availability for calendar display
    today = date.today()
    max_date = today + timedelta(days=90)
    existing_availability = GuideAvailability.objects.filter(
        guide=guide,
        date__gte=today,
        date__lte=max_date
    ).order_by('date')

    context = {
        'guide': guide,
        'form': form,
        'existing_availability': existing_availability,
    }

    return render(request, 'guides/availability_form.html', context)


@login_required
def my_schedule(request):
    """View assigned shifts (published schedules only)."""
    try:
        guide = request.user.guide_profile
    except Guide.DoesNotExist:
        messages.error(request, "You are not registered as a guide.")
        return redirect('/admin/')

    today = date.today()

    # Get week offset from query parameter (default to current week)
    week_offset = int(request.GET.get('week', 0))
    start_of_week = today + timedelta(days=-today.weekday(), weeks=week_offset)
    end_of_week = start_of_week + timedelta(days=6)

    # Get sessions for the week (published only)
    sessions = TourSession.objects.filter(
        assigned_guide=guide,
        daily_schedule__date__gte=start_of_week,
        daily_schedule__date__lte=end_of_week,
        daily_schedule__is_published=True
    ).select_related('daily_schedule', 'time_slot').order_by('daily_schedule__date', 'time_slot__start_time')

    # Get standby days for the week (published only)
    standby_days = DailySchedule.objects.filter(
        standby_guide=guide,
        date__gte=start_of_week,
        date__lte=end_of_week,
        is_published=True
    ).order_by('date')

    # Organize sessions by date
    schedule_by_date = {}
    for session in sessions:
        session_date = session.daily_schedule.date
        if session_date not in schedule_by_date:
            schedule_by_date[session_date] = []
        schedule_by_date[session_date].append(session)

    # Create list of days in week with sessions
    week_days = []
    current_date = start_of_week
    while current_date <= end_of_week:
        is_standby = any(s.date == current_date for s in standby_days)
        day_sessions = schedule_by_date.get(current_date, [])

        week_days.append({
            'date': current_date,
            'is_today': current_date == today,
            'is_standby': is_standby,
            'sessions': day_sessions,
        })
        current_date += timedelta(days=1)

    context = {
        'guide': guide,
        'week_days': week_days,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'week_offset': week_offset,
        'prev_week': week_offset - 1,
        'next_week': week_offset + 1,
    }

    return render(request, 'guides/my_schedule.html', context)


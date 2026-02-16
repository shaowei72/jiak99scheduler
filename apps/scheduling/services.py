"""
Business logic and validation for tour scheduling.
"""
from datetime import datetime, time, timedelta, date
from typing import List, Dict
from django.db.models import Q
from apps.guides.models import Guide, GuideAvailability
from apps.scheduling.models import TourTimeSlot, TourSession, DailySchedule


class SchedulingService:
    """Service class for scheduling operations and validations."""

    def generate_tour_time_slots(self):
        """Generate all tour time slots (10:00am-9:30pm, on the hour, 1.5-hour tours)."""
        slots_created = 0
        start_hour = 10  # Start at 10:00 AM
        tour_duration_minutes = 90  # 1.5 hours

        # Generate slots from 10:00am to 8:00pm (last tour starts at 8pm, ends at 9:30pm)
        # Tours start on the hour: 10am, 11am, 12pm, 1pm, 2pm, 3pm, 4pm, 5pm, 6pm, 7pm, 8pm
        for hour in range(start_hour, 21):  # 10 to 20 (8pm)
            current_time = time(hour, 0)  # On the hour

            # Calculate end time (1.5 hours later)
            start_dt = datetime.combine(date.today(), current_time)
            end_dt = start_dt + timedelta(minutes=tour_duration_minutes)

            slot, created = TourTimeSlot.objects.get_or_create(
                start_time=current_time,
                end_time=end_dt.time(),
                defaults={'duration_minutes': tour_duration_minutes}
            )

            if created:
                slots_created += 1

        return slots_created

    def generate_sessions_for_date(self, target_date):
        """Generate tour sessions for a specific date."""
        # Get or create daily schedule
        daily_schedule, created = DailySchedule.objects.get_or_create(date=target_date)

        # Get all time slots
        time_slots = TourTimeSlot.objects.all()

        sessions_created = 0
        for time_slot in time_slots:
            session, created = TourSession.objects.get_or_create(
                daily_schedule=daily_schedule,
                time_slot=time_slot
            )
            if created:
                sessions_created += 1

        return sessions_created, daily_schedule

    def generate_sessions_for_month(self, year, month):
        """Generate sessions for all days in a month."""
        # Validate that we're generating at least 2 weeks in advance
        target_date = date(year, month, 1)
        two_weeks_ahead = date.today() + timedelta(days=14)

        if target_date < two_weeks_ahead:
            raise ValueError(
                f"Schedules must be created at least 2 weeks in advance. "
                f"Please create schedules starting from {two_weeks_ahead.strftime('%B %Y')}."
            )

        # Get last day of month
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        total_sessions = 0
        schedules_created = []

        current_date = target_date
        while current_date <= last_day:
            sessions_count, daily_schedule = self.generate_sessions_for_date(current_date)
            total_sessions += sessions_count
            schedules_created.append(daily_schedule)
            current_date += timedelta(days=1)

        return total_sessions, schedules_created

    def validate_session_assignment(self, session):
        """
        Validate a tour session assignment.
        Returns a list of validation error messages.
        """
        errors = []

        if not session.assigned_guide:
            return errors

        guide = session.assigned_guide
        session_date = session.daily_schedule.date
        time_slot = session.time_slot

        # 1. Check guide type compatibility
        if not guide.can_work_timeslot(time_slot):
            guide_type = guide.get_guide_type_display()
            errors.append(
                f"{guide_type} guide cannot work {time_slot} time slot"
            )

        # 2. Check availability
        try:
            availability = GuideAvailability.objects.get(
                guide=guide,
                date=session_date
            )
            if not availability.is_available:
                errors.append(f"Guide marked as unavailable on {session_date}")
        except GuideAvailability.DoesNotExist:
            # If no availability record exists, assume available
            pass

        # 3. Check for 1-hour break requirement
        break_errors = self._check_break_requirement(session)
        errors.extend(break_errors)

        return errors

    def _check_break_requirement(self, session):
        """
        Check if guide has at least 30 minutes break between tours.
        Returns list of error messages.
        """
        errors = []

        if not session.assigned_guide:
            return errors

        guide = session.assigned_guide
        session_date = session.daily_schedule.date
        current_slot = session.time_slot

        # Get all other sessions for this guide on the same day
        other_sessions = TourSession.objects.filter(
            daily_schedule__date=session_date,
            assigned_guide=guide
        ).exclude(id=session.id)

        for other_session in other_sessions:
            other_slot = other_session.time_slot

            # Calculate time gap between sessions
            if current_slot.end_time <= other_slot.start_time:
                # Current session ends before other starts
                gap = self._calculate_time_gap(current_slot.end_time, other_slot.start_time)
            elif other_slot.end_time <= current_slot.start_time:
                # Other session ends before current starts
                gap = self._calculate_time_gap(other_slot.end_time, current_slot.start_time)
            else:
                # Sessions overlap
                errors.append(
                    f"Session overlaps with another assigned tour at {other_slot}"
                )
                continue

            # Check if gap is less than 30 minutes
            if gap < 30:
                errors.append(
                    f"Less than 30-minute break between {current_slot} and {other_slot} "
                    f"(gap: {gap} minutes)"
                )

        return errors

    def _calculate_time_gap(self, end_time, start_time):
        """Calculate gap in minutes between two times."""
        end_dt = datetime.combine(date.today(), end_time)
        start_dt = datetime.combine(date.today(), start_time)
        return int((start_dt - end_dt).total_seconds() / 60)

    def validate_daily_schedule(self, daily_schedule):
        """
        Validate entire daily schedule.
        Returns dictionary with validation results.
        """
        errors = {
            'general': [],
            'sessions': {}
        }

        # Check if standby guide is assigned
        if not daily_schedule.standby_guide:
            errors['general'].append("No standby guide assigned")

        # Check if standby guide is available
        if daily_schedule.standby_guide:
            try:
                availability = GuideAvailability.objects.get(
                    guide=daily_schedule.standby_guide,
                    date=daily_schedule.date
                )
                if not availability.is_available:
                    errors['general'].append("Standby guide marked as unavailable")
            except GuideAvailability.DoesNotExist:
                pass

        # Validate each session
        for session in daily_schedule.sessions.all():
            session_errors = self.validate_session_assignment(session)
            if session_errors:
                errors['sessions'][session.id] = session_errors

        # Check if all sessions are assigned (for publishing)
        unassigned_count = daily_schedule.sessions.filter(
            assigned_guide__isnull=True
        ).count()
        if unassigned_count > 0:
            errors['general'].append(
                f"{unassigned_count} session(s) not assigned to any guide"
            )

        return errors

    def get_available_guides_for_session(self, session):
        """
        Get list of guides who can work a specific session.
        Returns queryset of eligible guides.
        """
        time_slot = session.time_slot
        session_date = session.daily_schedule.date

        # Start with all active guides
        eligible_guides = Guide.objects.filter(is_active=True)

        # Filter by guide type compatibility
        eligible_guide_ids = []
        for guide in eligible_guides:
            if guide.can_work_timeslot(time_slot):
                eligible_guide_ids.append(guide.id)

        eligible_guides = Guide.objects.filter(id__in=eligible_guide_ids)

        # Filter by availability
        unavailable_guide_ids = GuideAvailability.objects.filter(
            date=session_date,
            is_available=False
        ).values_list('guide_id', flat=True)

        eligible_guides = eligible_guides.exclude(id__in=unavailable_guide_ids)

        # Filter guides who already have conflicting sessions or break violations
        valid_guide_ids = []
        for guide in eligible_guides:
            # Temporarily assign guide to check validation
            temp_session = TourSession(
                daily_schedule=session.daily_schedule,
                time_slot=time_slot,
                assigned_guide=guide
            )
            validation_errors = self.validate_session_assignment(temp_session)
            if not validation_errors:
                valid_guide_ids.append(guide.id)

        return Guide.objects.filter(id__in=valid_guide_ids)

    def can_publish_schedule(self, daily_schedule):
        """
        Check if a schedule can be published.
        Returns tuple (can_publish: bool, errors: list).
        """
        errors = self.validate_daily_schedule(daily_schedule)

        can_publish = (
            not errors['general'] and
            not errors['sessions'] and
            daily_schedule.standby_guide is not None
        )

        all_errors = errors['general'].copy()
        for session_id, session_errors in errors['sessions'].items():
            all_errors.extend(session_errors)

        return can_publish, all_errors

    def _check_consecutive_tours(self, guide_sessions, new_session):
        """
        Check how many consecutive tours a guide would have if we add new_session.
        Returns number of consecutive tours ending with new_session.
        """
        if not guide_sessions:
            return 1

        # Sort by start time
        sorted_sessions = sorted(guide_sessions + [new_session], key=lambda s: s.time_slot.start_time)

        # Find position of new session
        new_pos = next(i for i, s in enumerate(sorted_sessions) if s == new_session)

        consecutive = 1
        # Count backwards from new_session
        for i in range(new_pos - 1, -1, -1):
            prev_session = sorted_sessions[i]
            curr_session = sorted_sessions[i + 1]

            # Check if they're consecutive (curr starts when prev ends + 30-min buffer)
            gap = self._calculate_time_gap(prev_session.time_slot.end_time, curr_session.time_slot.start_time)
            if gap == 30:  # Only 30-min buffer between them
                consecutive += 1
            else:
                break  # There's a larger break, not consecutive

        return consecutive

    def _has_one_hour_break(self, guide_sessions):
        """
        Check if guide has a continuous 1-hour break (not counting 30-min buffers).
        Returns True if guide has at least one gap of 90+ minutes between tours.

        The 90 minutes accounts for:
        - 30 minutes: mandatory buffer after first tour
        - 60 minutes: actual continuous break
        """
        if len(guide_sessions) <= 1:
            return True  # No break needed for 0-1 tours

        sorted_sessions = sorted(guide_sessions, key=lambda s: s.time_slot.start_time)

        for i in range(len(sorted_sessions) - 1):
            gap = self._calculate_time_gap(
                sorted_sessions[i].time_slot.end_time,
                sorted_sessions[i + 1].time_slot.start_time
            )
            if gap >= 90:  # 30-min buffer + 60-min break
                return True

        return False

    def auto_schedule_day(self, daily_schedule, assign_standby=True):
        """
        Automatically assign guides to all sessions for a day.
        Optimizes for maximum coverage with minimal guides.

        Constraints:
        1. Each tour is 1.5 hours with 30-min buffer
        2. Each guide must have a continuous 1-hour break (90-min gap: 30-min buffer + 60-min break) for 3+ tours
        3. No more than 2 consecutive tours per guide
        4. Maximum 4 tours per guide per day

        Returns: dict with results including:
            - assigned_count: number of sessions assigned
            - unfillable_count: number of sessions that cannot be filled
            - unfillable_sessions: list of session IDs that cannot be filled
        """
        results = {
            'assigned_count': 0,
            'unfillable_count': 0,
            'unfillable_sessions': [],
            'errors': []
        }

        # Get all unassigned sessions for this day, ordered by time
        sessions = TourSession.objects.filter(
            daily_schedule=daily_schedule,
            assigned_guide__isnull=True
        ).select_related('time_slot').order_by('time_slot__start_time')

        if not sessions:
            results['errors'].append("No unassigned sessions found")
            return results

        # Get all active guides
        all_guides = list(Guide.objects.filter(is_active=True))

        if not all_guides:
            results['errors'].append("No active guides available")
            return results

        # Track guide assignments to manage workload
        guide_assignments = {guide.id: [] for guide in all_guides}

        # Build list of (session, eligible_guides) sorted by constraint
        session_options = []
        for session in sessions:
            eligible = self.get_available_guides_for_session(session)
            eligible_list = list(eligible)
            session_options.append({
                'session': session,
                'eligible_guides': eligible_list,
                'count': len(eligible_list)
            })

        # Sort by number of eligible guides (most constrained first)
        session_options.sort(key=lambda x: x['count'])

        # Assign guides using strategy to MINIMIZE total guides used
        # Key principle: Maximize each guide's utilization before using another guide
        for option in session_options:
            session = option['session']
            eligible_guides = option['eligible_guides']

            if not eligible_guides:
                # Cannot fill this slot
                results['unfillable_count'] += 1
                results['unfillable_sessions'].append(session.id)
                continue

            # Filter to only guides who can actually take this session (re-validate + new constraints)
            valid_guides = []
            for guide in eligible_guides:
                temp_session = TourSession(
                    id=session.id,
                    daily_schedule=session.daily_schedule,
                    time_slot=session.time_slot,
                    assigned_guide=guide
                )

                # Check basic validation (guide type, availability, 30-min buffer)
                validation_errors = self.validate_session_assignment(temp_session)
                if validation_errors:
                    continue

                # Get guide's currently assigned sessions
                guide_current_sessions = []
                for sess_id in guide_assignments[guide.id]:
                    try:
                        guide_current_sessions.append(TourSession.objects.get(id=sess_id))
                    except TourSession.DoesNotExist:
                        pass

                # CONSTRAINT 1: Max 4 tours per guide per day
                if len(guide_current_sessions) >= 4:
                    continue  # Guide already has 4 tours (at maximum)

                # CONSTRAINT 2: Check consecutive tours limit (max 2)
                consecutive = self._check_consecutive_tours(guide_current_sessions, temp_session)
                if consecutive > 2:
                    continue  # Would exceed 2 consecutive tours

                # CONSTRAINT 3: Check 1-hour break requirement (90-min gap)
                # If guide has 3+ tours, they must have a 90-min gap (30-min buffer + 60-min break)
                if len(guide_current_sessions) >= 2:
                    # Check if adding this session would still allow for required break
                    future_sessions = guide_current_sessions + [temp_session]
                    has_break = self._has_one_hour_break(future_sessions)

                    # If no 90-min gap yet and would have 3+ tours, reject this assignment
                    if not has_break and len(future_sessions) >= 3:
                        continue  # Would have 3+ tours without required 90-min gap

                valid_guides.append(guide)

            if not valid_guides:
                # No valid guide found
                results['unfillable_count'] += 1
                results['unfillable_sessions'].append(session.id)
                continue

            # Separate into guides already working vs not working
            guides_with_work = [g for g in valid_guides if len(guide_assignments[g.id]) > 0]
            guides_without_work = [g for g in valid_guides if len(guide_assignments[g.id]) == 0]

            # PRIORITY 1: Use a guide who's already working today (maximize their utilization)
            # But prefer guides who haven't hit the consecutive limit yet
            if guides_with_work:
                # Sort by: (has room for more tours, number of assignments)
                def guide_priority(g):
                    guide_sessions = [TourSession.objects.get(id=sid) for sid in guide_assignments[g.id]]
                    temp_s = TourSession(
                        daily_schedule=session.daily_schedule,
                        time_slot=session.time_slot,
                        assigned_guide=g
                    )
                    consecutive = self._check_consecutive_tours(guide_sessions, temp_s)
                    # Prioritize guides who aren't at consecutive limit, then by assignment count
                    return (consecutive < 2, len(guide_assignments[g.id]))

                best_guide = max(guides_with_work, key=guide_priority)
            # PRIORITY 2: Only use a new guide if no working guide can take it
            elif guides_without_work:
                best_guide = guides_without_work[0]
            else:
                best_guide = None

            if best_guide:
                # Assign the guide
                session.assigned_guide = best_guide
                session.save()
                guide_assignments[best_guide.id].append(session.id)
                results['assigned_count'] += 1
            else:
                # Should not reach here, but handle it
                results['unfillable_count'] += 1
                results['unfillable_sessions'].append(session.id)

        # Optionally assign standby guide (guide with fewest assignments)
        if assign_standby and not daily_schedule.standby_guide:
            # Find guide with least assignments who is available
            available_guides = [g for g in all_guides if len(guide_assignments[g.id]) < len(sessions)]

            # Check availability
            available_on_date = []
            for guide in available_guides:
                try:
                    avail = GuideAvailability.objects.get(
                        guide=guide,
                        date=daily_schedule.date
                    )
                    if avail.is_available:
                        available_on_date.append(guide)
                except GuideAvailability.DoesNotExist:
                    # No record means available
                    available_on_date.append(guide)

            if available_on_date:
                # Choose guide with fewest assignments
                standby = min(available_on_date, key=lambda g: len(guide_assignments[g.id]))
                daily_schedule.standby_guide = standby
                daily_schedule.save()

        return results

    def check_session_feasibility(self, session):
        """
        Check if a session can be filled by any guide.
        Returns: (can_fill: bool, eligible_guides: list)
        """
        eligible_guides = self.get_available_guides_for_session(session)
        eligible_list = list(eligible_guides)
        return len(eligible_list) > 0, eligible_list

    def get_daily_feasibility(self, daily_schedule):
        """
        Get feasibility status for all sessions in a day.
        Returns: dict with session_id -> (can_fill: bool, eligible_count: int)
        """
        feasibility = {}
        sessions = daily_schedule.sessions.all()

        for session in sessions:
            can_fill, eligible = self.check_session_feasibility(session)
            feasibility[session.id] = {
                'can_fill': can_fill,
                'eligible_count': len(eligible),
                'is_assigned': session.assigned_guide is not None
            }

        return feasibility


# ============================================================================
# RESTAURANT STAFF SCHEDULING SERVICE
# ============================================================================

class RestaurantSchedulingService:
    """Service class for restaurant staff scheduling operations."""

    # Optimal shift patterns (Pattern A: Mixed 4h + 8h shifts)
    SHIFT_PATTERN_MIXED = [
        {'start': time(10, 0), 'end': time(18, 0), 'duration': 8},  # Full day - opening
        {'start': time(10, 0), 'end': time(14, 0), 'duration': 4},  # Half day - lunch rush
        {'start': time(13, 30), 'end': time(21, 30), 'duration': 8},  # Full day - closing
        {'start': time(17, 30), 'end': time(21, 30), 'duration': 4},  # Half day - dinner rush
    ]

    # Alternative pattern (Pattern B: All 8h shifts - simpler but less efficient)
    SHIFT_PATTERN_ALL_8H = [
        {'start': time(10, 0), 'end': time(18, 0), 'duration': 8},
        {'start': time(10, 0), 'end': time(18, 0), 'duration': 8},
        {'start': time(13, 30), 'end': time(21, 30), 'duration': 8},
        {'start': time(13, 30), 'end': time(21, 30), 'duration': 8},
    ]

    def generate_shifts_for_date(self, target_date):
        """Generate shift templates for a specific date (without assignment)."""
        from apps.scheduling.models import DailyRestaurantSchedule, StaffShift

        # Get or create daily schedule
        daily_schedule, created = DailyRestaurantSchedule.objects.get_or_create(
            date=target_date
        )

        shifts_created = 0

        # Create shifts for kitchen staff (using mixed pattern)
        for pattern in self.SHIFT_PATTERN_MIXED:
            shift, created = StaffShift.objects.get_or_create(
                daily_schedule=daily_schedule,
                start_time=pattern['start'],
                end_time=pattern['end'],
                duration_hours=pattern['duration'],
                staff=None  # Unassigned
            )
            if created:
                shifts_created += 1

        # Create shifts for serving staff (using mixed pattern)
        for pattern in self.SHIFT_PATTERN_MIXED:
            shift, created = StaffShift.objects.get_or_create(
                daily_schedule=daily_schedule,
                start_time=pattern['start'],
                end_time=pattern['end'],
                duration_hours=pattern['duration'],
                staff=None  # Unassigned
            )
            if created:
                shifts_created += 1

        return shifts_created, daily_schedule

    def get_available_staff(self, target_date, staff_type):
        """
        Get available staff for a specific date and type.

        Args:
            target_date: Date to check availability
            staff_type: 'kitchen' or 'serving'

        Returns:
            QuerySet of available RestaurantStaff
        """
        from apps.scheduling.models import RestaurantStaff, StaffAvailability

        # Get all active staff of this type
        staff_qs = RestaurantStaff.objects.filter(
            is_active=True,
            staff_type=staff_type
        )

        # Exclude staff marked as unavailable
        unavailable_staff_ids = StaffAvailability.objects.filter(
            date=target_date,
            is_available=False
        ).values_list('staff_id', flat=True)

        staff_qs = staff_qs.exclude(id__in=unavailable_staff_ids)

        # Exclude staff already assigned to a shift on this date
        from apps.scheduling.models import StaffShift
        assigned_staff_ids = StaffShift.objects.filter(
            daily_schedule__date=target_date,
            staff__isnull=False
        ).values_list('staff_id', flat=True)

        staff_qs = staff_qs.exclude(id__in=assigned_staff_ids)

        return staff_qs.order_by('user__first_name', 'user__last_name')

    def auto_schedule_day(self, daily_schedule, pattern='mixed'):
        """
        Auto-assign staff to all shifts for a day.

        Optimizes for minimum staff count while maintaining coverage.

        Args:
            daily_schedule: DailyRestaurantSchedule instance
            pattern: 'mixed' (default) or 'all_8h'

        Returns:
            dict with results:
                - kitchen_assigned: number of kitchen staff assigned
                - serving_assigned: number of serving staff assigned
                - total_staff: total staff assigned
                - unfillable_count: shifts that couldn't be filled
                - errors: list of error messages
        """
        from apps.scheduling.models import StaffShift, RestaurantStaff

        results = {
            'kitchen_assigned': 0,
            'serving_assigned': 0,
            'total_staff': 0,
            'unfillable_count': 0,
            'unfillable_shifts': [],
            'errors': []
        }

        target_date = daily_schedule.date

        # Select shift pattern
        if pattern == 'all_8h':
            shift_patterns = self.SHIFT_PATTERN_ALL_8H
        else:
            shift_patterns = self.SHIFT_PATTERN_MIXED

        # Clear existing assignments for this day
        StaffShift.objects.filter(daily_schedule=daily_schedule).delete()

        # Get all available kitchen staff
        available_kitchen_staff = list(self.get_available_staff(target_date, 'kitchen'))

        if len(available_kitchen_staff) < 4:
            results['errors'].append(
                f"Insufficient kitchen staff: need 4, have {len(available_kitchen_staff)}"
            )
            results['unfillable_count'] += (4 - len(available_kitchen_staff))

        # Assign kitchen staff (one staff per shift, no overlaps)
        kitchen_staff_used = set()
        for i, pattern_def in enumerate(shift_patterns):
            # Find next available kitchen staff
            assigned = False
            for staff in available_kitchen_staff:
                if staff.id not in kitchen_staff_used:
                    StaffShift.objects.create(
                        daily_schedule=daily_schedule,
                        staff=staff,
                        start_time=pattern_def['start'],
                        end_time=pattern_def['end'],
                        duration_hours=pattern_def['duration']
                    )
                    kitchen_staff_used.add(staff.id)
                    results['kitchen_assigned'] += 1
                    assigned = True
                    break

            if not assigned:
                # Create unassigned shift
                StaffShift.objects.create(
                    daily_schedule=daily_schedule,
                    staff=None,
                    start_time=pattern_def['start'],
                    end_time=pattern_def['end'],
                    duration_hours=pattern_def['duration']
                )
                results['unfillable_shifts'].append({
                    'type': 'kitchen',
                    'start': pattern_def['start'],
                    'end': pattern_def['end']
                })

        # Get all available serving staff
        available_serving_staff = list(self.get_available_staff(target_date, 'serving'))

        if len(available_serving_staff) < 4:
            results['errors'].append(
                f"Insufficient serving staff: need 4, have {len(available_serving_staff)}"
            )
            results['unfillable_count'] += (4 - len(available_serving_staff))

        # Assign serving staff (one staff per shift, no overlaps)
        serving_staff_used = set()
        for i, pattern_def in enumerate(shift_patterns):
            # Find next available serving staff
            assigned = False
            for staff in available_serving_staff:
                if staff.id not in serving_staff_used:
                    StaffShift.objects.create(
                        daily_schedule=daily_schedule,
                        staff=staff,
                        start_time=pattern_def['start'],
                        end_time=pattern_def['end'],
                        duration_hours=pattern_def['duration']
                    )
                    serving_staff_used.add(staff.id)
                    results['serving_assigned'] += 1
                    assigned = True
                    break

            if not assigned:
                # Create unassigned shift
                StaffShift.objects.create(
                    daily_schedule=daily_schedule,
                    staff=None,
                    start_time=pattern_def['start'],
                    end_time=pattern_def['end'],
                    duration_hours=pattern_def['duration']
                )
                results['unfillable_shifts'].append({
                    'type': 'serving',
                    'start': pattern_def['start'],
                    'end': pattern_def['end']
                })

        results['total_staff'] = results['kitchen_assigned'] + results['serving_assigned']

        return results

    def validate_coverage(self, daily_schedule):
        """
        Validate that minimum coverage (2 kitchen + 2 serving) is met at all times.

        Args:
            daily_schedule: DailyRestaurantSchedule instance

        Returns:
            dict with validation results:
                - is_valid: True if coverage requirements met
                - gaps: list of time periods with insufficient coverage
                - coverage_by_hour: dict of hour -> {kitchen: count, serving: count}
        """
        from apps.scheduling.models import StaffShift

        # Operating hours: 10:00 AM - 9:30 PM
        # Check coverage for each 30-minute period

        validation = {
            'is_valid': True,
            'gaps': [],
            'coverage_by_hour': {}
        }

        # Get all assigned shifts for this day
        shifts = StaffShift.objects.filter(
            daily_schedule=daily_schedule,
            staff__isnull=False
        ).select_related('staff')

        # Check coverage for each half-hour period
        # Operating hours: 10:00 AM - 9:30 PM
        # Check coverage up to 9:00 PM (last 30-min period before closing)
        current_time = time(10, 0)
        end_time = time(21, 0)  # Check up to 9:00 PM (not including 9:30 PM closing time)

        while current_time <= end_time:
            # Count kitchen and serving staff working at this time
            kitchen_count = 0
            serving_count = 0

            for shift in shifts:
                # Check if this shift covers current_time
                if shift.start_time <= current_time < shift.end_time:
                    if shift.staff.staff_type == 'kitchen':
                        kitchen_count += 1
                    elif shift.staff.staff_type == 'serving':
                        serving_count += 1

            # Store coverage
            time_key = current_time.strftime('%H:%M')
            validation['coverage_by_hour'][time_key] = {
                'kitchen': kitchen_count,
                'serving': serving_count
            }

            # Check if minimum coverage met
            if kitchen_count < 2 or serving_count < 2:
                validation['is_valid'] = False
                validation['gaps'].append({
                    'time': time_key,
                    'kitchen': kitchen_count,
                    'serving': serving_count,
                    'missing_kitchen': max(0, 2 - kitchen_count),
                    'missing_serving': max(0, 2 - serving_count)
                })

            # Move to next 30-minute period
            current_dt = datetime.combine(date.today(), current_time)
            next_dt = current_dt + timedelta(minutes=30)
            current_time = next_dt.time()

            # Stop at 9:30 PM
            if current_time > time(21, 30):
                break

        return validation

    def get_schedule_summary(self, daily_schedule):
        """
        Get a summary of the schedule for a specific day.

        Returns:
            dict with summary statistics
        """
        from apps.scheduling.models import StaffShift

        shifts = StaffShift.objects.filter(
            daily_schedule=daily_schedule
        ).select_related('staff')

        summary = {
            'total_shifts': shifts.count(),
            'assigned_shifts': shifts.filter(staff__isnull=False).count(),
            'unassigned_shifts': shifts.filter(staff__isnull=True).count(),
            'kitchen_staff': shifts.filter(
                staff__staff_type='kitchen',
                staff__isnull=False
            ).values('staff').distinct().count(),
            'serving_staff': shifts.filter(
                staff__staff_type='serving',
                staff__isnull=False
            ).values('staff').distinct().count(),
            'total_staff': shifts.filter(
                staff__isnull=False
            ).values('staff').distinct().count(),
            'full_day_shifts': shifts.filter(duration_hours=8).count(),
            'half_day_shifts': shifts.filter(duration_hours=4).count(),
            'total_hours': sum(shift.duration_hours for shift in shifts if shift.staff),
        }

        # Add coverage validation
        validation = self.validate_coverage(daily_schedule)
        summary['coverage_valid'] = validation['is_valid']
        summary['coverage_gaps'] = len(validation['gaps'])

        return summary

    def can_publish_schedule(self, daily_schedule):
        """
        Check if a schedule can be published.

        Returns:
            tuple (can_publish: bool, errors: list)
        """
        errors = []

        # Check coverage
        validation = self.validate_coverage(daily_schedule)
        if not validation['is_valid']:
            for gap in validation['gaps']:
                errors.append(
                    f"Insufficient coverage at {gap['time']}: "
                    f"Kitchen: {gap['kitchen']}/2, Serving: {gap['serving']}/2"
                )

        # Check for unassigned shifts
        from apps.scheduling.models import StaffShift
        unassigned = StaffShift.objects.filter(
            daily_schedule=daily_schedule,
            staff__isnull=True
        ).count()

        if unassigned > 0:
            errors.append(f"{unassigned} shift(s) not assigned to any staff")

        can_publish = len(errors) == 0

        return can_publish, errors

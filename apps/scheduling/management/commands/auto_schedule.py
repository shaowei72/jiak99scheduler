from django.core.management.base import BaseCommand, CommandError
from apps.scheduling.services import SchedulingService
from apps.scheduling.models import DailySchedule
from datetime import date, datetime
import calendar


class Command(BaseCommand):
    help = 'Automatically assign guides to tour sessions for a specific date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date in YYYY-MM-DD format (defaults to today)'
        )
        parser.add_argument(
            '--assign-standby',
            action='store_true',
            default=True,
            help='Also assign standby guide (default: True)'
        )
        parser.add_argument(
            '--no-assign-standby',
            action='store_false',
            dest='assign_standby',
            help='Do not assign standby guide'
        )

    def handle(self, *args, **options):
        # Parse date
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError("Invalid date format. Use YYYY-MM-DD")
        else:
            target_date = date.today()

        assign_standby = options['assign_standby']

        self.stdout.write(f"Auto-scheduling guides for {target_date}...")

        # Get or create daily schedule
        try:
            daily_schedule = DailySchedule.objects.get(date=target_date)
        except DailySchedule.DoesNotExist:
            raise CommandError(
                f"No schedule found for {target_date}. "
                f"Create sessions first using: python manage.py create_monthly_schedule"
            )

        # Run auto-scheduler
        service = SchedulingService()
        results = service.auto_schedule_day(daily_schedule, assign_standby=assign_standby)

        # Calculate guide utilization
        from apps.scheduling.models import TourSession
        from apps.guides.models import Guide

        sessions_by_guide = {}
        assigned_sessions = TourSession.objects.filter(
            daily_schedule=daily_schedule,
            assigned_guide__isnull=False
        ).select_related('assigned_guide')

        for session in assigned_sessions:
            guide_id = session.assigned_guide.id
            if guide_id not in sessions_by_guide:
                sessions_by_guide[guide_id] = []
            sessions_by_guide[guide_id].append(session)

        guides_used = len(sessions_by_guide)
        total_guides = Guide.objects.filter(is_active=True).count()

        # Display results
        self.stdout.write("\n" + "="*60)
        self.stdout.write("AUTO-SCHEDULING RESULTS (OPTIMIZED)")
        self.stdout.write("="*60)

        if results['assigned_count'] > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"+ Successfully assigned {results['assigned_count']} session(s)"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"+ Guides used: {guides_used} out of {total_guides} "
                    f"(Utilization optimized!)"
                )
            )

            # Show per-guide breakdown
            if sessions_by_guide:
                self.stdout.write("\nPer-guide assignments:")
                sorted_guides = sorted(
                    sessions_by_guide.items(),
                    key=lambda x: len(x[1]),
                    reverse=True
                )
                for guide_id, sessions_list in sorted_guides:
                    guide = Guide.objects.get(id=guide_id)
                    self.stdout.write(
                        f"  - {guide.user.username}: {len(sessions_list)} tours"
                    )

        if results['unfillable_count'] > 0:
            self.stdout.write(
                self.style.ERROR(
                    f"- Could not fill {results['unfillable_count']} session(s) "
                    f"(no eligible guides available)"
                )
            )

        if results['errors']:
            self.stdout.write("\nErrors:")
            for error in results['errors']:
                self.stdout.write(self.style.ERROR(f"  - {error}"))

        # Show unfillable sessions details
        if results['unfillable_sessions']:
            self.stdout.write("\nUnfillable sessions:")
            from apps.scheduling.models import TourSession
            for session_id in results['unfillable_sessions']:
                try:
                    session = TourSession.objects.get(id=session_id)
                    self.stdout.write(
                        self.style.WARNING(
                            f"  - {session.time_slot} (no eligible guides)"
                        )
                    )
                except TourSession.DoesNotExist:
                    pass

        # Show standby assignment
        daily_schedule.refresh_from_db()
        if daily_schedule.standby_guide:
            self.stdout.write(
                f"\n+ Standby guide: {daily_schedule.standby_guide.user.get_full_name()}"
            )
        else:
            self.stdout.write(
                self.style.WARNING("\n⚠ No standby guide assigned")
            )

        # Show coverage summary
        total_sessions = daily_schedule.sessions.count()
        assigned_sessions = daily_schedule.sessions.exclude(assigned_guide__isnull=True).count()
        coverage_pct = round((assigned_sessions / total_sessions) * 100) if total_sessions > 0 else 0

        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"Coverage: {assigned_sessions}/{total_sessions} sessions ({coverage_pct}%)")
        self.stdout.write("="*60)

        self.stdout.write("\nNext steps:")
        self.stdout.write("1. Review assignments in admin panel or schedule overview")
        self.stdout.write("2. Manually adjust if needed")
        self.stdout.write("3. Publish schedule when ready")

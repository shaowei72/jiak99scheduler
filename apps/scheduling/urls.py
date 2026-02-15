from django.urls import path
from apps.scheduling import views, api_views

urlpatterns = [
    path('overview/', views.schedule_overview, name='schedule_overview'),
    path('manager/', views.schedule_manager, name='schedule_manager'),

    # API endpoints (Phase 2)
    path('api/assign/', api_views.assign_guide, name='api_assign_guide'),
    path('api/unassign/', api_views.unassign_guide, name='api_unassign_guide'),
    path('api/session/<int:session_id>/eligible/', api_views.get_eligible_guides, name='api_eligible_guides'),
    path('api/session/<int:session_id>/', api_views.get_session_data, name='api_session_data'),
    path('api/standby/', api_views.update_standby, name='api_update_standby'),
    path('api/stats/<str:date_str>/', api_views.get_schedule_stats, name='api_schedule_stats'),

    # API endpoints (Phase 3)
    path('api/auto-assign/', api_views.auto_assign_day, name='api_auto_assign'),
    path('api/clear-all/', api_views.clear_all_assignments, name='api_clear_all'),

    # API endpoints (Phase 4)
    path('api/export/<str:date_str>/', api_views.export_schedule_csv, name='api_export_csv'),
    path('api/publish/', api_views.publish_schedule, name='api_publish'),
]

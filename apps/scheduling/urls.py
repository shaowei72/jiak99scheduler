from django.urls import path
from apps.scheduling import views, api_views

urlpatterns = [
    # Main Dashboard
    path('', views.schedule_dashboard, name='schedule_dashboard'),

    # Tour Guide Schedule
    path('guide/overview/', views.schedule_overview, name='schedule_overview'),
    path('guide/', views.schedule_manager, name='schedule_manager'),

    # Restaurant Schedule
    path('restaurant/', views.restaurant_schedule_manager, name='restaurant_schedule_manager'),
    path('restaurant/grid/', views.kitchen_staff_grid, name='kitchen_staff_grid'),

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

    # Restaurant API endpoints (Phase 5)
    path('api/restaurant/auto-assign/', api_views.restaurant_auto_assign, name='api_restaurant_auto_assign'),
    path('api/restaurant/clear-all/', api_views.restaurant_clear_all, name='api_restaurant_clear_all'),
    path('api/restaurant/publish/', api_views.restaurant_publish, name='api_restaurant_publish'),
    path('api/restaurant/assign-shift/', api_views.restaurant_assign_shift, name='api_restaurant_assign_shift'),
    path('api/restaurant/schedule/<str:date_str>/', api_views.restaurant_schedule_data, name='api_restaurant_schedule_data'),
    path('api/restaurant/export/<str:date_str>/', api_views.restaurant_export_csv, name='api_restaurant_export_csv'),
]

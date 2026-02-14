from django.urls import path
from apps.scheduling import views

urlpatterns = [
    path('overview/', views.schedule_overview, name='schedule_overview'),
]

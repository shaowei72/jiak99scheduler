from django.urls import path
from apps.guides import views

urlpatterns = [
    path('dashboard/', views.guide_dashboard, name='guide_dashboard'),
    path('availability/', views.mark_availability, name='mark_availability'),
    path('schedule/', views.my_schedule, name='my_schedule'),
]

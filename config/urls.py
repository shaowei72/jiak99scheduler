"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from config import views

# Customize admin site
admin.site.site_header = "Jiak99 Planner - Manager Administration"
admin.site.site_title = "Jiak99 Planner Admin"
admin.site.index_title = "Manager Dashboard"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('guides/', include('apps.guides.urls')),
    path('schedule/', include('apps.scheduling.urls')),
    path('main/', views.main_landing, name='main_landing'),
    path('', lambda request: redirect('main_landing')),
]

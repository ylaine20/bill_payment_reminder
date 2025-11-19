from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.bills_list, name='bills_list'),
    path('reminders/', views.reminders, name='reminders'),
    path('reports/', views.reports, name='reports'),
    path('settings/', views.settings, name='settings'),
]
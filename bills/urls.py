from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('bills/', views.bills_list, name='bills-list'),
    path('bills/create/', views.bill_create, name='bill-create'),
    path('bills/<int:pk>/', views.bill_detail, name='bill-detail'),
    path('bills/<int:pk>/edit/', views.bill_update, name='bill-update'),
    path('bills/<int:pk>/delete/', views.bill_delete, name='bill-delete'),
    path('bills/<int:pk>/pay/', views.mark_as_paid, name='bill-pay'),
    path('logout/', views.logout_view, name='logout'),
    
    # Notifications
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Settings & Preferences
    path('settings/', views.settings_view, name='settings'),
    path('payment-methods/', views.payment_methods_view, name='payment_methods'),
    path('settings/payment-method/<int:pk>/delete/', views.delete_payment_method, name='delete_payment_method'),
    path('settings/budget/<int:pk>/delete/', views.delete_budget, name='delete_budget'),
    
    # Analytics & Export
    path('api/analytics/', views.analytics_data, name='analytics_data'),
    path('export/csv/', views.export_bills_csv, name='export_csv'),
    path('export/pdf/', views.export_bills_pdf, name='export_pdf'),
    
    # Search
    path('api/search/', views.search_bills, name='search_bills'),
    
    # Calendar
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/calendar-events/', views.calendar_events, name='calendar_events'),
]
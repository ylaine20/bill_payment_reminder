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
]
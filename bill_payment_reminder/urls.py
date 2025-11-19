from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from security_management.views import register_view, login_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', 
         LoginView.as_view(template_name='security_management/organisms/login.html'),
         name='login'),

    path('logout/', LogoutView.as_view(), name='logout'),

    path('bills/', include('bills.urls')),

    path('', RedirectView.as_view(url='/bills/', permanent=False)),

    
    path('register/', register_view, name='register'),   
]



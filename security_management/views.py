from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm
from .models import LoginAttempt
from django.utils import timezone
from django.contrib.auth.views import LoginView  # Optional, but useful

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('bills-dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created successfully for {user.first_name}!')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'security_management/organisms/register.html', {'form': form})


def login_view(request):
    """User login view with security tracking"""
    if request.user.is_authenticated:
        return redirect('bills-dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        # Log login attempt
        ip_address = get_client_ip(request)
        LoginAttempt.objects.create(
            user=user if user else None,
            ip_address=ip_address,
            username_attempted=username,
            successful=user is not None
        )
        
        if user is not None:
            login(request, user)
            
            if not remember_me:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(1209600)
            
            messages.success(request, f'Welcome back, {user.first_name}!')
            
            next_page = request.GET.get('next', 'bills-dashboard')
            return redirect(next_page)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'security_management/organisms/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')

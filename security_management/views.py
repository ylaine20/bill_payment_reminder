from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm
from .models import LoginAttempt
from django.utils import timezone


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
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created successfully! Welcome, {user.first_name}!')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'security_management/organisms/register.html', {'form': form})


def login_view(request):
    """User login view with security tracking - uses email"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Get email from the form (it's submitted as 'username' field)
        email = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        # Authenticate using email (your EmailBackend handles this)
        user = authenticate(request, username=email, password=password)
        
        # Log login attempt
        ip_address = get_client_ip(request)
        LoginAttempt.objects.create(
            user=user if user else None,
            ip_address=ip_address,
            username_attempted=email,
            successful=user is not None
        )
        
        if user is not None:
            login(request, user)
            
            # Handle "Remember Me"
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            else:
                request.session.set_expiry(1209600)  # 2 weeks
            
            # Show greeting with first name
            messages.success(request, f'Welcome back, {user.first_name}!')
            
            next_page = request.GET.get('next', 'dashboard')
            return redirect(next_page)
        else:
            messages.error(request, 'Invalid email or password.')
    
    form = UserLoginForm()
    return render(request, 'security_management/organisms/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')
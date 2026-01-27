from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm, ChangePasswordForm
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
    
    return render(request, 'security_management/pages/register.html', {'form': form})


def login_view(request):
    """User login view with security tracking - uses email"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    attempted_username = ''
    
    if request.method == 'POST':
        # Get email from the form (it's submitted as 'username' field)
        email = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        attempted_username = email  # Save for form repopulation
        
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
            
            next_page = request.GET.get('next', 'dashboard')
            return redirect(next_page)
        else:
            # Check if the email exists to give more specific error
            from .models import CustomUser
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, 'Invalid password.')
            else:
                messages.error(request, 'Email not found.')
    
    form = UserLoginForm()
    return render(request, 'security_management/pages/login.html', {
        'form': form,
        'attempted_username': attempted_username
    })


@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def profile_view(request):
    """User profile view"""
    if request.method == 'POST':
        # Determine which form was submitted based on the button name or hidden field
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=request.user)
            password_form = ChangePasswordForm(request.user)
            
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
                
        elif 'change_password' in request.POST:
            profile_form = ProfileUpdateForm(instance=request.user)
            password_form = ChangePasswordForm(request.user, request.POST)
            
            if password_form.is_valid():
                user = request.user
                user.set_password(password_form.cleaned_data['new_password'])
                user.save()
                # Keep user logged in after password change using proper Django method
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('profile')
        else:
            profile_form = ProfileUpdateForm(instance=request.user)
            password_form = ChangePasswordForm(request.user)
            
    else:
        profile_form = ProfileUpdateForm(instance=request.user)
        password_form = ChangePasswordForm(request.user)
        
    return render(request, 'security_management/pages/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form
    })
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Bill

@login_required
def dashboard(request):
    """
    Dashboard view showing bill statistics
    """
    # Get the current user's bills
    bills = Bill.objects.filter(user=request.user)
    
    # Get current date
    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate statistics
    total_bills = bills.count()
    pending_bills = bills.filter(status='pending').count()
    paid_bills = bills.filter(status='paid', payment_date__gte=current_month_start).count()
    overdue_bills = bills.filter(
        due_date__lt=now,
        status='pending'
    ).count()
    
    # Calculate last month's total for comparison
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_month_bills = bills.filter(
        created_at__gte=last_month_start,
        created_at__lt=current_month_start
    ).count()
    
    # Calculate percentage change
    if last_month_bills > 0:
        change_percent = ((total_bills - last_month_bills) / last_month_bills) * 100
        total_change = f"+{change_percent:.0f}% from last month" if change_percent > 0 else f"{change_percent:.0f}% from last month"
    else:
        total_change = "+0% from last month"
    
    # Get user initials for badge
    user_initials = ''.join([name[0].upper() for name in request.user.get_full_name().split()[:2]]) if request.user.get_full_name() else request.user.username[:2].upper()
    
    context = {
        'username': request.user.first_name or request.user.username,
        'user_initials': user_initials,
        'notification_count': overdue_bills,  # Number of overdue bills as notifications
        'total_bills': total_bills,
        'pending_bills': pending_bills,
        'paid_bills': paid_bills,
        'overdue_bills': overdue_bills,
        'total_change': total_change,
    }
    
    return render(request, 'bills/dashboard.html', context)


@login_required
def bills_list(request):
    """
    View to list all bills
    """
    bills = Bill.objects.filter(user=request.user).order_by('-due_date')
    
    context = {
        'bills': bills,
    }
    
    return render(request, 'bills/bills_list.html', context)


@login_required
def reminders(request):
    """
    View to show reminders
    """
    context = {}
    return render(request, 'bills/reminders.html', context)


@login_required
def reports(request):
    """
    View to show reports
    """
    context = {}
    return render(request, 'bills/reports.html', context)


@login_required
def settings(request):
    """
    View to show settings
    """
    context = {}
    return render(request, 'bills/settings.html', context)


def logout_view(request):
    """
    Logout view
    """
    auth_logout(request)
    return redirect('login')  # Adjust to your login URL name
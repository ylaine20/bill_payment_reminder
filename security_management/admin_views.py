from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser
from bills.models import Bill, Notification


def is_admin(user):
    """Check if user is admin (staff or superuser)"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def admin_dashboard(request):
    """Admin dashboard home with statistics"""
    # User statistics
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    staff_users = CustomUser.objects.filter(is_staff=True).count()
    superusers = CustomUser.objects.filter(is_superuser=True).count()
    
    # New users this month
    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month = CustomUser.objects.filter(date_joined__gte=month_start).count()
    
    # Bill statistics
    total_bills = Bill.objects.count()
    pending_bills = Bill.objects.filter(status='pending').count()
    paid_bills = Bill.objects.filter(status='paid').count()
    
    # Recent users
    recent_users = CustomUser.objects.order_by('-date_joined')[:5]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'new_users_this_month': new_users_this_month,
        'total_bills': total_bills,
        'pending_bills': pending_bills,
        'paid_bills': paid_bills,
        'recent_users': recent_users,
    }
    return render(request, 'security_management/admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def admin_user_list(request):
    """List all users with search and filter"""
    users = CustomUser.objects.all()
    
    # Search
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Filter by role
    role = request.GET.get('role', '')
    if role == 'admin':
        users = users.filter(is_superuser=True)
    elif role == 'staff':
        users = users.filter(is_staff=True, is_superuser=False)
    elif role == 'user':
        users = users.filter(is_staff=False, is_superuser=False)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    
    # Annotate with bill count
    users = users.annotate(bill_count=Count('bill'))
    
    # Pagination
    paginator = Paginator(users.order_by('-date_joined'), 10)
    page = request.GET.get('page', 1)
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'search': search,
        'role': role,
        'status': status,
    }
    return render(request, 'security_management/admin/user_list.html', context)


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def admin_user_detail(request, pk):
    """View user details"""
    user = get_object_or_404(CustomUser, pk=pk)
    bills = Bill.objects.filter(user=user).order_by('-due_date')[:10]
    
    context = {
        'user_obj': user,
        'bills': bills,
        'total_bills': Bill.objects.filter(user=user).count(),
        'pending_bills': Bill.objects.filter(user=user, status='pending').count(),
        'paid_bills': Bill.objects.filter(user=user, status='paid').count(),
    }
    return render(request, 'security_management/admin/user_detail.html', context)


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def admin_user_edit(request, pk):
    """Edit user details and roles"""
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.method == 'POST':
        # Update basic info
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        
        # Update roles (only superusers can change roles)
        if request.user.is_superuser:
            user.is_active = request.POST.get('is_active') == 'on'
            user.is_staff = request.POST.get('is_staff') == 'on'
            # Prevent removing own superuser status
            if user != request.user:
                user.is_superuser = request.POST.get('is_superuser') == 'on'
        
        user.save()
        messages.success(request, f'User "{user.email}" updated successfully!')
        return redirect('admin_user_list')
    
    context = {
        'user_obj': user,
    }
    return render(request, 'security_management/admin/user_edit.html', context)


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def admin_user_toggle_active(request, pk):
    """Toggle user active status"""
    user = get_object_or_404(CustomUser, pk=pk)
    
    # Prevent deactivating self
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account!")
        return redirect('admin_user_list')
    
    user.is_active = not user.is_active
    user.save()
    
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f'User "{user.email}" has been {status}.')
    return redirect('admin_user_list')


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def admin_user_delete(request, pk):
    """Delete user"""
    user = get_object_or_404(CustomUser, pk=pk)
    
    # Prevent deleting self
    if user == request.user:
        messages.error(request, "You cannot delete your own account!")
        return redirect('admin_user_list')
    
    # Prevent non-superusers from deleting admins
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "Only superusers can delete admin accounts!")
        return redirect('admin_user_list')
    
    if request.method == 'POST':
        email = user.email
        user.delete()
        messages.success(request, f'User "{email}" has been deleted.')
        return redirect('admin_user_list')
    
    context = {
        'user_obj': user,
    }
    return render(request, 'security_management/admin/user_delete.html', context)

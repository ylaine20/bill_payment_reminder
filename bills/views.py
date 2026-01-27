from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Bill
from .forms import BillForm

@login_required
def dashboard(request):
    bills = Bill.objects.filter(user=request.user)
    
    pending_bills = bills.filter(status='pending')
    paid_bills = bills.filter(status='paid')
    
    # Get overdue and due soon bills
    overdue_bills = []
    due_soon_bills = []
    
    for bill in pending_bills:
        if bill.is_overdue:
            overdue_bills.append(bill)
        elif bill.is_due_soon:
            due_soon_bills.append(bill)
    
    # Get bills for the next 7 days
    now = timezone.now()
    seven_days_later = now + timedelta(days=7)
    upcoming_bills = pending_bills.filter(
        due_date__gte=now,
        due_date__lte=seven_days_later
    ).order_by('due_date')
    
    # Count paid bills this month
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    paid_this_month = paid_bills.filter(payment_date__gte=current_month_start).count()
    
    context = {
        'bills': bills,
        'pending_bills': pending_bills,
        'paid_bills': paid_bills,
        'overdue_bills': overdue_bills,
        'due_soon_bills': due_soon_bills,
        'upcoming_bills': upcoming_bills,
        'total_bills': bills.count(),
        'total_pending': pending_bills.count(),
        'total_paid': paid_bills.count(),
        'paid_this_month': paid_this_month,
        'overdue_count': len(overdue_bills),
    }
    
    return render(request, 'bills/dashboard.html', context)

@login_required
@login_required
def bills_list(request):
    # Get the status filter from query parameters
    status_filter = request.GET.get('status', None)
    
    # Start with all bills for the current user
    bills = Bill.objects.filter(user=request.user)
    
    # Apply filter if status parameter exists
    if status_filter == 'pending':
        bills = bills.filter(status='pending')
    elif status_filter == 'paid':
        bills = bills.filter(status='paid')
    
    # Order bills by due date (optional but recommended)
    bills = bills.order_by('due_date')
    
    # Keep these for backward compatibility if needed elsewhere
    pending_bills = Bill.objects.filter(user=request.user, status='pending')
    paid_bills = Bill.objects.filter(user=request.user, status='paid')
    
    context = {
        'bills': bills,
        'pending_bills': pending_bills,
        'paid_bills': paid_bills,
        'status_filter': status_filter,
    }
    
    return render(request, 'bills/bill_list.html', context)
@login_required
def bill_create(request):
    if request.method == 'POST':
        form = BillForm(request.POST, request.FILES)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.user = request.user
            bill.save()
            messages.success(request, 'Bill created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
            print("Form errors:", form.errors)
    else:
        form = BillForm()
    
    return render(request, 'bills/bill_form.html', {'form': form, 'action': 'Create'})

@login_required
def bill_detail(request, pk):
    bill = get_object_or_404(Bill, pk=pk, user=request.user)
    return render(request, 'bills/bill_detail.html', {'bill': bill})

@login_required
def bill_update(request, pk):
    bill = get_object_or_404(Bill, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BillForm(request.POST, request.FILES, instance=bill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bill updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BillForm(instance=bill)
    
    return render(request, 'bills/bill_form.html', {'form': form, 'bill': bill, 'action': 'Update'})

@login_required
def bill_delete(request, pk):
    bill = get_object_or_404(Bill, pk=pk, user=request.user)
    if request.method == 'POST':
        bill.delete()
        messages.success(request, 'Bill deleted successfully!')
        return redirect('dashboard')
    
    return render(request, 'bills/bill_confirm_delete.html', {'bill': bill})

@login_required
def mark_as_paid(request, pk):
    bill = get_object_or_404(Bill, pk=pk, user=request.user)
    bill.status = 'paid'
    bill.payment_date = timezone.now()
    bill.save()
    messages.success(request, f'{bill.name} marked as paid!')
    return redirect('dashboard')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    bills = Bill.objects.filter(user=request.user)
    
    # DEBUG: Print all bills
    print(f"Total bills: {bills.count()}")
    for bill in bills:
        print(f"Bill: {bill.name}, Status: {bill.status}, Due: {bill.due_date}")
    
    pending_bills = bills.filter(status='pending')
    paid_bills = bills.filter(status='paid')
    
    # Get overdue and due soon bills
    overdue_bills = []
    due_soon_bills = []
    
    for bill in pending_bills:
        if bill.is_overdue:
            overdue_bills.append(bill)
        elif bill.is_due_soon:
            due_soon_bills.append(bill)
    
    # Get bills for the next 7 days
    now = timezone.now()
    seven_days_later = now + timedelta(days=7)
    
    # DEBUG
    print(f"Now: {now}")
    print(f"Seven days later: {seven_days_later}")
    
    upcoming_bills = pending_bills.filter(
        due_date__gte=now,
        due_date__lte=seven_days_later
    ).order_by('due_date')
    
    # DEBUG
    print(f"Upcoming bills count: {upcoming_bills.count()}")
    
    # Count paid bills this month
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    paid_this_month = paid_bills.filter(payment_date__gte=current_month_start).count()
    
    context = {
        'bills': bills,
        'pending_bills': pending_bills,
        'paid_bills': paid_bills,
        'overdue_bills': overdue_bills,
        'due_soon_bills': due_soon_bills,
        'upcoming_bills': upcoming_bills,
        'total_bills': bills.count(),
        'total_pending': pending_bills.count(),
        'total_paid': paid_bills.count(),
        'paid_this_month': paid_this_month,
        'overdue_count': len(overdue_bills),
    }
    
    return render(request, 'bills/dashboard.html', context)
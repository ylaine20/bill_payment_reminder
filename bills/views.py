from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from .models import Bill, Notification
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
    
    # Get budgets for the user
    from .models import Budget
    from .forms import BudgetForm
    
    budgets = Budget.objects.filter(user=request.user, is_active=True)
    budget_form = BudgetForm()
    
    # Handle budget form submission
    if request.method == 'POST' and 'add_budget' in request.POST:
        budget_form = BudgetForm(request.POST)
        if budget_form.is_valid():
            budget = budget_form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(request, 'Budget goal added!')
            return redirect('dashboard')
    
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
        'budgets': budgets,
        'budget_form': budget_form,
    }
    
    return render(request, 'bills/dashboard.html', context)

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
    elif status_filter == 'overdue':
        # Overdue = pending bills with due_date in the past
        now = timezone.now()
        bills = bills.filter(status='pending', due_date__lt=now)
    
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
        form = BillForm(request.POST, request.FILES, user=request.user)
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
        form = BillForm(user=request.user)
    
    return render(request, 'bills/bill_form.html', {'form': form, 'action': 'Create'})

@login_required
def bill_detail(request, pk):
    bill = get_object_or_404(Bill, pk=pk, user=request.user)
    return render(request, 'bills/bill_detail.html', {'bill': bill})

@login_required
def bill_update(request, pk):
    bill = get_object_or_404(Bill, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BillForm(request.POST, request.FILES, instance=bill, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bill updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BillForm(instance=bill, user=request.user)
    
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
    
    # DEBUG: Log recurring bill info
    print(f"[DEBUG] Marking bill as paid: {bill.name}")
    print(f"[DEBUG] bill.recurring = {bill.recurring}")
    print(f"[DEBUG] bill.recurrence_frequency = '{bill.recurrence_frequency}'")
    
    bill.status = 'paid'
    bill.payment_date = timezone.now()
    bill.save()
    
    # Remove overdue/due_soon notifications for this bill
    Notification.objects.filter(
        user=request.user, bill=bill, 
        notification_type__in=['overdue', 'due_soon']
    ).delete()
    
    # Create payment confirmation notification
    Notification.objects.create(
        user=request.user,
        bill=bill,
        title='Payment Confirmed',
        message=f'You have successfully paid "{bill.name}". Amount:\u00A0₱{bill.amount}',
        notification_type='payment'
    )
    
    # Handle recurring bills - create next occurrence
    # Check if recurring is True AND frequency is NOT 'none'
    if bill.recurring and bill.recurrence_frequency and bill.recurrence_frequency != 'none':
        next_due_date = bill.get_next_due_date()
        print(f"[DEBUG] Creating next bill with due date: {next_due_date}")
        if next_due_date:
            new_bill = Bill.objects.create(
                user=request.user,
                name=bill.name,
                amount=bill.amount,
                due_date=next_due_date,
                status='pending',
                category=bill.category,
                notes=bill.notes,
                recurring=True,
                recurrence_frequency=bill.recurrence_frequency,
                payment_method=bill.payment_method,
            )
            print(f"[DEBUG] Created new bill ID: {new_bill.id}")
            messages.info(request, f'Next "{bill.name}" bill created for {next_due_date.strftime("%b %d, %Y")}')
    else:
        print(f"[DEBUG] NOT creating next bill - recurring={bill.recurring}, frequency='{bill.recurrence_frequency}'")
    
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


def generate_notifications(user):
    """Generate notifications for overdue and due soon bills"""
    pending_bills = Bill.objects.filter(user=user, status='pending')
    
    for bill in pending_bills:
        # Check for overdue bills - create notification if not already exists
        if bill.is_overdue:
            existing = Notification.objects.filter(
                user=user, bill=bill, notification_type='overdue'
            ).exists()
            if not existing:
                Notification.objects.create(
                    user=user,
                    bill=bill,
                    title='Overdue Bill',
                    message=f'"{bill.name}" was due on {bill.due_date.strftime("%b %d, %Y at %I:%M %p")}. Amount:\u00A0₱{bill.amount}',
                    notification_type='overdue'
                )
        # Check for due soon bills
        elif bill.is_due_soon:
            existing = Notification.objects.filter(
                user=user, bill=bill, notification_type='due_soon'
            ).exists()
            if not existing:
                Notification.objects.create(
                    user=user,
                    bill=bill,
                    title='Bill Due Soon',
                    message=f'"{bill.name}" is due on {bill.due_date.strftime("%b %d, %Y at %I:%M %p")}. Amount:\u00A0₱{bill.amount}',
                    notification_type='due_soon'
                )


@login_required
def get_notifications(request):
    """API endpoint to get user notifications"""
    # Generate any new notifications
    generate_notifications(request.user)
    
    notifications = Notification.objects.filter(user=request.user)[:10]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    data = {
        'unread_count': unread_count,
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'icon': n.icon,
                'color': n.color,
                'is_read': n.is_read,
                'created_at': n.created_at.strftime('%b %d, %H:%M'),
            }
            for n in notifications
        ]
    }
    return JsonResponse(data)


@login_required
def mark_notification_read(request, pk):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'ok'})


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})


# ============ SETTINGS & PREFERENCES ============

@login_required
def settings_view(request):
    """User settings page for preferences, payment methods, and budgets"""
    from .forms import UserPreferenceForm, PaymentMethodForm, BudgetForm
    from .models import UserPreference, PaymentMethod, Budget
    
    # Get or create user preferences
    try:
        preferences = request.user.preferences
    except UserPreference.DoesNotExist:
        preferences = UserPreference.objects.create(user=request.user)
    
    # Handle form submissions
    if request.method == 'POST':
        if 'save_preferences' in request.POST:
            pref_form = UserPreferenceForm(request.POST, instance=preferences)
            if pref_form.is_valid():
                pref_form.save()
                messages.success(request, 'Preferences saved!')
                return redirect('settings')
        elif 'add_payment_method' in request.POST:
            pm_form = PaymentMethodForm(request.POST)
            if pm_form.is_valid():
                pm = pm_form.save(commit=False)
                pm.user = request.user
                pm.save()
                messages.success(request, 'Payment method added!')
                return redirect('settings')
        elif 'add_budget' in request.POST:
            budget_form = BudgetForm(request.POST)
            if budget_form.is_valid():
                budget = budget_form.save(commit=False)
                budget.user = request.user
                budget.save()
                messages.success(request, 'Budget goal added!')
                return redirect('settings')
    
    context = {
        'preferences': preferences,
        'pref_form': UserPreferenceForm(instance=preferences),
        'pm_form': PaymentMethodForm(),
        'budget_form': BudgetForm(),
        'payment_methods': PaymentMethod.objects.filter(user=request.user),
        'budgets': Budget.objects.filter(user=request.user, is_active=True),
    }
    return render(request, 'bills/settings.html', context)


@login_required
def delete_payment_method(request, pk):
    """Delete a payment method"""
    from .models import PaymentMethod
    pm = get_object_or_404(PaymentMethod, pk=pk, user=request.user)
    pm.delete()
    messages.success(request, 'Payment method deleted!')
    return redirect('payment_methods')


@login_required
def payment_methods_view(request):
    """Dedicated page for managing payment methods"""
    from .models import PaymentMethod
    from .forms import PaymentMethodForm
    
    if request.method == 'POST':
        if 'add_payment_method' in request.POST:
            pm_form = PaymentMethodForm(request.POST)
            if pm_form.is_valid():
                pm = pm_form.save(commit=False)
                pm.user = request.user
                pm.save()
                messages.success(request, 'Payment method added!')
                return redirect('payment_methods')
    
    context = {
        'payment_methods': PaymentMethod.objects.filter(user=request.user),
        'pm_form': PaymentMethodForm(),
    }
    return render(request, 'bills/payment_methods.html', context)


@login_required
def delete_budget(request, pk):
    """Delete a budget"""
    from .models import Budget
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    budget.delete()
    messages.success(request, 'Budget deleted!')
    return redirect('dashboard')


# ============ ANALYTICS DATA ============

@login_required
def analytics_data(request):
    """API endpoint for dashboard charts"""
    from django.db.models import Sum
    from django.db.models.functions import TruncMonth
    from collections import defaultdict
    import json
    
    # Monthly spending for last 6 months
    now = timezone.now()
    six_months_ago = now - timedelta(days=180)
    
    monthly_data = Bill.objects.filter(
        user=request.user,
        status='paid',
        payment_date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    months = []
    amounts = []
    for item in monthly_data:
        if item['month']:
            months.append(item['month'].strftime('%b %Y'))
            amounts.append(float(item['total'] or 0))
    
    # Category breakdown
    category_data = Bill.objects.filter(
        user=request.user,
        status='paid',
        payment_date__gte=six_months_ago
    ).values('category').annotate(
        total=Sum('amount')
    )
    
    categories = []
    category_amounts = []
    category_colors = []
    for item in category_data:
        categories.append(dict(Bill.CATEGORY_CHOICES).get(item['category'], item['category']))
        category_amounts.append(float(item['total'] or 0))
        category_colors.append(Bill.CATEGORY_COLORS.get(item['category'], '#64748b'))
    
    return JsonResponse({
        'monthly': {'labels': months, 'data': amounts},
        'categories': {'labels': categories, 'data': category_amounts, 'colors': category_colors},
    })


# ============ EXPORT FUNCTIONALITY ============

@login_required
def export_bills_csv(request):
    """Export bills to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bills_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Amount', 'Due Date', 'Status', 'Category', 'Payment Date', 'Payment Method', 'Notes'])
    
    # Get filter parameters
    status = request.GET.get('status', '')
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    
    bills = Bill.objects.filter(user=request.user)
    
    if status:
        bills = bills.filter(status=status)
    if date_from:
        bills = bills.filter(due_date__gte=date_from)
    if date_to:
        bills = bills.filter(due_date__lte=date_to)
    
    for bill in bills.order_by('-due_date'):
        writer.writerow([
            bill.name,
            bill.amount,
            bill.due_date.strftime('%Y-%m-%d %H:%M'),
            bill.get_status_display(),
            bill.get_category_display(),
            bill.payment_date.strftime('%Y-%m-%d %H:%M') if bill.payment_date else '',
            bill.payment_method.name if bill.payment_method else '',
            bill.notes or '',
        ])
    
    return response


@login_required
def export_bills_pdf(request):
    """Export bills to PDF"""
    from django.http import HttpResponse
    from io import BytesIO
    
    # Simple HTML to PDF approach
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2563eb; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #2563eb; color: white; }}
            .paid {{ color: green; }}
            .pending {{ color: orange; }}
            .total {{ font-weight: bold; font-size: 18px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>Bill Payment Report</h1>
        <p>Generated on: {timezone.now().strftime('%B %d, %Y')}</p>
        <table>
            <thead>
                <tr>
                    <th>Bill Name</th>
                    <th>Amount</th>
                    <th>Due Date</th>
                    <th>Status</th>
                    <th>Category</th>
                </tr>
            </thead>
            <tbody>
    """
    
    bills = Bill.objects.filter(user=request.user).order_by('-due_date')
    total = 0
    
    for bill in bills:
        status_class = 'paid' if bill.status == 'paid' else 'pending'
        html_content += f"""
            <tr>
                <td>{bill.name}</td>
                <td>₱{bill.amount}</td>
                <td>{bill.due_date.strftime('%b %d, %Y')}</td>
                <td class="{status_class}">{bill.get_status_display()}</td>
                <td>{bill.get_category_display()}</td>
            </tr>
        """
        total += bill.amount
    
    html_content += f"""
            </tbody>
        </table>
        <p class="total">Total: ₱{total}</p>
    </body>
    </html>
    """
    
    response = HttpResponse(content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="bills_report_{timezone.now().strftime("%Y%m%d")}.html"'
    response.write(html_content)
    
    return response


# ============ SEARCH & FILTER (AJAX) ============

@login_required
def search_bills(request):
    """AJAX search for bills"""
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    sort = request.GET.get('sort', 'due_date')
    
    bills = Bill.objects.filter(user=request.user)
    
    if query:
        bills = bills.filter(name__icontains=query)
    if status:
        bills = bills.filter(status=status)
    if category:
        bills = bills.filter(category=category)
    
    # Sorting
    if sort == 'amount':
        bills = bills.order_by('-amount')
    elif sort == 'name':
        bills = bills.order_by('name')
    elif sort == '-due_date':
        bills = bills.order_by('-due_date')
    else:
        bills = bills.order_by('due_date')
    
    data = {
        'bills': [
            {
                'id': b.id,
                'name': b.name,
                'amount': str(b.amount),
                'due_date': b.due_date.strftime('%b %d, %Y'),
                'status': b.status,
                'category': b.category,
                'category_display': b.get_category_display(),
                'category_icon': b.category_icon,
                'category_color': b.category_color,
                'is_overdue': b.is_overdue,
                'is_due_soon': b.is_due_soon,
            }
            for b in bills[:50]
        ]
    }
    return JsonResponse(data)


# ============ CALENDAR VIEW ============

@login_required
def calendar_view(request):
    """Calendar page showing bills on due dates"""
    return render(request, 'bills/calendar.html')


@login_required
def calendar_events(request):
    """API endpoint returning bills as calendar events for FullCalendar"""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    
    start = request.GET.get('start', '')
    end = request.GET.get('end', '')
    
    # Parse the date range
    try:
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00')) if end else timezone.now() + timedelta(days=365)
    except:
        end_date = timezone.now() + timedelta(days=365)
    
    # Get all bills (not just in range, we'll generate recurring events)
    bills = Bill.objects.filter(user=request.user)
    
    events = []
    
    for bill in bills:
        # Determine color based on status
        if bill.status == 'paid':
            color = '#10b981'  # green
        elif bill.is_overdue:
            color = '#ef4444'  # red
        elif bill.is_due_soon:
            color = '#f59e0b'  # orange/warning
        else:
            color = Bill.CATEGORY_COLORS.get(bill.category, '#2563eb')
        
        # Always show as all-day event (no time display)
        is_all_day = True
        
        # Add the actual bill event
        events.append({
            'id': bill.id,
            'title': f'{bill.name} - ₱{bill.amount}',
            'start': bill.due_date.isoformat(),
            'allDay': is_all_day,  # Hide time if midnight, show if specific time set
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'status': bill.status,
                'category': bill.get_category_display(),
                'amount': str(bill.amount),
                'is_recurring': bill.recurring,
            }
        })
        
        # Generate future recurring events (virtual - not yet in database)
        if bill.recurring and bill.recurrence_frequency and bill.recurrence_frequency != 'none':
            # Calculate future occurrences
            current_date = bill.due_date
            occurrences_added = 0
            max_occurrences = 12  # Show up to 12 future occurrences
            
            while occurrences_added < max_occurrences:
                # Calculate next date based on frequency
                if bill.recurrence_frequency == 'weekly':
                    next_date = current_date + timedelta(weeks=1)
                elif bill.recurrence_frequency == 'monthly':
                    next_date = current_date + relativedelta(months=1)
                elif bill.recurrence_frequency == 'yearly':
                    next_date = current_date + relativedelta(years=1)
                else:
                    break
                
                # Stop if we're past the calendar range
                if next_date > end_date:
                    break
                
                # Check if a bill already exists for this date (avoid duplicates)
                existing = Bill.objects.filter(
                    user=request.user,
                    name=bill.name,
                    due_date__date=next_date.date()
                ).exists()
                
                if not existing:
                    # Add virtual future event (faded yellow - clearly different from actual bills)
                    events.append({
                        'id': f'future_{bill.id}_{occurrences_added}',
                        'title': f'{bill.name} - ₱{bill.amount}',
                        'start': next_date.isoformat(),
                        'allDay': True,
                        'backgroundColor': '#fef3c7',  # Light yellow background
                        'borderColor': '#f59e0b',  # Amber border
                        'textColor': '#92400e',  # Dark amber text
                        'extendedProps': {
                            'status': 'future',
                            'category': bill.get_category_display(),
                            'amount': str(bill.amount),
                            'is_recurring': True,
                            'is_future': True,
                            'original_bill_id': bill.id,  # Link to original bill
                        }
                    })
                    occurrences_added += 1
                
                current_date = next_date
    
    return JsonResponse(events, safe=False)
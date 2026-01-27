from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class UserPreference(models.Model):
    """User preferences for email reminders and settings"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    
    # Email reminder settings
    email_reminders_enabled = models.BooleanField(default=True)
    remind_days_before = models.IntegerField(default=3, help_text="Days before due date to send reminder")
    daily_digest_enabled = models.BooleanField(default=False)
    
    # Theme preference
    dark_mode = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.email}"


class PaymentMethod(models.Model):
    """Payment methods for tracking how bills are paid"""
    PAYMENT_ICONS = {
        'cash': 'bi-cash-stack',
        'gcash': 'bi-phone',
        'bank': 'bi-bank',
        'card': 'bi-credit-card',
        'maya': 'bi-wallet2',
        'other': 'bi-wallet',
    }
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    name = models.CharField(max_length=100)
    method_type = models.CharField(max_length=20, choices=[
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
        ('maya', 'Maya'),
        ('bank', 'Bank Transfer'),
        ('card', 'Credit/Debit Card'),
        ('other', 'Other'),
    ], default='cash')
    account_details = models.CharField(max_length=200, blank=True, help_text="Account number or details")
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.get_method_type_display()})"
    
    @property
    def icon(self):
        return self.PAYMENT_ICONS.get(self.method_type, 'bi-wallet')
    
    def save(self, *args, **kwargs):
        # Ensure only one default per user
        if self.is_default:
            PaymentMethod.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class Bill(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]
    
    CATEGORY_CHOICES = [
        ('utilities', 'Utilities'),
        ('electricity', 'Electricity'),
        ('water', 'Water'),
        ('internet', 'Internet'),
        ('rent', 'Rent'),
        ('insurance', 'Insurance'),
        ('subscription', 'Subscription'),
        ('phone', 'Phone'),
        ('transportation', 'Transportation'),
        ('food', 'Food & Grocery'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('entertainment', 'Entertainment'),
        ('other', 'Other'),
    ]
    
    CATEGORY_ICONS = {
        'utilities': 'bi-lightning-charge-fill',
        'electricity': 'bi-lightning-fill',
        'water': 'bi-droplet-fill',
        'internet': 'bi-wifi',
        'rent': 'bi-house-fill',
        'insurance': 'bi-shield-fill-check',
        'subscription': 'bi-calendar-check-fill',
        'phone': 'bi-phone-fill',
        'transportation': 'bi-car-front-fill',
        'food': 'bi-cart-fill',
        'healthcare': 'bi-heart-pulse-fill',
        'education': 'bi-mortarboard-fill',
        'entertainment': 'bi-controller',
        'other': 'bi-file-earmark-text-fill',
    }
    
    CATEGORY_COLORS = {
        'utilities': '#f59e0b',
        'electricity': '#eab308',
        'water': '#0ea5e9',
        'internet': '#8b5cf6',
        'rent': '#10b981',
        'insurance': '#3b82f6',
        'subscription': '#ec4899',
        'phone': '#6366f1',
        'transportation': '#f97316',
        'food': '#22c55e',
        'healthcare': '#ef4444',
        'education': '#14b8a6',
        'entertainment': '#a855f7',
        'other': '#64748b',
    }
    
    RECURRENCE_CHOICES = [
        ('none', 'One-time'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', blank=True)
    notes = models.TextField(blank=True, null=True)
    
    # Recurring bill support
    recurring = models.BooleanField(default=False)
    recurrence_frequency = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='none')
    
    # Payment tracking
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Email reminder tracking
    reminder_sent = models.BooleanField(default=False)
    last_reminder_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date']
        verbose_name = 'Bill'
        verbose_name_plural = 'Bills'
    
    def __str__(self):
        return f"{self.name} - ₱{self.amount}"
    
    @property
    def is_overdue(self):
        """Check if bill is overdue"""
        if self.status == 'pending' and self.due_date:
            # Compare dates, not datetimes to avoid timezone issues
            return self.due_date.date() < timezone.now().date()
        return False

    @property
    def is_due_soon(self):
        """Check if bill is due within 3 days"""
        if self.status == 'pending' and self.due_date:
            now = timezone.now()
            three_days_later = now + timedelta(days=3)
            return now <= self.due_date <= three_days_later
        return False
    
    @property
    def category_icon(self):
        return self.CATEGORY_ICONS.get(self.category, 'bi-file-earmark-text-fill')
    
    @property
    def category_color(self):
        return self.CATEGORY_COLORS.get(self.category, '#64748b')
    
    @property
    def receipt(self):
        """Alias for receipt_image for cleaner template usage"""
        return self.receipt_image
    
    def get_next_due_date(self):
        """Calculate next due date based on recurrence frequency"""
        if self.recurrence_frequency == 'weekly':
            return self.due_date + timedelta(weeks=1)
        elif self.recurrence_frequency == 'biweekly':
            return self.due_date + timedelta(weeks=2)
        elif self.recurrence_frequency == 'monthly':
            return self.due_date + timedelta(days=30)
        elif self.recurrence_frequency == 'quarterly':
            return self.due_date + timedelta(days=90)
        elif self.recurrence_frequency == 'yearly':
            return self.due_date + timedelta(days=365)
        return None


class BillAttachment(models.Model):
    """Multiple file attachments for bills"""
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='bill_attachments/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.filename} - {self.bill.name}"
    
    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = self.file.name.split('/')[-1]
        super().save(*args, **kwargs)


class Budget(models.Model):
    """Monthly budget goals per category"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    category = models.CharField(max_length=50, choices=Bill.CATEGORY_CHOICES)
    monthly_limit = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'category']
    
    def __str__(self):
        return f"{self.get_category_display()} Budget - ₱{self.monthly_limit}"
    
    def get_spent_this_month(self):
        """Calculate how much spent in this category this month"""
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return Bill.objects.filter(
            user=self.user,
            category=self.category,
            status='paid',
            payment_date__gte=start_of_month
        ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    @property
    def percentage_used(self):
        spent = self.get_spent_this_month()
        if self.monthly_limit > 0:
            return min(100, int((spent / self.monthly_limit) * 100))
        return 0
    
    @property
    def remaining(self):
        return max(0, self.monthly_limit - self.get_spent_this_month())


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('overdue', 'Overdue Bill'),
        ('due_soon', 'Bill Due Soon'),
        ('payment', 'Payment Confirmation'),
        ('reminder', 'Email Reminder Sent'),
        ('budget', 'Budget Alert'),
        ('info', 'Information'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    @property
    def icon(self):
        """Return Bootstrap icon class based on notification type"""
        icons = {
            'overdue': 'bi-exclamation-triangle-fill',
            'due_soon': 'bi-clock-fill',
            'payment': 'bi-check-circle-fill',
            'reminder': 'bi-envelope-fill',
            'budget': 'bi-piggy-bank-fill',
            'info': 'bi-info-circle-fill',
        }
        return icons.get(self.notification_type, 'bi-bell-fill')
    
    @property
    def color(self):
        """Return color class based on notification type"""
        colors = {
            'overdue': 'danger',
            'due_soon': 'warning',
            'payment': 'success',
            'reminder': 'primary',
            'budget': 'warning',
            'info': 'primary',
        }
        return colors.get(self.notification_type, 'secondary')
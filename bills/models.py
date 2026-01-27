from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class Bill(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]
    
    CATEGORY_CHOICES = [
        ('utilities', 'Utilities'),
        ('rent', 'Rent'),
        ('insurance', 'Insurance'),
        ('subscription', 'Subscription'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', blank=True)
    notes = models.TextField(blank=True, null=True)
    recurring = models.BooleanField(default=False)
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-due_date']
        verbose_name = 'Bill'
        verbose_name_plural = 'Bills'
    
    def __str__(self):
        return f"{self.name} - ${self.amount}"
    
    @property
    def is_overdue(self):
        """Check if bill is overdue"""
        if self.status == 'pending' and self.due_date:
            return self.due_date < timezone.now()
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
    def receipt(self):
        """Alias for receipt_image for cleaner template usage"""
        return self.receipt_image
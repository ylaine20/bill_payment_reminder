"""
Django management command to send bill reminder emails.
Run this command daily via cron or task scheduler:
    python manage.py send_reminders
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from bills.models import Bill, UserPreference, Notification


class Command(BaseCommand):
    help = 'Send email reminders for upcoming bills'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        reminders_sent = 0
        
        self.stdout.write(f"Checking for bills that need reminders at {now}")
        
        # Get all pending bills
        pending_bills = Bill.objects.filter(
            status='pending',
            due_date__gte=now,
        ).select_related('user')
        
        for bill in pending_bills:
            # Get user preferences
            try:
                prefs = bill.user.preferences
            except UserPreference.DoesNotExist:
                # Create default preferences if not exists
                prefs = UserPreference.objects.create(user=bill.user)
            
            if not prefs.email_reminders_enabled:
                continue
            
            # Check if reminder should be sent
            days_until_due = (bill.due_date - now).days
            
            if days_until_due <= prefs.remind_days_before:
                # Check if reminder was already sent today
                if bill.last_reminder_date and bill.last_reminder_date.date() == now.date():
                    continue
                
                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Would send reminder to {bill.user.email} "
                        f"for '{bill.name}' due in {days_until_due} days"
                    )
                else:
                    # Send email
                    success = self.send_reminder_email(bill, days_until_due)
                    
                    if success:
                        # Update bill tracking
                        bill.reminder_sent = True
                        bill.last_reminder_date = now
                        bill.save()
                        
                        # Create notification
                        Notification.objects.create(
                            user=bill.user,
                            bill=bill,
                            title='Reminder Email Sent',
                            message=f'Reminder sent for "{bill.name}" due in {days_until_due} days.',
                            notification_type='reminder'
                        )
                        
                        reminders_sent += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"Sent reminder to {bill.user.email} for '{bill.name}'")
                        )
        
        self.stdout.write(
            self.style.SUCCESS(f"Done! Sent {reminders_sent} reminder(s).")
        )

    def send_reminder_email(self, bill, days_until_due):
        """Send reminder email for a bill"""
        subject = f"Bill Reminder: {bill.name} due in {days_until_due} day(s)"
        
        message = f"""
Hello {bill.user.first_name or bill.user.username},

This is a friendly reminder that your bill is due soon:

Bill: {bill.name}
Amount: ₱{bill.amount}
Due Date: {bill.due_date.strftime('%B %d, %Y')}
Category: {bill.get_category_display()}

Don't forget to pay on time to avoid late fees!

---
Bill Payment Reminder
        """.strip()
        
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #2563eb, #3b82f6); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8fafc; padding: 20px; border-radius: 0 0 8px 8px; }}
        .bill-details {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .amount {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
        .due-date {{ color: #f59e0b; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>📋 Bill Payment Reminder</h2>
        </div>
        <div class="content">
            <p>Hello {bill.user.first_name or bill.user.username},</p>
            <p>This is a friendly reminder that your bill is due soon:</p>
            
            <div class="bill-details">
                <h3>{bill.name}</h3>
                <p class="amount" style="color: #2563eb; font-weight: bold; font-size: 24px;">Amount:&nbsp;₱{bill.amount}</p>
                <p class="due-date">Due: {bill.due_date.strftime('%B %d, %Y')} ({days_until_due} day(s) left)</p>
                <p>Category: {bill.get_category_display()}</p>
            </div>
            
            <p>Don't forget to pay on time to avoid late fees!</p>
            
            <p style="color: #64748b; font-size: 12px; margin-top: 30px;">
                — Bill Payment Reminder Team
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@billreminder.com',
                recipient_list=[bill.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to send email to {bill.user.email}: {e}")
            )
            return False

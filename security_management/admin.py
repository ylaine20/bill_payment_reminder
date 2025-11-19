from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, LoginAttempt

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Custom User Admin with additional fields
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_email_verified', 'created_at']
    list_filter = ['is_staff', 'is_active', 'is_email_verified', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'profile_picture', 'date_of_birth', 'is_email_verified')
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'sms_notifications')
        }),
    )


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """
    Login Attempt tracking admin
    """
    list_display = ['username_attempted', 'ip_address', 'successful', 'attempted_at']
    list_filter = ['successful', 'attempted_at']
    search_fields = ['username_attempted', 'ip_address']
    readonly_fields = ['user', 'ip_address', 'username_attempted', 'attempted_at', 'successful']
    ordering = ['-attempted_at']
    
    def has_add_permission(self, request):
        return False
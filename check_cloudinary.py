"""
Cloudinary Diagnostic Script for Bill Payment Reminder System
This script checks Cloudinary configuration and tests image upload/retrieval.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bill_payment_reminder.settings')
django.setup()

from django.conf import settings
import cloudinary
import cloudinary.uploader
from io import BytesIO
from PIL import Image


def print_status(message, status='info'):
    """Print formatted status messages"""
    symbols = {
        'success': '✓',
        'error': '✗',
        'info': 'ℹ',
        'warning': '⚠'
    }
    colors = {
        'success': '\033[92m',  # Green
        'error': '\033[91m',    # Red
        'info': '\033[94m',     # Blue
        'warning': '\033[93m'   # Yellow
    }
    reset = '\033[0m'
    
    symbol = symbols.get(status, 'ℹ')
    color = colors.get(status, '')
    
    print(f"{color}{symbol} {message}{reset}")


def check_environment_variables():
    """Check if Cloudinary environment variables are set"""
    print("\n" + "="*60)
    print("1. CHECKING ENVIRONMENT VARIABLES")
    print("="*60)
    
    required_vars = {
        'CLOUDINARY_CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
        'CLOUDINARY_API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
        'CLOUDINARY_API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            # Show partial value for security
            masked_value = var_value[:4] + '*' * (len(var_value) - 4) if len(var_value) > 4 else '***'
            print_status(f"{var_name}: {masked_value}", 'success')
        else:
            print_status(f"{var_name}: NOT SET", 'error')
            all_set = False
    
    return all_set


def check_django_settings():
    """Check Django settings for Cloudinary configuration"""
    print("\n" + "="*60)
    print("2. CHECKING DJANGO SETTINGS")
    print("="*60)
    
    # Check if cloudinary is in INSTALLED_APPS
    has_cloudinary = 'cloudinary' in settings.INSTALLED_APPS
    has_cloudinary_storage = 'cloudinary_storage' in settings.INSTALLED_APPS
    
    print_status(f"'cloudinary' in INSTALLED_APPS: {has_cloudinary}", 'success' if has_cloudinary else 'error')
    print_status(f"'cloudinary_storage' in INSTALLED_APPS: {has_cloudinary_storage}", 'success' if has_cloudinary_storage else 'error')
    
    # Check DEFAULT_FILE_STORAGE
    default_storage = getattr(settings, 'DEFAULT_FILE_STORAGE', None)
    if default_storage:
        is_cloudinary = 'cloudinary' in default_storage.lower()
        print_status(f"DEFAULT_FILE_STORAGE: {default_storage}", 'success' if is_cloudinary else 'warning')
    else:
        print_status("DEFAULT_FILE_STORAGE: NOT SET (will use default file system)", 'warning')
    
    # Check CLOUDINARY_STORAGE settings
    cloudinary_config = getattr(settings, 'CLOUDINARY_STORAGE', {})
    if cloudinary_config:
        print_status(f"CLOUDINARY_STORAGE configured: YES", 'success')
    else:
        print_status(f"CLOUDINARY_STORAGE configured: NO", 'warning')
    
    return has_cloudinary and has_cloudinary_storage


def test_cloudinary_connection():
    """Test connection to Cloudinary by attempting to upload a test image"""
    print("\n" + "="*60)
    print("3. TESTING CLOUDINARY CONNECTION")
    print("="*60)
    
    try:
        # Create a small test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        print_status("Uploading test image to Cloudinary...", 'info')
        
        # Upload test image
        result = cloudinary.uploader.upload(
            img_bytes,
            folder="test",
            public_id="diagnostic_test",
            overwrite=True
        )
        
        print_status("Upload successful!", 'success')
        print_status(f"Image URL: {result.get('secure_url')}", 'info')
        print_status(f"Public ID: {result.get('public_id')}", 'info')
        print_status(f"Format: {result.get('format')}", 'info')
        
        # Clean up test image
        print_status("Cleaning up test image...", 'info')
        cloudinary.uploader.destroy(result.get('public_id'))
        print_status("Test image deleted", 'success')
        
        return True
        
    except Exception as e:
        print_status(f"Connection failed: {str(e)}", 'error')
        return False


def check_existing_images():
    """Check if there are existing images in the database"""
    print("\n" + "="*60)
    print("4. CHECKING EXISTING IMAGES IN DATABASE")
    print("="*60)
    
    from bills.models import Bill
    from security_management.models import CustomUser
    
    # Check bills with receipt images
    bills_with_receipts = Bill.objects.exclude(receipt_image='').exclude(receipt_image__isnull=True)
    print_status(f"Bills with receipt images: {bills_with_receipts.count()}", 'info')
    
    if bills_with_receipts.exists():
        print("\nSample receipt URLs:")
        for bill in bills_with_receipts[:3]:
            url = bill.receipt_image.url if bill.receipt_image else 'N/A'
            is_cloudinary = 'cloudinary' in url.lower() if url != 'N/A' else False
            status = 'success' if is_cloudinary else 'warning'
            print_status(f"  - {bill.name}: {url}", status)
    
    # Check users with profile pictures
    users_with_photos = CustomUser.objects.exclude(profile_picture='').exclude(profile_picture__isnull=True)
    print_status(f"Users with profile pictures: {users_with_photos.count()}", 'info')
    
    if users_with_photos.exists():
        print("\nSample profile picture URLs:")
        for user in users_with_photos[:3]:
            url = user.profile_picture.url if user.profile_picture else 'N/A'
            is_cloudinary = 'cloudinary' in url.lower() if url != 'N/A' else False
            status = 'success' if is_cloudinary else 'warning'
            print_status(f"  - {user.username}: {url}", status)
    
    return bills_with_receipts.count(), users_with_photos.count()


def main():
    """Run all diagnostic tests"""
    print("\n" + "="*60)
    print("CLOUDINARY DIAGNOSTIC TOOL")
    print("="*60)
    
    # Run all checks
    env_ok = check_environment_variables()
    settings_ok = check_django_settings()
    
    if env_ok and settings_ok:
        connection_ok = test_cloudinary_connection()
        check_existing_images()
    else:
        print_status("\nCannot proceed with connection test due to configuration issues", 'error')
        connection_ok = False
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if env_ok and settings_ok and connection_ok:
        print_status("Cloudinary is properly configured and working!", 'success')
        print_status("\nIf images aren't showing:", 'info')
        print_status("  1. Images may have been uploaded before Cloudinary was configured", 'warning')
        print_status("  2. Check if image URLs contain 'cloudinary' in them", 'warning')
        print_status("  3. You may need to re-upload existing images", 'warning')
    else:
        print_status("There are configuration issues that need to be fixed", 'error')
    
    print("="*60 + "\n")


if __name__ == '__main__':
    main()

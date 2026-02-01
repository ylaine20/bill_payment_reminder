# Quick check for existing images
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bill_payment_reminder.settings')
django.setup()

from bills.models import Bill
from security_management.models import CustomUser

print("\n=== CHECKING EXISTING IMAGES ===\n")

# Check bills with receipts
bills_with_receipts = Bill.objects.exclude(receipt_image='').exclude(receipt_image__isnull=True)
print(f"Bills with receipt images: {bills_with_receipts.count()}")

if bills_with_receipts.exists():
    print("\nReceipt URLs:")
    for bill in bills_with_receipts[:5]:
        try:
            url = bill.receipt_image.url
            is_cloudinary = 'cloudinary' in url
            print(f"  - {bill.name}")
            print(f"    URL: {url}")
            print(f"    Cloudinary: {'YES ✓' if is_cloudinary else 'NO (Local) ✗'}\n")
        except Exception as e:
            print(f"  - {bill.name}: ERROR - {e}\n")

# Check users with profile pictures
users_with_photos = CustomUser.objects.exclude(profile_picture='').exclude(profile_picture__isnull=True)
print(f"\nUsers with profile pictures: {users_with_photos.count()}")

if users_with_photos.exists():
    print("\nProfile picture URLs:")
    for user in users_with_photos[:5]:
        try:
            url = user.profile_picture.url
            is_cloudinary = 'cloudinary' in url
            print(f"  - {user.username}")
            print(f"    URL: {url}")
            print(f"    Cloudinary: {'YES ✓' if is_cloudinary else 'NO (Local) ✗'}\n")
        except Exception as e:
            print(f"  - {user.username}: ERROR - {e}\n")

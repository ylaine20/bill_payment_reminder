"""
Migrate Local Images to Cloudinary
This script uploads existing local images to Cloudinary and updates the database.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bill_payment_reminder.settings')
django.setup()

from django.core.files import File
from bills.models import Bill
from security_management.models import CustomUser
import cloudinary
import cloudinary.uploader
from django.conf import settings


def migrate_bill_receipts():
    """Migrate bill receipt images from local storage to Cloudinary"""
    print("\n" + "="*60)
    print("MIGRATING BILL RECEIPTS TO CLOUDINARY")
    print("="*60 + "\n")
    
    # Get all bills with receipt images
    bills = Bill.objects.exclude(receipt_image='').exclude(receipt_image__isnull=True)
    
    if not bills.exists():
        print("No bills with receipts found.")
        return 0
    
    print(f"Found {bills.count()} bill(s) with receipt images\n")
    
    migrated = 0
    skipped = 0
    failed = 0
    
    for bill in bills:
        try:
            # Check if already on Cloudinary
            current_url = bill.receipt_image.url
            if 'cloudinary' in current_url:
                print(f"✓ SKIP: {bill.name} - Already on Cloudinary")
                skipped += 1
                continue
            
            # Get the local file path
            local_path = bill.receipt_image.path
            
            if not os.path.exists(local_path):
                print(f"✗ ERROR: {bill.name} - File not found: {local_path}")
                failed += 1
                continue
            
            print(f"→ Migrating: {bill.name}")
            print(f"  Local: {local_path}")
            
            # Upload to Cloudinary
            with open(local_path, 'rb') as img_file:
                result = cloudinary.uploader.upload(
                    img_file,
                    folder="receipts",
                    resource_type="auto"
                )
            
            # Update the bill's receipt_image field with cloudinary URL
            # The field stores the cloudinary public_id
            bill.receipt_image = result['public_id']
            bill.save()
            
            new_url = bill.receipt_image.url
            print(f"  Cloudinary URL: {new_url}")
            print(f"✓ SUCCESS: {bill.name}\n")
            migrated += 1
            
        except Exception as e:
            print(f"✗ ERROR: {bill.name} - {str(e)}\n")
            failed += 1
    
    print("="*60)
    print(f"Migration Summary:")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped (already on Cloudinary): {skipped}")
    print(f"  Failed: {failed}")
    print("="*60 + "\n")
    
    return migrated


def migrate_profile_pictures():
    """Migrate user profile pictures from local storage to Cloudinary"""
    print("\n" + "="*60)
    print("MIGRATING PROFILE PICTURES TO CLOUDINARY")
    print("="*60 + "\n")
    
    # Get all users with profile pictures
    users = CustomUser.objects.exclude(profile_picture='').exclude(profile_picture__isnull=True)
    
    if not users.exists():
        print("No users with profile pictures found.")
        return 0
    
    print(f"Found {users.count()} user(s) with profile pictures\n")
    
    migrated = 0
    skipped = 0
    failed = 0
    
    for user in users:
        try:
            # Check if already on Cloudinary
            current_url = user.profile_picture.url
            if 'cloudinary' in current_url:
                print(f"✓ SKIP: {user.username} - Already on Cloudinary")
                skipped += 1
                continue
            
            # Get the local file path
            local_path = user.profile_picture.path
            
            if not os.path.exists(local_path):
                print(f"✗ ERROR: {user.username} - File not found: {local_path}")
                failed += 1
                continue
            
            print(f"→ Migrating: {user.username}")
            print(f"  Local: {local_path}")
            
            # Upload to Cloudinary
            with open(local_path, 'rb') as img_file:
                result = cloudinary.uploader.upload(
                    img_file,
                    folder="profile_pics",
                    resource_type="auto"
                )
            
            # Update the user's profile_picture field
            user.profile_picture = result['public_id']
            user.save()
            
            new_url = user.profile_picture.url
            print(f"  Cloudinary URL: {new_url}")
            print(f"✓ SUCCESS: {user.username}\n")
            migrated += 1
            
        except Exception as e:
            print(f"✗ ERROR: {user.username} - {str(e)}\n")
            failed += 1
    
    print("="*60)
    print(f"Migration Summary:")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped (already on Cloudinary): {skipped}")
    print(f"  Failed: {failed}")
    print("="*60 + "\n")
    
    return migrated


def main():
    """Main migration function"""
    print("\n" + "="*70)
    print(" "*15 + "LOCAL TO CLOUDINARY MIGRATION TOOL")
    print("="*70)
    
    # Check if Cloudinary is configured
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    if not cloud_name:
        print("\n✗ ERROR: Cloudinary is not configured!")
        print("Please set CLOUDINARY_CLOUD_NAME environment variable")
        return
    
    print(f"\nCloudinary Cloud Name: {cloud_name}")
    print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
    
    # Confirm migration
    print("\n" + "="*70)
    response = input("Do you want to proceed with migration? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        return
    
    # Run migrations
    total_migrated = 0
    total_migrated += migrate_bill_receipts()
    total_migrated += migrate_profile_pictures()
    
    print("\n" + "="*70)
    print(f"TOTAL IMAGES MIGRATED: {total_migrated}")
    print("="*70)
    
    if total_migrated > 0:
        print("\n✓ Migration completed successfully!")
        print("\nNext steps:")
        print("  1. Test your hosted application")
        print("  2. Verify images are now visible")
        print("  3. If everything works, you can optionally delete local media files")
    else:
        print("\n⚠ No images were migrated.")
        print("Images may already be on Cloudinary or there might be an issue.")


if __name__ == '__main__':
    main()

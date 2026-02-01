"""
Simple script to upload local receipt images to Cloudinary
"""
import os
import cloudinary
import cloudinary.uploader
from pathlib import Path

# Configure Cloudinary
cloudinary.config(
    cloud_name="djed39cus",
    api_key="549725383441976",
    api_secret="Pa0g9H3sQJud7IMfL1J7VbIUwCo"
)

# Path to local receipts folder
receipts_dir = Path(r"c:\Users\Janna\OneDrive\Desktop\bill_payment_reminder\media\receipts")

print("="*70)
print(" "*20 + "UPLOADING RECEIPTS TO CLOUDINARY")
print("="*70)
print(f"\nScanning: {receipts_dir}\n")

# Get all image files
image_files = list(receipts_dir.glob("*.png")) + list(receipts_dir.glob("*.jpg")) + list(receipts_dir.glob("*.jpeg"))

if not image_files:
    print("No images found!")
else:
    print(f"Found {len(image_files)} image(s)\n")
    
    uploaded = []
    failed = []
    
    for img_file in image_files:
        try:
            print(f"→ Uploading: {img_file.name}")
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                str(img_file),
                folder="receipts",
                public_id=img_file.stem,  # Use filename without extension
                resource_type="auto",
                overwrite=True
            )
            
            cloudinary_url = result['secure_url']
            print(f"  ✓ SUCCESS")
            print(f"  URL: {cloudinary_url}\n")
            
            uploaded.append({
                'file': img_file.name,
                'url': cloudinary_url,
                'public_id': result['public_id']
            })
            
        except Exception as e:
            print(f"  ✗ FAILED: {e}\n")
            failed.append(img_file.name)
    
    # Summary
    print("="*70)
    print("UPLOAD SUMMARY")
    print("="*70)
    print(f"Successfully uploaded: {len(uploaded)}")
    print(f"Failed: {len(failed)}")
    
    if uploaded:
        print("\n" + "="*70)
        print("UPLOADED IMAGES - CLOUDINARY URLs:")
        print("="*70)
        for item in uploaded:
            print(f"\n{item['file']}")
            print(f"  Public ID: {item['public_id']}")
            print(f"  URL: {item['url']}")
    
    if failed:
        print("\nFailed files:")
        for f in failed:
            print(f"  - {f}")
    
    print("\n" + "="*70)
    print("IMPORTANT: Now you need to update database records")
    print("="*70)
    print("\nOption 1: On your hosted site (Render):")
    print("  1. Edit each bill")
    print("  2. Remove old receipt")
    print("  3. Re-upload from local (it will use Cloudinary)")
    print("\nOption 2: Update database manually:")
    print("  - Update Bill.receipt_image field with Cloudinary public_id")
    print("="*70)

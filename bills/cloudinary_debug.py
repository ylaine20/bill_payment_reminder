"""
Add a debug view to check Cloudinary configuration on the hosted environment
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
import os


@staff_member_required
def cloudinary_status(request):
    """
    Debug view to check if Cloudinary is properly configured
    """
    context = {
        'cloudinary_cloud_name': os.environ.get('CLOUDINARY_CLOUD_NAME', 'NOT SET'),
        'cloudinary_api_key': os.environ.get('CLOUDINARY_API_KEY', 'NOT SET'),
        'cloudinary_api_secret_set': 'YES' if os.environ.get('CLOUDINARY_API_SECRET') else 'NO',
        'default_file_storage': getattr(settings, 'DEFAULT_FILE_STORAGE', 'NOT SET'),
        'debug_mode': settings.DEBUG,
        'cloudinary_in_installed_apps': 'cloudinary' in settings.INSTALLED_APPS,
        'cloudinary_storage_in_installed_apps': 'cloudinary_storage' in settings.INSTALLED_APPS,
    }
    
    return render(request, 'bills/cloudinary_status.html', context)

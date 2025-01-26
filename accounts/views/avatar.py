import os
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.conf import settings
from django.urls import reverse
from ..models import RegistrationToken
import logging

# Avatar constants
MAX_AVATAR_SIZE = 10 * 1024 * 1024  # 10MB in bytes

logger = logging.getLogger(__name__)

def crop_avatar(request, token):
    """处理头像上传并显示裁剪界面"""
    registration_token = get_object_or_404(RegistrationToken, token=token)
    if not registration_token.is_valid():
        return redirect('accounts:register')
    
    # 生成临时文件名
    temp_filename = registration_token.subscriber.generate_filename()
    
    return render(request, 'accounts/crop_avatar.html', {
        'token': token,
        'temp_filename': temp_filename
    })

def save_avatar(request, token):
    """保存裁剪后的头像"""
    logger.info(f"Saving avatar for token: {token}")
    if request.method != 'POST':
        logger.error("Invalid request method")
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    # 验证token
    registration_token = get_object_or_404(RegistrationToken, token=token)
    if not registration_token.is_valid():
        logger.error(f"Invalid token: {token}")
        return JsonResponse({'success': False, 'error': 'Invalid token'})
    
    # 获取上传的文件
    avatar_file = request.FILES.get('avatar')
    temp_filename = request.POST.get('temp_filename')
    
    if not avatar_file:
        logger.error("No file uploaded")
        return JsonResponse({'success': False, 'error': 'No file uploaded'})
    
    # 验证文件类型和大小
    if not avatar_file.content_type.startswith('image/'):
        return JsonResponse({'success': False, 'error': 'Invalid file type'})
    
    if avatar_file.size > MAX_AVATAR_SIZE:
        return JsonResponse({
            'success': False, 
            'error': 'File too large. Maximum size is 10MB'
        })
    
    try:
        # 确保临时目录存在
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp', 'uploads')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 保存临时文件
        temp_path = os.path.join(temp_dir, temp_filename)
        with open(temp_path, 'wb+') as destination:
            for chunk in avatar_file.chunks():
                destination.write(chunk)
        
        logger.info(f"Avatar saved successfully: {temp_filename}")
        return JsonResponse({
            'success': True,
            'temp_filename': temp_filename,
            'redirect_url': f'/complete-registration/{token}/'
        })
        
    except Exception as e:
        logger.error(f"Error saving avatar: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}) 
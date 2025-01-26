from django.shortcuts import render, redirect
from django.http import JsonResponse
from PIL import Image
import os
from django.conf import settings
import uuid

def index(request):
    return render(request, 'photo_crop/index.html')

def upload_photo(request):
    if request.method == 'POST':
        photo = request.FILES.get('photo')
        
        if photo:
            # 生成临时文件名
            temp_filename = f"{uuid.uuid4()}.jpg"
            temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', temp_filename)
            
            # 确保temp目录存在
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            # 保存上传的图片到临时文件
            with open(temp_path, 'wb+') as destination:
                for chunk in photo.chunks():
                    destination.write(chunk)
            
            # 重定向到裁剪页面，传递参数
            return redirect(f'/photo_crop/crop/?file={temp_filename}')
    
    return redirect('photo_crop:index')

def crop_photo(request):
    return render(request, 'photo_crop/crop.html', {
        'file': request.GET.get('file')
    })

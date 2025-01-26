document.addEventListener('DOMContentLoaded', function() {
    let cropper = null;
    // 获取DOM元素
    const imageInput = document.getElementById('imageInput');
    const cropImage = document.getElementById('cropImage');
    const uploadPrompt = document.getElementById('uploadPrompt');
    const cropPreview = document.querySelector('.crop-preview');
    
    // 初始化裁剪器
    function initCropper(image) {
        cropper = new Cropper(image, {
            aspectRatio: 1,
            viewMode: 1,
            dragMode: 'move',
            autoCropArea: 1,
            cropBoxMovable: false,
            cropBoxResizable: false,
            guides: false,
            center: false,
            highlight: false,
            background: false,
            toggleDragModeOnDblclick: false,
        });
    }
    
    // 点击裁剪框时打开文件选择
    cropPreview.onclick = function() {
        if (!cropper) {
            imageInput.click();
        }
    };
    
    // 处理文件上传
    imageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                cropImage.src = e.target.result;
                
                // 隐藏上传提示
                uploadPrompt.style.display = 'none';
                
                if (cropper) {
                    cropper.destroy();
                }
                initCropper(cropImage);
            };
            reader.readAsDataURL(file);
        }
    });
    
    // 处理保存
    document.getElementById('saveCrop').addEventListener('click', function() {
        if (!cropper) {
            return;
        }
        
        const canvas = cropper.getCroppedCanvas({
            width: 200,    // 2inch at 100dpi
            height: 200,
            imageSmoothingEnabled: true,
            imageSmoothingQuality: 'high',
        });
        
        canvas.toBlob(function(blob) {
            const formData = new FormData();
            formData.append('avatar', blob, 'avatar.png');
            formData.append('temp_filename', TEMP_FILENAME);
            
            fetch(SAVE_AVATAR_URL, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': CSRF_TOKEN
                }
            })
            .then(response => {
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    window.location.href = data.redirect_url + '?temp_avatar=' + data.temp_filename;
                } else {
                    alert('Error saving avatar');
                }
            })
            .catch(error => {
                alert('Failed to save avatar. Please try again.');
            });
        }, 'image/png');
    });
}); 
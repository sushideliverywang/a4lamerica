from functools import wraps
from django.core.exceptions import PermissionDenied
from frontend.models_proxy import Staff
from django.shortcuts import redirect

def customer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')  # 确保使用正确的URL名称
        if request.user.is_staff:
            raise PermissionDenied("This feature is for customers only.")  # 更友好的错误消息
        return view_func(request, *args, **kwargs)
    return _wrapped_view

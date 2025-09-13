from django.core.exceptions import PermissionDenied

class AdminRequiredMixin:
    """确保只有管理员可以访问的 Mixin"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("You must be an administrator to access this page.")
        return super().dispatch(request, *args, **kwargs)
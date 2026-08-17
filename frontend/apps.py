from django.apps import AppConfig


class FrontendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'frontend'
    
    def ready(self):
        import frontend.templatetags.frontend_filters
        import frontend.signals  # 导入信号以注册购物车合并处理

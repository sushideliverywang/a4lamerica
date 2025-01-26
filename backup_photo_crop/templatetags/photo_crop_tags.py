from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def get_media_url(file_path):
    return f"{settings.MEDIA_URL}temp/{file_path}" 
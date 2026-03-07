from django.utils.timezone import now
from django.core.cache import cache

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, 'user', None) and request.user.is_authenticated:
            # 5 minutes idle time before considering it "offline"
            cache.set(f'seen_user_{request.user.id}', now(), 300)
        return self.get_response(request)

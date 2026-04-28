import time
import logging
from django.http import JsonResponse

logger = logging.getLogger('django.request')

class APIVersionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/') and not request.path.startswith('/api/auth/'):
            version = request.headers.get('X-API-Version')
            if not version or version != '1':
                return JsonResponse({'status': 'error', 'message': 'API version header required'}, status=400)
        return self.get_response(request)

class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration = time.time() - start
        logger.info(f"{request.method} {request.path} {response.status_code} {duration:.3f}s")
        return response
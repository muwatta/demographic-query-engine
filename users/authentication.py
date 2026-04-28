import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Try to get token from cookie (web) or Authorization header (CLI)
        token = request.COOKIES.get('access_token')
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if not token:
            return None
        
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            user = User.objects.get(id=payload['user_id'], is_active=True)
        except (jwt.InvalidTokenError, User.DoesNotExist):
            raise AuthenticationFailed('Invalid or expired token')
        
        return (user, token)
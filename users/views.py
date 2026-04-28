import logging
import requests
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_ratelimit.decorators import ratelimit

from .models import User
from .tokens import create_access_token, create_refresh_token, decode_token
from .oauth_helpers import (
    generate_code_verifier, generate_code_challenge, generate_state
)
from .permissions import IsAnalyst

logger = logging.getLogger(__name__)

# ---------- Helper ----------
def exchange_github_code_for_user(code, redirect_uri, code_verifier=None):
    """Exchange GitHub OAuth code for user instance (create/update)."""
    token_url = 'https://github.com/login/oauth/access_token'
    payload = {
        'client_id': settings.GITHUB_CLIENT_ID,
        'client_secret': settings.GITHUB_CLIENT_SECRET,
        'code': code,
        'redirect_uri': redirect_uri,
    }
    if code_verifier:
        payload['code_verifier'] = code_verifier
    
    headers = {'Accept': 'application/json'}
    resp = requests.post(token_url, data=payload, headers=headers, timeout=10)
    if resp.status_code != 200:
        logger.error(f"GitHub token exchange failed: {resp.text}")
        return None, "GitHub token exchange failed"
    
    github_token = resp.json().get('access_token')
    if not github_token:
        return None, "No access token from GitHub"
    
    user_info_resp = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'Bearer {github_token}'},
        timeout=10
    )
    if user_info_resp.status_code != 200:
        return None, "Failed to fetch GitHub user info"
    user_info = user_info_resp.json()
    
    user, created = User.objects.get_or_create(
        github_id=str(user_info['id']),
        defaults={
            'username': user_info['login'],
            'email': user_info.get('email', ''),
            'avatar_url': user_info.get('avatar_url', '')
        }
    )
    # Update fields if they changed (e.g., username renamed)
    if not created:
        user.username = user_info['login']
        user.email = user_info.get('email', user.email)
        user.avatar_url = user_info.get('avatar_url', user.avatar_url)
        user.save()
    
    if not user.is_active:
        return None, "User inactive"
    
    user.last_login_at = timezone.now()
    user.save(update_fields=['last_login_at'])
    
    return user, None

# ---------- Rate‑limited mixin ----------
class RateLimitedView(APIView):
    @method_decorator(ratelimit(key='ip', rate='10/m', method='ALL'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

# ---------- Web OAuth Start ----------
class GitHubAuthStartView(RateLimitedView):
    def get(self, request):
        state = generate_state()
        request.session['oauth_state'] = state
        redirect_uri = f"{settings.BASE_URL}/auth/github/callback"
        auth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
            f"&scope=read:user"
        )
        return HttpResponseRedirect(auth_url)

# ---------- Web OAuth Callback ----------
class GitHubCallbackView(RateLimitedView):
    def get(self, request):
        code = request.GET.get('code')
        state = request.GET.get('state')
        stored_state = request.session.pop('oauth_state', None)
        
        if not code or state != stored_state:
            logger.warning(f"OAuth state mismatch: {state} vs {stored_state}")
            return JsonResponse({'status': 'error', 'message': 'Invalid state'}, status=400)
        
        redirect_uri = f"{settings.BASE_URL}/auth/github/callback"
        user, error = exchange_github_code_for_user(code, redirect_uri)
        if error:
            return JsonResponse({'status': 'error', 'message': error}, status=500)
        
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        response = JsonResponse({
            'status': 'success',
            'access_token': access_token,
            'refresh_token': refresh_token
        })
        # Secure cookies: HttpOnly, Secure (if HTTPS), SameSite=Lax
        response.set_cookie(
            'access_token', access_token,
            httponly=True, secure=settings.USE_HTTPS, samesite='Lax',
            max_age=settings.ACCESS_TOKEN_LIFETIME_SECONDS
        )
        response.set_cookie(
            'refresh_token', refresh_token,
            httponly=True, secure=settings.USE_HTTPS, samesite='Lax',
            max_age=settings.REFRESH_TOKEN_LIFETIME_SECONDS
        )
        return response

# ---------- CLI OAuth Start (PKCE) ----------
class CLIAuthStartView(RateLimitedView):
    def get(self, request):
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier)
        state = generate_state()
        # Store both state and verifier for validation
        cache.set(f'pkce_{state}', {'verifier': verifier, 'state': state}, timeout=300)
        redirect_uri = f"{settings.BASE_URL}/auth/github/cli-callback"
        auth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
            f"&code_challenge={challenge}"
            f"&code_challenge_method=S256"
        )
        return JsonResponse({'auth_url': auth_url, 'state': state})

# ---------- CLI Callback (PKCE) ----------
class CLICallbackView(RateLimitedView):
    # csrf_exempt is not needed because we are not using SessionAuthentication
    def post(self, request):
        code = request.data.get('code')
        state = request.data.get('state')
        code_verifier = request.data.get('code_verifier')
        
        if not all([code, state, code_verifier]):
            return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)
        
        stored = cache.get(f'pkce_{state}')
        if not stored or stored.get('verifier') != code_verifier or stored.get('state') != state:
            logger.warning(f"PKCE validation failed for state {state}")
            return JsonResponse({'status': 'error', 'message': 'Invalid PKCE verifier or state'}, status=400)
        
        # Clean up cache
        cache.delete(f'pkce_{state}')
        
        redirect_uri = f"{settings.BASE_URL}/auth/github/cli-callback"
        user, error = exchange_github_code_for_user(code, redirect_uri, code_verifier)
        if error:
            return JsonResponse({'status': 'error', 'message': error}, status=500)
        
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        return JsonResponse({
            'status': 'success',
            'access_token': access_token,
            'refresh_token': refresh_token
        })

# ---------- Refresh Token (with invalidation) ----------
class RefreshTokenView(RateLimitedView):
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({'status': 'error', 'message': 'refresh_token required'}, status=400)
        
        # Decode without verification first to check blacklist? We'll rely on decode_token
        payload = decode_token(refresh_token)
        if not payload:
            return Response({'status': 'error', 'message': 'Invalid refresh token'}, status=401)
        
        # Optional: check if token is blacklisted (simplified – can use cache or DB)
        blacklist_key = f'token_blacklist:{refresh_token}'
        if cache.get(blacklist_key):
            return Response({'status': 'error', 'message': 'Token revoked'}, status=401)
        
        try:
            user = User.objects.get(id=payload['user_id'], is_active=True)
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': 'User not found'}, status=401)
        
        # Invalidate the old refresh token (add to blacklist)
        cache.set(blacklist_key, True, timeout=settings.REFRESH_TOKEN_LIFETIME_SECONDS)
        
        new_access = create_access_token(user.id)
        new_refresh = create_refresh_token(user.id)
        return Response({
            'status': 'success',
            'access_token': new_access,
            'refresh_token': new_refresh
        })

# ---------- Logout (revoke tokens) ----------
class LogoutView(APIView):
    def post(self, request):
        # Invalidate refresh token if present
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            cache.set(f'token_blacklist:{refresh_token}', True, timeout=settings.REFRESH_TOKEN_LIFETIME_SECONDS)
        
        response = Response({'status': 'success'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

# ---------- User Info (for authenticated users) ----------
class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]  # Changed from IsAnalyst (adjust as needed)
    def get(self, request):
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'role': request.user.role,
            'email': request.user.email,
            'avatar_url': request.user.avatar_url
        })
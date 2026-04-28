from django.urls import path
from .views import (
    GitHubAuthStartView, GitHubCallbackView,
    CLIAuthStartView, CLICallbackView,
    RefreshTokenView, LogoutView, UserInfoView
)

urlpatterns = [
    path('auth/github/', GitHubAuthStartView.as_view()),
    path('auth/github/callback/', GitHubCallbackView.as_view()),
    path('auth/github/cli/', CLIAuthStartView.as_view()),
    path('auth/github/cli-callback/', CLICallbackView.as_view()),
    path('auth/refresh/', RefreshTokenView.as_view()),
    path('auth/logout/', LogoutView.as_view()),
    path('auth/me/', UserInfoView.as_view()),
]
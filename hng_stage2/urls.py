from django.urls import path, include
from profiles.views import ProfileListView, NaturalLanguageSearchView, ProfileDetailView, ProfileExportView, health_check, ProfileCreateView

urlpatterns = [
    path('', include('users.urls')),
    path('api/health/', health_check),
    path('api/profiles/', ProfileListView.as_view()),
    path('api/profiles/search/', NaturalLanguageSearchView.as_view()),
    path('api/profiles/export/', ProfileExportView.as_view()),
    path('api/profiles/<uuid:id>/', ProfileDetailView.as_view()),
    path('api/profiles/create/', ProfileCreateView.as_view()),
]
from django.urls import path
from profiles.views import ProfileListView, NaturalLanguageSearchView, ProfileDetailView, SeedDatabaseView

urlpatterns = [
    path('api/profiles/', ProfileListView.as_view(), name='profiles-list'),
    path('api/profiles/search/', NaturalLanguageSearchView.as_view(), name='profiles-search'),
    path('api/profiles/<uuid:id>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('api/seed/', SeedDatabaseView.as_view(), name='seed-database'),
]
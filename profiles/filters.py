import django_filters
from .models import Profile

class ProfileFilter(django_filters.FilterSet):
    min_age = django_filters.NumberFilter(field_name='age', lookup_expr='gte')
    max_age = django_filters.NumberFilter(field_name='age', lookup_expr='lte')
    min_gender_probability = django_filters.NumberFilter(field_name='gender_probability', lookup_expr='gte')
    min_country_probability = django_filters.NumberFilter(field_name='country_probability', lookup_expr='gte')

    class Meta:
        model = Profile
        fields = {
            'gender': ['exact'],
            'age_group': ['exact'],
            'country_id': ['exact'],
        }
from rest_framework import serializers
from .models import Profile

class ProfileDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

class ProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'name', 'gender', 'age', 'age_group', 'country_id', 'country_name', 'created_at']
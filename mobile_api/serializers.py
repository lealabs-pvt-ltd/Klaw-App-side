from rest_framework import serializers
from .models import AppUser

class AppUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = [
            'full_name',
            'college',
            'email',
            'department',
            'university',
            'blood_group',
            'profile_pic',
            'subscription_plan',
        ]
        read_only_fields = ['phone_number']

from rest_framework import serializers
from django.contrib.auth.hashers import check_password, make_password
from .models import AppUser, CourseProxy, CourseBasicInfoProxy, BlogProxy, NotificationProxy, News, NotificationReadStatus

# --- Unchanged: AppUserSerializer ---
class AppUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = [
            'full_name',
            'phone_number',
            'college',
            'email',
            'referral_code',
            'department',
            'university',
            'blood_group',
            'profile_pic',
            'subscription_plan',
            'year_of_study',
        ]

# --- Unchanged: EditProfileSerializer ---
class EditProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = [
            'full_name',
            'phone_number',
            'college',
            'email',
            'department',
            'university',
            'blood_group',
            'subscription_plan',
            'year_of_study',
        ]
        extra_kwargs = {
            'email': {'required': False},
            'phone_number': {'required': False},
        }

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            if value is not None:
                setattr(instance, field, value)
        instance.save()
        return instance

# --- Unchanged: UpdatePasswordSerializer ---
class UpdatePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        if not check_password(data['old_password'], user.password):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"new_password": "New passwords do not match."})
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.password = make_password(self.validated_data['new_password'])
        user.save()
        return user

# --- Unchanged: NewsSerializer ---
class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'date', 'content', 'last_updated']

# --- Unchanged: CourseSerializer ---
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseBasicInfoProxy
        fields = ['_id', 'title', 'course_code', 'year', 'branch', 'semester', 'group', 'created_at', 'updated_at']

# --- Unchanged: BlogSerializer ---
class BlogSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = BlogProxy
        fields = ['id', 'title', 'author', 'category', 'status', 'created_at', 'html_code']

# --- Unchanged: BlogDetailSerializer ---
class BlogDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = BlogProxy
        fields = ['id', 'title', 'author', 'category', 'html_code', 'status', 'created_at']

# --- Updated: NotificationSerializer to include read status ---
class NotificationSerializer(serializers.ModelSerializer):
    read = serializers.SerializerMethodField()

    class Meta:
        model = NotificationProxy
        fields = ['id', 'title', 'message', 'created_at', 'read']

    def get_read(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return NotificationReadStatus.objects.filter(
            user=user, notification_id=obj.id, read=True
        ).exists()
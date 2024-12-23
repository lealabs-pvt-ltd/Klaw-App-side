from django.db import models
from djongo import models 
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.models import AbstractUser, Group, Permission

def get_default_expiry_time():
    return now() + timedelta(minutes=5)

class OTP(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=6)
    expiry_time = models.DateTimeField(default=get_default_expiry_time)  # Use the function here

    def is_valid(self):
        return now() <= self.expiry_time

class AppUser(AbstractUser):
    groups = models.ManyToManyField(Group, related_name='appuser_groups', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='appuser_permissions', blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True) 
    phone_number = models.CharField(max_length=15, unique=True)
    college = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    university = models.CharField(max_length=100, null=True, blank=True)
    blood_group = models.CharField(max_length=3, null=True, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    subscription_plan = models.CharField(
        max_length=50, 
        choices=[('Plan 1', 'Plan 1'), ('Plan 2', 'Plan 2'), ('Plan 3', 'Plan 3')], 
        default='Plan 1'
    )

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email']

class CourseProxy(models.Model):
    class Meta:
        managed = False  # Prevent Django from trying to create/migrate this model
        db_table = 'admin_panel_course'  # Specify the actual table name in the database

    _id = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=255)
    course_code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    university = models.CharField(max_length=255)
    file_input = models.JSONField(default=list)
    vectorized_data = models.JSONField(default=dict)
    status = models.CharField(max_length=10)

    def __str__(self):
        return self.title


from djongo import models

class PreferredSubject(models.Model):
    user = models.ForeignKey('AppUser', on_delete=models.CASCADE, related_name='preferred_subjects')
    course_code = models.CharField(max_length=255)  # Store course_code directly here
    added_on = models.DateTimeField(auto_now_add=True)

    # class Meta:
    #     unique_together = ('user', 'course_code')  # Ensure unique course_code for each user

    def __str__(self):
        return f"{self.user.phone_number} - {self.course_code}"


class ChatHistory(models.Model):
    user = models.ForeignKey('AppUser', on_delete=models.CASCADE, related_name="chat_histories")
    course_code = models.CharField(max_length=50)  # Make sure course_code is defined
    question = models.TextField()
    answer = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat history for {self.course_code} by {self.user}"
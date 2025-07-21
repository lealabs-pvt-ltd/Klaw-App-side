from django.db import models
from djongo import models
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.crypto import get_random_string
from django.utils import timezone

def get_default_expiry_time():
    return now() + timedelta(minutes=5)

class OTP(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=6)
    expiry_time = models.DateTimeField(default=get_default_expiry_time)

    def is_valid(self):
        return now() <= self.expiry_time

class AppUser(AbstractUser):
    groups = models.ManyToManyField(Group, related_name='appuser_groups', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='appuser_permissions', blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    year_of_study = models.CharField(
        max_length=10,
        choices=[('1st year', '1st year'), ('2nd year', '2nd year'), ('3rd year', '3rd year'), ('4th year', '4th year')],
        null=True,
        blank=True
    )
    full_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True)
    college = models.CharField(max_length=100, null=True, blank=True)
    referral_code = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    university = models.CharField(max_length=100, null=True, blank=True)
    blood_group = models.CharField(max_length=3, null=True, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    subscription_plan = models.CharField(
        max_length=50,
        choices=[('Basic', 'Basic'), ('Beginner', 'Beginner'), ('Advanced', 'Advanced')],
        default='Basic'
    )
    status = models.CharField(
        max_length=20,
        choices=[('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='rejected'
    )

    def save(self, *args, **kwargs):
        self.full_name = f"{self.first_name} {self.last_name}" if self.first_name and self.last_name else None
        if not self.username:
            first_part = self.first_name[:5] if self.first_name else "user"
            last_digits = self.phone_number[-3:] if self.phone_number else get_random_string(3, '0123456789')
            self.username = f"{first_part}{last_digits}".lower()
        super().save(*args, **kwargs)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email']

class DailyQuery(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    word_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.full_name} - {self.date}: {self.word_count} words"

# --- Unchanged: CourseProxy for admin_panel_course ---
class CourseProxy(models.Model):
    class Meta:
        managed = False
        db_table = 'admin_panel_course'

    _id = models.CharField(max_length=255, primary_key=True)
    course_code = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=[('draft', 'Draft'), ('published', 'Published')])
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    def __str__(self):
        return self.course_code

# --- Unchanged: CourseBasicInfoProxy for admin_panel_coursebasicinfo ---
class CourseBasicInfoProxy(models.Model):
    class Meta:
        managed = False
        db_table = 'admin_panel_coursebasicinfo'

    _id = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=255, db_column='course_name')  # Map course_name to title
    course_code = models.CharField(max_length=50, unique=True)
    year = models.IntegerField()
    branch = models.CharField(max_length=100)
    semester = models.IntegerField()
    group = models.CharField(max_length=100)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    def __str__(self):
        return self.title

# --- Unchanged: BlogProxy for admin_panel_blog ---
class BlogProxy(models.Model):
    class Meta:
        managed = False
        db_table = 'admin_panel_blog'

    id = models.IntegerField(primary_key=True)  # Use integer id to match admin_panel Blog
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    html_code = models.TextField()
    status = models.CharField(max_length=20, choices=[('draft', 'Draft'), ('publish', 'Published')])
    created_at = models.DateTimeField()

    def __str__(self):
        return self.title

# --- Unchanged: NotificationProxy for admin_panel_notification ---
class NotificationProxy(models.Model):
    class Meta:
        managed = False
        db_table = 'admin_panel_notification'

    #_id = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField()

    def __str__(self):
        return self.title

# --- New: NotificationReadStatus to track read status per user ---
class NotificationReadStatus(models.Model):
    user = models.ForeignKey('AppUser', on_delete=models.CASCADE, related_name='notification_read_statuses')
    notification_id = models.IntegerField()  # References NotificationProxy id
    read = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'notification_id')

    def __str__(self):
        return f"{self.user.phone_number} - Notification {self.notification_id}: {'Read' if self.read else 'Unread'}"

class PreferredSubject(models.Model):
    user = models.ForeignKey('AppUser', on_delete=models.CASCADE, related_name='preferred_subjects')
    course_code = models.CharField(max_length=255)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.phone_number} - {self.course_code}"

class ChatHistory(models.Model):
    user = models.ForeignKey('AppUser', on_delete=models.CASCADE, related_name="chat_histories")
    course_code = models.CharField(max_length=50)
    question = models.TextField()
    answer = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat history for {self.course_code} by {self.user}"

class News(models.Model):
    title = models.CharField(max_length=255, unique=True)
    date = models.CharField(max_length=100, blank=True)
    content = models.TextField(blank=True)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
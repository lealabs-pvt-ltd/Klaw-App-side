from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    RequestOTP, VerifyOTP, SignUpPartOne, SignUpPartTwo, LoginWithOTP, 
    LoginWithPassword, ResetPassword, UserProfileView, UpdateProfilePicView, 
    get_ktu_news, PreferredSubjectsView, AddPreferredSubjectView,
    AvailableSubjectsView, SubjectDetailView,
    ChatView, GetUserStatusView, UpdateProfileAndPasswordView,
    ResendOTP, AddNewsView, BlogListView, BlogDetailView, NotificationHistoryView,
    ToggleNotificationReadStatusView,
)

urlpatterns = [
    path('request-otp/', RequestOTP.as_view(), name='request_otp'),
    path('verify-otp/', VerifyOTP.as_view(), name='verify_otp'),
    path('resend-otp/', ResendOTP.as_view(), name='resend-otp'),
    path('signup/part1/', SignUpPartOne.as_view(), name='signup_part1'),
    path('signup/part2/', SignUpPartTwo.as_view(), name='signup_part2'),
    path('login-otp/', LoginWithOTP.as_view(), name='login_with_otp'),
    path('login-password/', LoginWithPassword.as_view(), name='login_with_password'),
    path('reset-password/', ResetPassword.as_view(), name='reset_password'),
    path('user-profile/', UserProfileView.as_view(), name='user_profile'),
    path('update-profile-pic/', UpdateProfilePicView.as_view(), name='update_profile_pic'),
    path('preferred-subjects/', PreferredSubjectsView.as_view(), name='preferred_subjects'),
    path('add-preferred-subject/', AddPreferredSubjectView.as_view(), name='add_preferred_subjects'),
    path('available-subjects/', AvailableSubjectsView.as_view(), name='available_subjects'),
    path('subject-detail/<str:course_code>/', SubjectDetailView.as_view(), name='subject_detail'),
    path('chat/<str:course_code>/', ChatView.as_view(), name='chat'),
    path('user/status/', GetUserStatusView.as_view(), name='get_user_status'),
    path('editprofile/', UpdateProfileAndPasswordView.as_view(), name='edit_profile'),
    path('ktu-news/', get_ktu_news, name='get_ktu_news'),
    path('add-ktu-news/', AddNewsView.as_view(), name='add_ktu_news'),
    path('blogs/', BlogListView.as_view(), name='blog-list'),
    path('blog/<int:id>/', BlogDetailView.as_view(), name='blog-detail'),
    path('notifications/', NotificationHistoryView.as_view(), name='notification-history'),
    path('toggle-notification-read/', ToggleNotificationReadStatusView.as_view(), name='toggle_notification_read'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
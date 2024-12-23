# urls.py
from django.urls import path
from .views import RequestOTP, VerifyOTP, SignUpPartOne, SignUpPartTwo,LoginWithOTP, LoginWithPassword, ResetPassword, UserProfileView, UpdateProfilePicView
from .views import (
    PreferredSubjectsView,
    AddPreferredSubjectView,
    RemovePreferredSubjectView,
    AvailableSubjectsView,
    SubjectDetailView,
    ChatView,
)
urlpatterns = [
    path('request-otp/', RequestOTP.as_view(), name='request_otp'),
    path('verify-otp/', VerifyOTP.as_view(), name='verify_otp'),
    path('signup/part1/', SignUpPartOne.as_view(), name='signup_part1'),
    path('signup/part2/', SignUpPartTwo.as_view(), name='signup_part2'),
    path('login-otp/', LoginWithOTP.as_view(), name='login_with_otp'),
    path('login-password/', LoginWithPassword.as_view(), name='login_with_password'),
    path('reset-password/', ResetPassword.as_view(), name='reset_password'),
    path('user-profile/', UserProfileView.as_view(), name='user_profile'),
    path('update-profile-pic/', UpdateProfilePicView.as_view(), name='update_profile_pic'),
    path('preferred-subjects/', PreferredSubjectsView.as_view(), name='preferred_subjects'),
    path('add-preferred-subject/', AddPreferredSubjectView.as_view(), name='add_preferred_Subjects'),
    path('remove-preferred-subject/<str:course_code>/', RemovePreferredSubjectView.as_view(), name='remove_preferred_Subjects'),
    path('available-subjects/', AvailableSubjectsView.as_view(), name='available_subjects'),
    path('subject-detail/<str:course_code>/', SubjectDetailView.as_view(), name='subject_detail'),
    path('chat/<str:course_code>/', ChatView.as_view(), name='chat'),
    
]

from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
import http.client
import json
import random
import time
import os
import logging
import requests
from dotenv import load_dotenv
from .models import AppUser, OTP, PreferredSubject, CourseProxy, CourseBasicInfoProxy, ChatHistory, DailyQuery, News, BlogProxy, NotificationProxy, NotificationReadStatus
from .serializers import AppUserSerializer, EditProfileSerializer, UpdatePasswordSerializer, NewsSerializer, CourseSerializer, BlogSerializer, BlogDetailSerializer, NotificationSerializer
from .scrap import update_news

# Load environment variables
load_dotenv()

# MSG91 Configuration
MSG91_AUTH_KEY = os.getenv("MSG91_AUTH_KEY")
TEMPLATE_ID = os.getenv("MSG91_TEMPLATE_ID")
OTP_EXPIRY = int(os.getenv("OTP_EXPIRY", 5))
# AI API Configuration
AI_API_URL = os.getenv("AI_API_URL", "http://127.0.0.1:5000/api/user_request")
# KTU News API Configuration
KTU_NEWS_API_URL = os.getenv("KTU_NEWS_API_URL", "https://ktu.api.lealabs.in/api/data")
logger = logging.getLogger(__name__)

# Rotating User-Agent list to mimic organic traffic
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/117.0.2045.36 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
]

# --- Updated: News Update Functions ---
def extract_data():
    """Fetch data from KTU news API with rotating User-Agent and random delay."""
    try:
        # Add random delay (1–3 seconds) to mimic human behavior
        time.sleep(random.uniform(1, 3))
        headers = {
            "User-Agent": random.choice(USER_AGENTS)
        }
        response = requests.get(KTU_NEWS_API_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching KTU news API: Status {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch KTU news API: {str(e)}")
        return []
    except ValueError as e:
        logger.error(f"Invalid JSON response from KTU news API: {str(e)}")
        return []

def update_news():
    """Update News table with data from KTU news API."""
    # Check if last update was more than 12 hours ago
    last_update = News.objects.first()
    if last_update and timezone.now() - last_update.last_updated < timedelta(hours=12):
        logger.debug("Skipping news update: Last update within 12 hours")
        return

    # Fetch data
    data = extract_data()
    if not data:
        logger.warning("No data fetched from KTU news API")
        return

    # Clear existing news
    News.objects.all().delete()

    # Prepare new data (up to 10 items)
    news_items = []
    for item in data[:10]:
        try:
            news_item = {
                "title": item["TITLE"],
                "content": item["CONTENT"],
                "date": item["DATE"],  # Store as string, e.g., "Tuesday, July 8, 2025"
                "last_updated": timezone.now()
            }
            serializer = NewsSerializer(data=news_item)
            if serializer.is_valid():
                news_items.append(News(**serializer.validated_data))
            else:
                logger.error(f"Failed to validate news item '{item['TITLE']}': {serializer.errors}")
        except (KeyError, ValueError) as e:
            logger.error(f"Error processing news item '{item.get('TITLE', 'Unknown')}': {str(e)}")
            continue

    # Bulk create to optimize database performance
    if news_items:
        News.objects.bulk_create(news_items)
        logger.info(f"Successfully updated {len(news_items)} news items from KTU API")
        # Invalidate cache to ensure fresh data
        cache.delete('ktu_news')

# --- Unchanged: Utility Functions ---
def send_otp_via_msg91(phone_number, otp):
    conn = http.client.HTTPSConnection("control.msg91.com")
    payload = json.dumps({
        "template_id": TEMPLATE_ID,
        "mobile": phone_number,
        "authkey": MSG91_AUTH_KEY,
        "otp": otp,
        "otp_expiry": OTP_EXPIRY,
        "realTimeResponse": 1
    })
    headers = {"Content-Type": "application/JSON"}
    conn.request("POST", "/api/v5/otp", payload, headers)
    res = conn.getresponse()
    return json.loads(res.read().decode("utf-8"))

def verify_otp_via_msg91(phone_number, otp):
    conn = http.client.HTTPSConnection("control.msg91.com")
    headers = {"authkey": MSG91_AUTH_KEY}
    conn.request("GET", f"/api/v5/otp/verify?otp={otp}&mobile={phone_number}", headers=headers)
    res = conn.getresponse()
    return json.loads(res.read().decode("utf-8"))

def resend_otp_via_msg91(phone_number, retry_type="text"):
    conn = http.client.HTTPSConnection("control.msg91.com")
    conn.request("GET", f"/api/v5/otp/retry?authkey={MSG91_AUTH_KEY}&mobile={phone_number}&retrytype={retry_type}")
    res = conn.getresponse()
    return json.loads(res.read().decode("utf-8"))

# --- Unchanged: OTP Views ---
class RequestOTP(APIView):
    permission_classes = []
    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)
        otp = str(random.randint(100000, 999999))
        cache.set(phone_number, otp, timeout=300)
        request.session['phone_number'] = phone_number
        try:
            response = send_otp_via_msg91(phone_number, otp)
            if response.get("type") == "success":
                return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)
            return Response({"error": response.get("message", "Failed to send OTP.")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Failed to send OTP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyOTP(APIView):
    permission_classes = []
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        if not phone_number:
            return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not otp:
            return Response({"error": "OTP is required."}, status=status.HTTP_400_BAD_REQUEST)
        cached_otp = cache.get(phone_number)
        if cached_otp == otp:
            try:
                response = verify_otp_via_msg91(phone_number, otp)
                if response.get("type") == "success":
                    return Response({"message": "OTP verified."}, status=status.HTTP_200_OK)
                return Response({"error": response.get("message", "Invalid OTP.")}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": f"Failed to verify OTP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

class ResendOTP(APIView):
    permission_classes = []
    def post(self, request):
        phone_number = request.data.get('phone_number')
        retry_type = request.data.get('retry_type', "text")
        if not phone_number:
            return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            response = resend_otp_via_msg91(phone_number, retry_type)
            if response.get("type") == "success":
                return Response({"message": "OTP resent successfully."}, status=status.HTTP_200_OK)
            return Response({"error": response.get("message", "Failed to resend OTP.")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Failed to resend OTP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Unchanged: Authentication Views ---
class SignUpPartOne(APIView):
    permission_classes = []
    def post(self, request):
        data = request.data
        password = data.get('password')
        phone_number = data.get('phone_number')
        request.session['user_data'] = {
            "first_name": data.get('first_name'),
            "last_name": data.get('last_name'),
            "email": data.get('email'),
            "password": make_password(password),
            "phone_number": phone_number
        }
        return Response({"message": "Part 1 complete."}, status=status.HTTP_200_OK)

class SignUpPartTwo(APIView):
    permission_classes = []
    def post(self, request):
        data = request.data
        required_fields = ['first_name', 'last_name', 'email', 'password', 'phone_number', 'year_of_study']
        if not all(data.get(field) for field in required_fields):
            return Response({"error": "All required fields must be provided."}, status=status.HTTP_400_BAD_REQUEST)
        if AppUser.objects.filter(phone_number=data.get('phone_number')).exists():
            return Response({"error": "Phone number already registered."}, status=status.HTTP_400_BAD_REQUEST)
        user = AppUser.objects.create(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            password=make_password(data.get('password')),
            phone_number=data.get('phone_number'),
            year_of_study=data.get('year_of_study'),
            subscription_plan=data.get('subscription_plan', 'Basic'),
            college=data.get('college'),
            department=data.get('department'),
            university=data.get('university'),
            blood_group=data.get('blood_group'),
            referral_code=data.get('referral_code'),
        )
        return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)

class LoginWithOTP(APIView):
    permission_classes = []
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        if not phone_number:
            return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not otp:
            return Response({"error": "OTP is required."}, status=status.HTTP_400_BAD_REQUEST)
        cached_otp = cache.get(phone_number)
        if cached_otp == otp:
            try:
                response = verify_otp_via_msg91(phone_number, otp)
                if response.get("type") == "success":
                    try:
                        user = AppUser.objects.get(phone_number=phone_number)
                        refresh = RefreshToken.for_user(user)
                        return Response({
                            'access_token': str(refresh.access_token),
                            'refresh_token': str(refresh)
                        }, status=status.HTTP_200_OK)
                    except AppUser.DoesNotExist:
                        return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
                return Response({"error": response.get("message", "Invalid OTP.")}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": f"Failed to verify OTP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

class LoginWithPassword(APIView):
    permission_classes = []
    def post(self, request):
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        try:
            user = AppUser.objects.get(phone_number=phone_number)
            if check_password(password, user.password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh)
                }, status=status.HTTP_200_OK)
            return Response({"error": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
        except AppUser.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)

class ResetPassword(APIView):
    permission_classes = []
    def post(self, request):
        phone_number = request.data.get('phone_number')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        if not phone_number:
            return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not new_password or not confirm_password:
            return Response({"error": "Both new_password and confirm_password are required."}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = AppUser.objects.get(phone_number=phone_number)
            user.password = make_password(new_password)
            user.save()
            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
        except AppUser.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)

# --- Unchanged: Profile Management Views ---
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "User is not authenticated."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = AppUserSerializer(request.user)
        data = serializer.data
        profile_pic_url = data.get('profile_pic')
        if profile_pic_url:
            data['profile_pic'] = request.build_absolute_uri(profile_pic_url)
        return Response(data, status=status.HTTP_200_OK)

class UpdateProfileAndPasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request):
        user = request.user
        profile_fields = ['phone_number', 'email', 'department', 'blood_group', 'year_of_study']
        for field in profile_fields:
            value = request.data.get(field)
            if value is not None and value.strip() != "":
                setattr(user, field, value)
        full_name = request.data.get('full_name')
        if full_name is not None and full_name.strip() != "":
            names = full_name.strip().split(" ", 1)
            user.first_name = names[0]
            user.last_name = names[1] if len(names) > 1 else ""
            user.full_name = full_name
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        if old_password and new_password and confirm_password:
            if not check_password(old_password, user.password):
                return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            if new_password != confirm_password:
                return Response({"error": "New password and confirm password do not match."}, status=status.HTTP_400_BAD_REQUEST)
            user.password = make_password(new_password)
        try:
            user.save()
            return Response({"message": "Profile and password updated successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateProfilePicView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def patch(self, request):
        user = request.user
        profile_pic = request.FILES.get('profile_pic')
        if profile_pic:
            user.profile_pic = profile_pic
            user.save()
            return Response({"message": "Profile picture updated successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "Profile picture file not provided."}, status=status.HTTP_400_BAD_REQUEST)

# --- Unchanged: PreferredSubjectsView ---
class PreferredSubjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve the user's preferred subjects with title from CourseBasicInfoProxy."""
        user = request.user
        preferred_subjects = PreferredSubject.objects.filter(user=user)
        data = []

        for ps in preferred_subjects:
            logger.debug(f"Processing PreferredSubject ID: {ps.id}, Course Code: {ps.course_code}")
            try:
                course = CourseProxy.objects.get(course_code=ps.course_code, status="published")
                try:
                    basic_info = CourseBasicInfoProxy.objects.get(course_code=ps.course_code)
                    data.append({
                        "title": basic_info.title,
                        "course_code": course.course_code,
                    })
                    logger.debug(f"Course found: {basic_info.title}, {course.course_code}")
                except CourseBasicInfoProxy.DoesNotExist:
                    logger.warning(f"No CourseBasicInfoProxy for course_code: {ps.course_code}")
                    data.append({
                        "title": None,
                        "course_code": course.course_code,
                    })
            except CourseProxy.DoesNotExist:
                logger.error(f"Course not found for PreferredSubject ID: {ps.id}, User: {user.phone_number}")
            except Exception as e:
                logger.error(f"Error processing PreferredSubject ID: {ps.id} - {str(e)}")

        logger.debug(f"Returning data: {data}")
        return Response(data, status=status.HTTP_200_OK)

# --- Unchanged: AddPreferredSubjectView ---
class AddPreferredSubjectView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        course_code = request.data.get("course_code")
        preferred = request.data.get("preferred")
        
        if not course_code:
            return Response({"error": "Course code is required."}, status=status.HTTP_400_BAD_REQUEST)
        if preferred is None:
            return Response({"error": "Preferred status (true/false) is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            course = CourseProxy.objects.get(course_code=course_code, status="published")
            preferred_subject = PreferredSubject.objects.filter(user=user, course_code=course_code).first()
            
            if preferred is True:
                if preferred_subject:
                    return Response({"message": "Subject is already in your preferred list."}, status=status.HTTP_200_OK)
                PreferredSubject.objects.create(user=user, course_code=course_code)
                return Response({"message": "Subject added to preferred list."}, status=status.HTTP_201_CREATED)
            else:
                if not preferred_subject:
                    return Response({"message": "Subject is not in your preferred list."}, status=status.HTTP_200_OK)
                preferred_subject.delete()
                return Response({"message": "Subject removed from preferred list."}, status=status.HTTP_200_OK)
                
        except CourseProxy.DoesNotExist:
            return Response({"error": "Course not found or not published."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in AddPreferredSubjectView: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Unchanged: AvailableSubjectsView ---
class AvailableSubjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve all available published subjects with full details from CourseBasicInfoProxy."""
        try:
            # Get all published courses from CourseProxy
            published_courses = CourseProxy.objects.filter(status="published")
            # Get course codes of published courses
            published_course_codes = published_courses.values_list('course_code', flat=True)
            # Fetch corresponding CourseBasicInfoProxy entries
            subjects = CourseBasicInfoProxy.objects.filter(course_code__in=published_course_codes)
            serializer = CourseSerializer(subjects, many=True)
            logger.info(f"Retrieved {len(subjects)} published subjects")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in AvailableSubjectsView: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Unchanged: SubjectDetailView ---
class SubjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_code):
        """Retrieve details for a specific course with title from CourseBasicInfoProxy."""
        try:
            course = CourseProxy.objects.get(course_code=course_code, status="published")
            serializer = CourseSerializer(course)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CourseProxy.DoesNotExist:
            return Response({"error": "Course not found or not published."}, status=status.HTTP_404_NOT_FOUND)

# --- Unchanged: ChatView ---
class ChatView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, course_code):
        """Handle chat queries by calling external AI API and storing response."""
        user_question = request.data.get("query")
        previous_question_rating = request.data.get("previous_question_rating", "nil")
        
        if not user_question:
            return Response({"error": "Query is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        word_count = len(user_question.split())
        try:
            # Verify course exists
            course = CourseProxy.objects.filter(course_code=course_code).first()
            if not course:
                return Response({"error": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Fetch subject title from CourseBasicInfoProxy
            try:
                basic_info = CourseBasicInfoProxy.objects.get(course_code=course_code)
                subject_title = basic_info.title
            except CourseBasicInfoProxy.DoesNotExist:
                logger.warning(f"No CourseBasicInfoProxy for course_code: {course_code}")
                subject_title = None
            
            # Check daily word limit
            today = timezone.now().date()
            daily_query, created = DailyQuery.objects.get_or_create(user=request.user, date=today)
            if daily_query.word_count + word_count > 3000:
                return Response(
                    {"error": "Daily word limit exceeded. You can only query up to 3000 words per day."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Prepare data for AI API
            ai_data = {
                "user_id": str(request.user.id),
                "course_code": course_code,
                "user_question": user_question,
                "previous_question_rating": previous_question_rating
            }
            
            # Call AI API
            try:
                response = requests.post(AI_API_URL, data=ai_data, timeout=10)
                response.raise_for_status()
                ai_response = response.json()
                
                # Assume AI API returns {"answer": "response text"}; adjust if different
                response_text = ai_response.get("answer", "No response from AI.")
                input_tokens = ai_response.get("input_tokens", 0)
                output_tokens = ai_response.get("output_tokens", 0)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"AI API request failed: {str(e)}")
                return Response({"error": f"Failed to get response from AI: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Save to ChatHistory
            ChatHistory.objects.create(
                user=request.user,
                course_code=course_code,
                question=user_question,
                answer=response_text
            )
            
            # Update word count
            daily_query.word_count += word_count
            daily_query.save()
            
            # Fetch chat history
            chat_history = ChatHistory.objects.filter(user=request.user, course_code=course_code).order_by("timestamp")
            history = [{"question": entry.question, "answer": entry.answer} for entry in chat_history]
            
            return Response(
                {
                    "subject_title": subject_title,
                    "course_code": course_code,
                    "current_response": {"question": user_question, "answer": response_text},
                    "history": history
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error in ChatView POST: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, course_code):
        """Retrieve chat history for a specific course."""
        try:
            # Verify course exists
            course = CourseProxy.objects.filter(course_code=course_code).first()
            if not course:
                return Response({"error": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Fetch subject title from CourseBasicInfoProxy
            try:
                basic_info = CourseBasicInfoProxy.objects.get(course_code=course_code)
                subject_title = basic_info.title
            except CourseBasicInfoProxy.DoesNotExist:
                logger.warning(f"No CourseBasicInfoProxy for course_code: {course_code}")
                subject_title = None
            
            # Fetch chat history
            chat_history = ChatHistory.objects.filter(user=request.user, course_code=course_code).order_by("timestamp")
            history = [{"question": entry.question, "answer": entry.answer} for entry in chat_history]
            
            return Response(
                {
                    "subject_title": subject_title,
                    "course_code": course_code,
                    "history": history
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error in ChatView GET: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Unchanged: GetUserStatusView ---
class GetUserStatusView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        response_data = {
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "status": user.status,
        }
        return Response(response_data, status=status.HTTP_200_OK)

# --- Unchanged: get_ktu_news ---
def get_ktu_news(request):
    """Retrieve latest 10 news items and randomly trigger update during daytime IST."""
    # Check cache first
    cache_key = 'ktu_news'
    cached_news = cache.get(cache_key)
    if cached_news:
        return JsonResponse(cached_news, safe=False)

    # Check if current time is between 6 AM and 10 PM IST
    current_time = timezone.now()
    current_hour = current_time.hour
    
    if 6 <= current_hour < 22:  # Daytime IST (6 AM to 10 PM)
        # Randomly trigger update with 0.01% probability
        if random.random() < 0.0001:  # Tuned for ~9 updates/week with 10k+ users
            update_news()
    
    # Fetch news from database
    news_items = News.objects.all().order_by('-date')[:10].values('id', 'title', 'date', 'content')
    news_list = list(news_items)
    
    # Cache results for 5 minutes to reduce database load
    cache.set(cache_key, news_list, timeout=300)
    
    return JsonResponse(news_list, safe=False)

# --- Unchanged: AddNewsView ---
class AddNewsView(APIView):
    def post(self, request):
        data = request.data
        data['last_updated'] = timezone.now()
        serializer = NewsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            # Invalidate cache on manual update
            cache.delete('ktu_news')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- Unchanged: BlogListView ---
class BlogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve all published blogs, ordered by created_at descending."""
        blogs = BlogProxy.objects.filter(status="publish").order_by('-created_at')
        serializer = BlogSerializer(blogs, many=True)
        logger.info(f"Retrieved {len(blogs)} blogs")
        return Response(serializer.data, status=status.HTTP_200_OK)

# --- Unchanged: BlogDetailView ---
class BlogDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        """Retrieve details for a specific blog by integer ID."""
        try:
            blog = BlogProxy.objects.get(id=id, status="publish")
            serializer = BlogDetailSerializer(blog)
            logger.info(f"Retrieved blog: {blog.title} (ID: {id})")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BlogProxy.DoesNotExist:
            logger.error(f"Blog not found: ID {id}")
            return Response({"error": "Blog not found or not published."}, status=status.HTTP_404_NOT_FOUND)

# --- Unchanged: NotificationHistoryView ---
class NotificationHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve notification history with read status for the authenticated user."""
        try:
            notifications = NotificationProxy.objects.all().order_by('-created_at')
            serializer = NotificationSerializer(notifications, many=True, context={'request': request})
            logger.info(f"Retrieved {len(notifications)} notifications for user {request.user.phone_number}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in NotificationHistoryView: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Unchanged: ToggleNotificationReadStatusView ---
class ToggleNotificationReadStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Toggle the read status of a notification to True for the authenticated user."""
        notification_id = request.data.get('notification_id')
        if not notification_id:
            return Response({"error": "Notification ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verify notification exists
            notification = NotificationProxy.objects.filter(id=notification_id).first()
            if not notification:
                return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Get or create read status
            read_status, created = NotificationReadStatus.objects.get_or_create(
                user=request.user,
                notification_id=notification_id,
                defaults={'read': True}
            )
            
            if not created and not read_status.read:
                # Update to read if not already read
                read_status.read = True
                read_status.save()
                logger.info(f"Marked notification {notification_id} as read for user {request.user.phone_number}")
                return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)
            elif read_status.read:
                logger.info(f"Notification {notification_id} already read for user {request.user.phone_number}")
                return Response({"message": "Notification is already marked as read."}, status=status.HTTP_200_OK)
            else:
                logger.info(f"Created read status for notification {notification_id} for user {request.user.phone_number}")
                return Response({"message": "Notification marked as read."}, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error in ToggleNotificationReadStatusView: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
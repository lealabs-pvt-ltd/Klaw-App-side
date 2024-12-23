from django.shortcuts import render

# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AppUser, OTP, PreferredSubject,CourseProxy, ChatHistory
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from bson import ObjectId
from .serializers import AppUserSerializer
from twilio.rest import Client
import os
from dotenv import load_dotenv
from django.core.cache import cache
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
import random

load_dotenv()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Function to generate OTP
def generate_otp():
    return str(random.randint(100000, 999999))  # Generates a 6-digit OTP

# Function to send OTP via Twilio SMS
def send_otp_via_twilio(phone_number, otp):
    # Create a Twilio client
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    # Send OTP as SMS
    message = client.messages.create(
        body=f"Your OTP is {otp}",
        from_=TWILIO_PHONE_NUMBER,
        to=phone_number
    )

    return message.sid  # You can return message SID or just confirm message was sent

# Request OTP view for generating OTP
class RequestOTP(APIView):
    permission_classes = []

    def post(self, request):
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

        otp = generate_otp()  # Generate OTP

        # Store OTP in cache for 5 minutes (300 seconds TTL)
        cache.set(phone_number, otp, timeout=300)
        request.session['phone_number'] = phone_number

        # Send OTP to phone number using Twilio
        try:
            send_otp_via_twilio(phone_number, otp)
            return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to send OTP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Verify OTP view for checking OTP
class VerifyOTP(APIView):
    permission_classes = []

    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')

        if not phone_number or not otp:
            return Response({"error": "Phone number and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve OTP from cache
        cached_otp = cache.get(phone_number)

        if cached_otp == otp:
            return Response({"message": "OTP verified."}, status=status.HTTP_200_OK)

        return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
class SignUpPartOne(APIView):
    permission_classes = []
    def post(self, request):
        data = request.data
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        if password != confirm_password:
            return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
        # Temporarily store user data
        request.session['user_data'] = {
            "full_name": data.get('full_name'),
            "email": data.get('email'),
            "password": make_password(password),
        }
        return Response({"message": "Part 1 complete."}, status=status.HTTP_200_OK)

class SignUpPartTwo(APIView):
    permission_classes = []

    def post(self, request):
        phone_number = request.session.get('phone_number')
        print(f"Phone number from session: {phone_number}")  # Log phone number to verify it's correct
        user_data = request.session.get('user_data')
        
        if not user_data or not phone_number:
            return Response({"error": "Missing required data."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the phone number already exists in the database
        if AppUser.objects.filter(phone_number=phone_number).exists():
            return Response({"error": "Phone number already registered."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        # Create a new user with the data from session and request
        user = AppUser.objects.create(
            phone_number=phone_number,  # Using the phone number from session
            **user_data,
            college=data.get('college'),
            department=data.get('department'),
            university=data.get('university'),
            blood_group=data.get('blood_group'),
            subscription_plan=data.get('subscription_plan', 'Plan 1'),
        )
        
        return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
class LoginWithOTP(APIView):
    permission_classes = []
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')

        # Check if the OTP matches the cached OTP
        cached_otp = cache.get(phone_number)
        if cached_otp == otp:
            try:
                user = AppUser.objects.get(phone_number=phone_number)
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh)
                }, status=status.HTTP_200_OK)
            except AppUser.DoesNotExist:
                return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
    
class LoginWithPassword(APIView):
    permission_classes = []
    def post(self, request):
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

        try:
            user = AppUser.objects.get(phone_number=phone_number)
            
            # Check if password is correct
            if check_password(password, user.password):
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh)
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
        except AppUser.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
class ResetPassword(APIView):
    permission_classes = []
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        # Check if new password and confirm password match
        if new_password != confirm_password:
            return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if OTP is valid
        cached_otp = cache.get(phone_number)
        if cached_otp != otp:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the user
            user = AppUser.objects.get(phone_number=phone_number)

            # Set the new password
            user.password = make_password(new_password)
            user.save()

            # Clear the OTP from the cache
            cache.delete(phone_number)

            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)

        except AppUser.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve the profile of the logged-in user."""
        user = request.user
        serializer = AppUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Edit specific fields of the user's profile."""
        user = request.user
        serializer = AppUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateProfilePicView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request):
        """Update the user's profile picture."""
        user = request.user
        profile_pic = request.FILES.get('profile_pic')
        if profile_pic:
            user.profile_pic = profile_pic
            user.save()
            return Response({"message": "Profile picture updated successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "Profile picture file not provided."}, status=status.HTTP_400_BAD_REQUEST)

import logging

# # Set up logger
# # Set up logger
# # Set up logger
# logger = logging.getLogger(__name__)

# # Set up logger
logger = logging.getLogger(__name__)

class PreferredSubjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        preferred_subjects = PreferredSubject.objects.filter(user=user)

        data = []
        for ps in preferred_subjects:
            logger.debug(f"Processing PreferredSubject ID: {ps.id}, Course Code (stored): {ps.course_code}")

            try:
                # Query CourseProxy using the course_code
                course = CourseProxy.objects.get(course_code=ps.course_code)

                # Append only the required fields to the response data
                data.append({
                    "title": course.title,
                    "course_code": course.course_code,
                    "university": course.university,
                })
                logger.debug(f"Course found: {course.title}, {course.course_code}, {course.university}")

            except CourseProxy.DoesNotExist:
                logger.error(f"Course not found for PreferredSubject ID: {ps.id}, User: {user.phone_number}")
            except Exception as e:
                logger.error(f"Error processing PreferredSubject ID: {ps.id} - {str(e)}")

        logger.debug(f"Returning data: {data}")
        return Response(data, status=status.HTTP_200_OK)
    
class AddPreferredSubjectView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user  # The logged-in user
        course_code = request.data.get("course_code")  # Get course_code from the request body
        
        # Ensure that course_code is provided
        if not course_code:
            return Response({"error": "Course code is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Try to find the course based on course_code and check if it's published
            course = CourseProxy.objects.get(course_code=course_code, status="published")
            
            # Add the course to the user's preferred subjects list (if not already added)
            preferred_subject, created = PreferredSubject.objects.get_or_create(user=user, course_code=course_code)
            
            if created:
                return Response({"message": "Subject added to preferred list."}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message": "Subject is already in your preferred list."}, status=status.HTTP_200_OK)
        
        except CourseProxy.DoesNotExist:
            # If the course doesn't exist or is not published
            return Response({"error": "Course not found or not published."}, status=status.HTTP_404_NOT_FOUND)
class SubjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_code):
        try:
            # Query by course_code as a string
            course = CourseProxy.objects.get(course_code=course_code, status="published")
            
            data = {
                "title": course.title,
                "course_code": course.course_code,
                "university": course.university,
                "description": course.description,
            }
            return Response(data, status=status.HTTP_200_OK)

        except CourseProxy.DoesNotExist:
            return Response({"error": "Course not found or not published."}, status=status.HTTP_404_NOT_FOUND)

class AvailableSubjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subjects = CourseProxy.objects.filter(status="published")
        data = [
            {
                "title": subject.title,
                "course_code": subject.course_code,
                "university": subject.university,
            }
            for subject in subjects
        ]
        return Response(data, status=status.HTTP_200_OK)
class SubjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_code):
        try:
            # Query by course_code as a string
            course = CourseProxy.objects.get(course_code=course_code, status="published")
            
            data = {
                "title": course.title,
                "course_code": course.course_code,
                "university": course.university,
                "description": course.description,
            }
            return Response(data, status=status.HTTP_200_OK)

        except CourseProxy.DoesNotExist:
            return Response({"error": "Course not found or not published."}, status=status.HTTP_404_NOT_FOUND)
        
class RemovePreferredSubjectView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, course_code):
        user = request.user
        
        try:
            # Query based on the course_code directly in the PreferredSubject model
            preferred_subject = PreferredSubject.objects.get(user=user, course_code=course_code)
            
            # Delete the found preferred subject
            preferred_subject.delete()
            
            return Response({"message": "Subject removed from preferred list."}, status=status.HTTP_200_OK)
        
        except PreferredSubject.DoesNotExist:
            return Response({"error": "Subject not in preferred list."}, status=status.HTTP_404_NOT_FOUND)

from .Ai.reply import chat  # Import the AI function

class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_code):
        query = request.data.get("query")
        
        if not query:
            return Response(
                {"error": "Query is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Fetch the subject details from CourseProxy (admin panel database)
            course = CourseProxy.objects.filter(course_code=course_code).first()
            if not course:
                return Response(
                    {"error": "Course not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Call the chat function
            response_text, input_tokens, output_tokens = chat(query, course_code)

            # Save the current interaction in the ChatHistory model
            ChatHistory.objects.create(
                user=request.user,
                course_code=course_code,
                question=query,
                answer=response_text
            )

            # Fetch chat history for the course and user
            chat_history = ChatHistory.objects.filter(user=request.user, course_code=course_code).order_by("timestamp")
            history = [{"question": entry.question, "answer": entry.answer} for entry in chat_history]

            # Include course details and chat history in the response
            return Response(
                {
                    "subject_title": course.title,
                    "university": course.university,
                    "course_code": course.course_code,
                    "current_response": {
                        "question": query,
                        "answer": response_text
                    },
                    "history": history
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
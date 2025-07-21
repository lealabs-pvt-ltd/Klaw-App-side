# Klaw App Mobile Side Documentation

This documentation covers the **App Side** of the Klaw app, a Django REST Framework (DRF) project that connects to a MongoDB database using Djongo. The app side provides APIs for user authentication, profile management, course selection, chat interactions, KTU news, blogs, and notifications, all interacting with the shared MongoDB database (`klaw_db_dev`). Below, you’ll find setup instructions, model details, and a detailed breakdown of each API endpoint, including inputs, outputs, and logic.

## 1. Project Overview

The Klaw app’s mobile side is a Django project that provides APIs for:
- **User Authentication**: OTP-based signup/login, password-based login, and password reset.
- **Profile Management**: View and update user profiles, including profile pictures.
- **Course Management**: View available courses, add/remove preferred subjects, and access subject details.
- **Chat Functionality**: Interact with an external AI server for course-related queries with a daily word limit.
- **KTU News**: Fetch and update news from an external KTU API.
- **Blog Access**: View published blogs.
- **Notifications**: View notification history and toggle read status.

The app side shares the `klaw_db_dev` database with the admin side, accessing collections like `admin_panel_course`, `admin_panel_coursebasicinfo`, `admin_panel_blog`, and `admin_panel_notification`.

## 2. Setup Instructions

### Prerequisites
- **Python**: Python 3.10.18
- **MongoDB**: A running MongoDB instance (e.g., local or MongoDB Atlas)
- **Redis**: For Celery (task queue) and caching
- **Dependencies**: Install required packages using `pip install -r requirements.txt`. Key packages include:
anyio==4.9.0
asgiref==3.8.1
async-timeout==5.0.1
blinker==1.9.0
CacheControl==0.14.3
cachetools==5.5.2
certifi==2025.6.15
cffi==1.17.1
charset-normalizer==3.4.2
click==8.2.1
cryptography==45.0.5
Django==3.2.25
django-cors-headers==4.3.1
django-redis==5.4.0
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.1
djongo==1.3.6
exceptiongroup==1.3.0
firebase-admin==6.9.0
Flask==3.1.1
google-api-core==2.25.1
google-api-python-client==2.175.0
google-auth==2.40.3
google-auth-httplib2==0.2.0
google-cloud-core==2.4.3
google-cloud-firestore==2.21.0
google-cloud-storage==3.1.1
google-crc32c==1.7.1
google-resumable-media==2.7.2
googleapis-common-protos==1.70.0
grpcio==1.73.1
grpcio-status==1.73.1
h11==0.16.0
h2==4.2.0
hpack==4.1.0
httpcore==1.0.9
httplib2==0.22.0
httpx==0.28.1
hyperframe==6.1.0
idna==3.10
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.2
msgpack==1.1.1
numpy==1.26.4
pillow==11.3.0
proto-plus==1.26.1
protobuf==6.31.1
pyasn1==0.6.1
pyasn1_modules==0.4.2
pycparser==2.22
PyJWT==2.8.0
pymongo==3.12.3
pyparsing==3.2.3
python-decouple==3.8
python-dotenv==1.1.1
pytz==2025.2
redis==6.2.0
requests==2.32.4
requests-toolbelt==1.0.0
rsa==4.9.1
sniffio==1.3.1
sqlparse==0.2.4
typing_extensions==4.14.0
uritemplate==4.2.0
urllib3==2.5.0
Werkzeug==3.1.3

### Installation
1. **Clone the Project**:
   ```bash
   git clone 
   cd klaw_mobile
   ```

2. **Set Up Environment Variables**:
   Create a `.env` file in the project root:
   ```bash
   SECRET_KEY=your-secret-key
   MSG91_AUTH_KEY=your-msg91-auth-key
   MSG91_TEMPLATE_ID=your-msg91-template-id
   OTP_EXPIRY=5
   AI_API_URL=http://127.0.0.1:5000/api/user_request
   KTU_NEWS_API_URL=https://ktu.api.lealabs.in/api/data
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MongoDB**:
   Update `settings.py` with your MongoDB connection string:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'djongo',
           'NAME': 'klaw_db_dev',
           'CLIENT': {
               'host': 'mongodb://admin:developer2025@13.204.52.164:27017',
               'retryWrites': True,
               'w': 'majority',
           },
       }
   }
   ```

5. **Configure Redis**:
   Ensure Redis is running locally or update `CELERY_BROKER_URL` and `CACHES['default']['LOCATION']` in `settings.py` to match your Redis 
   installation of redis
#### install :
  sudo apt update
  sudo apt install redis-server
  sudo systemctl enable redis
  sudo systemctl start redis
  sudo systemctl status redis-server
  redis-cli ping
   
   instance:
   ```python
   CELERY_BROKER_URL = 'redis://localhost:6379/0'
   CACHES = {
       'default': {
           'BACKEND': 'django_redis.cache.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
           'OPTIONS': {
               'CLIENT_CLASS': 'django_redis.client.DefaultClient',
           }
       }
   }
   ```

6. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Run Redis Server**:
   ```bash
   redis-server
   ```
`

9. **Run the Server**:
   ```bash
   python manage.py runserver
   ```

10. **Access the API**:
    The mobile APIs are available at `http://localhost:8000/api/app/`.

### Directory Structure
- `klaw_mobile/`: Project root
  - `settings.py`: Configuration for Django, DRF, JWT, MongoDB, Celery, Redis, and CORS.
  - `urls.py`: Main URL configuration routing to `mobile_api.urls`.
  - `mobile_api/`: App containing models, serializers, views, and URLs.
    - `models.py`: Defines MongoDB models for users, OTPs, courses, blogs, notifications, etc.
    - `serializers.py`: Serializers for data validation and serialization.
    - `views.py`: API views for handling requests.
    - `urls.py`: URL patterns for mobile APIs.

## 3. Database Configuration
The project uses MongoDB with Djongo as the ORM engine. The database `klaw_db_dev` is hosted at `mongodb://admin:developer2025@13.204.52.164:27017`. Key collections include:
- `mobile_api_appuser`: User data
- `mobile_api_otp`: OTP records
- `mobile_api_dailyquery`: Daily query word counts
- `mobile_api_preferredsubject`: User-preferred courses
- `mobile_api_chathistory`: Chat interactions
- `mobile_api_news`: KTU news
- `mobile_api_notificationreadstatus`: Notification read status
- Shared with admin side:
  - `admin_panel_course`
  - `admin_panel_coursebasicinfo`
  - `admin_panel_blog`
  - `admin_panel_notification`

## 4. Models
The app side defines the following MongoDB models in `models.py`:

1. **OTP**: Stores OTPs for authentication.
   - Fields: `phone_number` (unique), `otp`, `expiry_time` (default: 5 minutes from creation).
   - Method: `is_valid()` checks if OTP is not expired.

2. **AppUser**: Custom user model extending `AbstractUser`.
   - Fields: `first_name`, `last_name`, `full_name`, `phone_number` (unique, `USERNAME_FIELD`), `email`, `year_of_study`, `college`, `referral_code`, `department`, `university`, `blood_group`, `profile_pic`, `subscription_plan` (Basic/Beginner/Advanced), `status` (accepted/rejected).
   - Method: `save()` generates `full_name` and `username` (from `first_name` and `phone_number`).

3. **DailyQuery**: Tracks daily word count for user queries.
   - Fields: `user` (ForeignKey to `AppUser`), `date`, `word_count`.
   - Constraint: Unique together (`user`, `date`).

4. **CourseProxy**: Proxy for `admin_panel_course` collection.
   - Fields: `_id`, `course_code` (unique), `status` (draft/published), `created_at`, `updated_at`.
   - Meta: `managed=False`, `db_table='admin_panel_course'`.

5. **CourseBasicInfoProxy**: Proxy for `admin_panel_coursebasicinfo` collection.
   - Fields: `_id`, `title` (mapped to `course_name`), `course_code` (unique), `year`, `branch`, `semester`, `group`, `created_at`, `updated_at`.
   - Meta: `managed=False`, `db_table='admin_panel_coursebasicinfo'`.

6. **BlogProxy**: Proxy for `admin_panel_blog` collection.
   - Fields: `id` (Integer), `title`, `author`, `category`, `html_code`, `status` (draft/publish), `created_at`.
   - Meta: `managed=False`, `db_table='admin_panel_blog'`.

7. **NotificationProxy**: Proxy for `admin_panel_notification` collection.
   - Fields: `title`, `message`, `created_at`.
   - Meta: `managed=False`, `db_table='admin_panel_notification'`.

8. **NotificationReadStatus**: Tracks notification read status per user.
   - Fields: `user` (ForeignKey to `AppUser`), `notification_id` (Integer), `read` (Boolean), `updated_at`.
   - Constraint: Unique together (`user`, `notification_id`).

9. **PreferredSubject**: Stores user-preferred courses.
   - Fields: `user` (ForeignKey to `AppUser`), `course_code`, `added_on`.

10. **ChatHistory**: Stores user chat interactions.
    - Fields: `user` (ForeignKey to `AppUser`), `course_code`, `question`, `answer`, `timestamp`.

11. **News**: Stores KTU news items.
    - Fields: `title` (unique), `date` (string), `content`, `last_updated`.

## 5. API Endpoints

Below is a detailed breakdown of each API endpoint, including the endpoint URL, HTTP method, inputs, outputs, and logic. Most APIs require JWT authentication (`IsAuthenticated`), except for authentication-related endpoints (`AllowAny`).

### 5.1 Request OTP
- **Endpoint**: `POST /api/app/request-otp/`
- **Permission**: `AllowAny`
- **Description**: Sends an OTP to the provided phone number via MSG91.
- **Input**:
  ```json
  {"phone_number": "string"}
  ```
- **Output**:
  - **Success (200)**:
    ```json
    {"message": "OTP sent successfully."}
    ```
  - **Error (400)**:
    ```json
    {"error": "Phone number is required."}
    ```
  - **Error (500)**:
    ```json
    {"error": "Failed to send OTP: <error_message>"}
    ```
- **Logic**:
  1. Validate `phone_number`.
  2. Generate a 6-digit OTP and store in cache (5-minute timeout).
  3. Save `phone_number` in session.
  4. Send OTP via `send_otp_via_msg91`.
  5. Return success or error based on MSG91 response.

### 5.2 Verify OTP
- **Endpoint**: `POST /api/app/verify-otp/`
- **Permission**: `AllowAny`
- **Description**: Verifies the OTP for a phone number.
- **Input**:
  ```json
  {
    "phone_number": "string",
    "otp": "string"
  }
  ```
- **Output**:
  - **Success (200)**:
    ```json
    {"message": "OTP verified."}
    ```
  - **Error (400)**:
    ```json
    {"error": "Phone number is required."}
    ```
  - **Error (400)**:
    ```json
    {"error": "Invalid OTP."}
    ```
  - **Error (500)**:
    ```json
    {"error": "Failed to verify OTP: <error_message>"}
    ```
- **Logic**:
  1. Validate `phone_number` and `otp`.
  2. Check cached OTP.
  3. Verify OTP via `verify_otp_via_msg91`.
  4. Return success or error based on verification.

### 5.3 Resend OTP
- **Endpoint**: `POST /api/app/resend-otp/`
- **Permission**: `AllowAny`
- **Description**: Resends an OTP to the provided phone number.
- **Input**:
  ```json
  {
    "phone_number": "string",
    "retry_type": "text" // Optional, defaults to "text"
  }
  ```
- **Output**:
  - **Success (200)**:
    ```json
    {"message": "OTP resent successfully."}
    ```
  - **Error (400)**:
    ```json
    {"error": "Phone number is required."}
    ```
  - **Error (500)**:
    ```json
    {"error": "Failed to resend OTP: <error_message>"}
    ```
- **Logic**:
  1. Validate `phone_number`.
  2. Resend OTP via `resend_otp_via_msg91` with specified `retry_type`.
  3. Return success or error based on MSG91 response.

### 5.4 Sign Up Part 1
- **Endpoint**: `POST /api/app/signup/part1/`
- **Permission**: `AllowAny`
- **Description**: Stores initial user data in session for two-step signup.
- **Input**:
  ```json
  {
    "first_name": "string",
    "last_name": "string",
    "email": "string",
    "password": "string",
    "phone_number": "string"
  }
  ```
- **Output**:
  - **Success (200)**:
    ```json
    {"message": "Part 1 complete."}
    ```
- **Logic**:
  1. Hash `password` using `make_password`.
  2. Store `first_name`, `last_name`, `email`, hashed `password`, and `phone_number` in session.
  3. Return success message.

### 5.5 Sign Up Part 2
- **Endpoint**: `POST /api/app/signup/part2/`
- **Permission**: `AllowAny`
- **Description**: Completes user registration using provided data.
- **Input**:
  ```json
  {
    "first_name": "string",
    "last_name": "string",
    "email": "string",
    "password": "string",
    "phone_number": "string",
    "year_of_study": "1st year|2nd year|3rd year|4th year",
    "subscription_plan": "Basic|Beginner|Advanced", // Optional
    "college": "string", // Optional
    "department": "string", // Optional
    "university": "string", // Optional
    "blood_group": "string", // Optional
    "referral_code": "string" // Optional
  }
  ```
- **Output**:
  - **Success (201)**:
    ```json
    {"message": "User created successfully."}
    ```
  - **Error (400)**:
    ```json
    {"error": "All required fields must be provided."}
    ```
  - **Error (400)**:
    ```json
    {"error": "Phone number already registered."}
    ```
- **Logic**:
  1. Validate required fields (`first_name`, `last_name`, `email`, `password`, `phone_number`, `year_of_study`).
  2. Check if `phone_number` is unique.
  3. Create `AppUser` with provided data, hashing `password`.
  4. Save and return success.

### 5.6 Login with OTP
- **Endpoint**: `POST /api/app/login-otp/`
- **Permission**: `AllowAny`
- **Description**: Authenticates a user using phone number and OTP, returning JWT tokens.
- **Input**:
  ```json
  {
    "phone_number": "string",
    "otp": "string"
  }
  ```
- **Output**:
  - **Success (200)**:
    ```json
    {
      "access_token": "jwt-access-token",
      "refresh_token": "jwt-refresh-token"
    }
    ```
  - **Error (400)**:
    ```json
    {"error": "Phone number is required."}
    ```
  - **Error (400)**:
    ```json
    {"error": "Invalid OTP."}
    ```
  - **Error (404)**:
    ```json
    {"error": "User does not exist."}
    ```
  - **Error (500)**:
    ```json
    {"error": "Failed to verify OTP: <error_message>"}
    ```
- **Logic**:
  1. Validate `phone_number` and `otp`.
  2. Check cached OTP and verify via `verify_otp_via_msg91`.
  3. Fetch user by `phone_number`.
  4. Generate JWT tokens using `RefreshToken.for_user`.
  5. Return tokens or error.

### 5.7 Login with Password
- **Endpoint**: `POST /api/app/login-password/`
- **Permission**: `AllowAny`
- **Description**: Authenticates a user using phone number and password, returning JWT tokens.
- **Input**:
  ```json
  {
    "phone_number": "string",
    "password": "string"
  }
  ```
- **Output**:
  - **Success (200)**:
    ```json
    {
      "access_token": "jwt-access-token",
      "refresh_token": "jwt-refresh-token"
    }
    ```
  - **Error (400)**:
    ```json
    {"error": "Invalid credentials."}
    ```
  - **Error (404)**:
    ```json
    {"error": "User does not exist."}
    ```
- **Logic**:
  1. Validate `phone_number` and `password`.
  2. Fetch user by `phone_number`.
  3. Verify password using `check_password`.
  4. Generate JWT tokens using `RefreshToken.for_user`.
  5. Return tokens or error.

### 5.8 Reset Password
- **Endpoint**: `POST /api/app/reset-password/`
- **Permission**: `AllowAny`
- **Description**: Resets a user’s password after verifying phone number.
- **Input**:
  ```json
  {
    "phone_number": "string",
    "new_password": "string",
    "confirm_password": "string"
  }
  ```
- **Output**:
  - **Success (200)**:
    ```json
    {"message": "Password reset successfully."}
    ```
  - **Error (400)**:
    ```json
    {"error": "Phone number is required."}
    ```
  - **Error (400)**:
    ```json
    {"error": "Passwords do not match."}
    ```
  - **Error (404)**:
    ```json
    {"error": "User does not exist."}
    ```
- **Logic**:
  1. Validate `phone_number`, `new_password`, and `confirm_password`.
  2. Check if passwords match.
  3. Fetch user by `phone_number`.
  4. Update password using `make_password` and save.

### 5.9 User Profile
- **Endpoint**: `GET /api/app/user-profile/`
- **Permission**: `IsAuthenticated`
- **Description**: Retrieves the authenticated user’s profile data.
- **Input**: None.
- **Output**:
  - **Success (200)**:
    ```json
    {
      "full_name": "string",
      "phone_number": "string",
      "college": "string",
      "email": "string",
      "referral_code": "string",
      "department": "string",
      "university": "string",
      "blood_group": "string",
      "profile_pic": "url or null",
      "subscription_plan": "Basic|Beginner|Advanced",
      "year_of_study": "1st year|2nd year|3rd year|4th year"
    }
    ```
  - **Error (401)**:
    ```json
    {"error": "User is not authenticated."}
    ```
- **Logic**:
  1. Verify user authentication.
  2. Serialize user data with `AppUserSerializer`.
  3. Convert `profile_pic` to absolute URL if present.

### 5.10 Update Profile Picture
- **Endpoint**: `PATCH /api/app/update-profile-pic/`
- **Permission**: `IsAuthenticated`
- **Description**: Updates the user’s profile picture.
- **Input**: 
  - Content-Type: `multipart/form-data`
  ```json
  {"profile_pic": file}
  ```
- **Output**:
  - **Success (200)**:
    ```json
    {"message": "Profile picture updated successfully."}
    ```
  - **Error (400)**:
    ```json
    {"error": "Profile picture file not provided."}
    ```
- **Logic**:
  1. Validate `profile_pic` file presence.
  2. Update user’s `profile_pic` field and save.

### 5.11 Update Profile and Password
- **Endpoint**: `PUT /api/app/editprofile/`
- **Permission**: `IsAuthenticated`
- **Description**: Updates user profile and optionally changes password.
- **Input**:
  ```json
  {
    "full_name": "string", // Optional
    "phone_number": "string", // Optional
    "email": "string", // Optional
    "department": "string", // Optional
    "blood_group": "string", // Optional
    "year_of_study": "1st year|2nd year|3rd year|4th year", // Optional
    "old_password": "string", // Optional
    "new_password": "string", // Optional
    "confirm_password": "string" // Optional
  }
  ```
- **Output**:
  - **Success (200)**:
    ```json
    {"message": "Profile and password updated successfully."}
    ```
  - **Error (400)**:
    ```json
    {"error": "Old password is incorrect."}
    ```
  - **Error (400)**:
    ```json
    {"error": "New password and confirm password do not match."}
    ```
  - **Error (500)**:
    ```json
    {"error": "<error_message>"}
    ```
- **Logic**:
  1. Update profile fields if provided and non-empty.
  2. Split `full_name` into `first_name` and `last_name`.
  3. If password fields are provided, verify `old_password`, check if `new_password` matches `confirm_password`, and update password.
  4. Save user and return success.

### 5.12 Preferred Subjects
- **Endpoint**: `GET /api/app/preferred-subjects/`
- **Permission**: `IsAuthenticated`
- **Description**: Retrieves the user’s preferred subjects with titles.
- **Input**: None.
- **Output**:
  - **Success (200)**:
    ```json
    [
      {
        "title": "string or null",
        "course_code": "string"
      }
    ]
    ```
- **Logic**:
  1. Fetch user’s `PreferredSubject` entries.
  2. For each, get `CourseProxy` (status=published) and `CourseBasicInfoProxy` for title.
  3. Log errors if course or basic info is missing.
  4. Return list of subjects with titles and course codes.

### 5.13 Add Preferred Subject
- **Endpoint**: `POST /api/app/add-preferred-subject/`
- **Permission**: `IsAuthenticated`
- **Description**: Adds or removes a subject from the user’s preferred list.
- **Input**:
  ```json
  {
    "course_code": "string",
    "preferred": true or false
  }
  ```
- **Output**:
  - **Success (201, add)**:
    ```json
    {"message": "Subject added to preferred list."}
    ```
  - **Success (200, remove or already added)**:
    ```json
    {"message": "Subject removed from preferred list."}
    ```
  - **Error (400)**:
    ```json
    {"error": "Course code is required."}
    ```
  - **Error (404)**:
    ```json
    {"error": "Course not found or not published."}
    ```
  - **Error (500)**:
    ```json
    {"error": "<error_message>"}
    ```
- **Logic**:
  1. Validate `course_code` and `preferred`.
  2. Verify course exists and is published.
  3. If `preferred=true`, create `PreferredSubject` if not exists.
  4. If `preferred=false`, delete `PreferredSubject` if exists.
  5. Return appropriate message.

### 5.14 Available Subjects
- **Endpoint**: `GET /api/app/available-subjects/`
- **Permission**: `IsAuthenticated`
- **Description**: Retrieves all published subjects with details.
- **Input**: None.
- **Output**:
  - **Success (200)**:
    ```json
    [
      {
        "_id": "string",
        "title": "string",
        "course_code": "string",
        "year": integer,
        "branch": "string",
        "semester": integer,
        "group": "string",
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    ]
    ```
  - **Error (500)**:
    ```json
    {"error": "<error_message>"}
    ```
- **Logic**:
  1. Fetch published courses from `CourseProxy`.
  2. Get corresponding `CourseBasicInfoProxy` entries.
  3. Serialize with `CourseSerializer` and return.

### 5.15 Subject Detail
- **Endpoint**: `GET /api/app/subject-detail/<course_code>/`
- **Permission**: `IsAuthenticated`
- **Description**: Retrieves details for a specific published course.
- **Input**: None (uses `course_code` from URL).
- **Output**:
  - **Success (200)**:
    ```json
    {
      "_id": "string",
      "title": "string",
      "course_code": "string",
      "year": integer,
      "branch": "string",
      "semester": integer,
      "group": "string",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
    ```
  - **Error (404)**:
    ```json
    {"error": "Course not found or not published."}
    ```
- **Logic**:
  1. Fetch published course by `course_code` from `CourseProxy`.
  2. Serialize with `CourseSerializer`.

### 5.16 Chat
- **Endpoint**: `POST /api/app/chat/<course_code>/`
- **Permission**: `IsAuthenticated`
- **Description**: Sends a query to an external AI API and stores the response in chat history.
- **Input**:
  ```json
  {
    "query": "string",
    "previous_question_rating": "string" // Optional, defaults to "nil"
  }
  ```
- **Output**:
  - **Success (200)**:
    ```json
    {
      "subject_title": "string or null",
      "course_code": "string",
      "current_response": {
        "question": "string",
        "answer": "string"
      },
      "history": [
        {
          "question": "string",
          "answer": "string"
        }
      ]
    }
    ```
  - **Error (400)**:
    ```json
    {"error": "Query is required."}
    ```
  - **Error (403)**:
    ```json
    {"error": "Daily word limit exceeded. You can only query up to 3000 words per day."}
    ```
  - **Error (404)**:
    ```json
    {"error": "Course not found."}
    ```
  - **Error (500)**:
    ```json
    {"error": "Failed to get response from AI: <error_message>"}
    ```
- **Logic**:
  1. Validate `query` and `course_code`.
  2. Verify course exists in `CourseProxy`.
  3. Get `subject_title` from `CourseBasicInfoProxy`.
  4. Check daily word limit (3000 words) using `DailyQuery`.
  5. Send query to AI API (`AI_API_URL`) with `user_id`, `course_code`, `user_question`, and `previous_question_rating`.
  6. Save response to `ChatHistory`.
  7. Update `DailyQuery` word count.
  8. Return subject title, course code, current response, and chat history.

- **Endpoint**: `GET /api/app/chat/<course_code>/`
- **Permission**: `IsAuthenticated`
- **Description**: Retrieves chat history for a specific course.
- **Input**: None (uses `course_code` from URL).
- **Output**:
  - **Success (200)**:
    ```json
    {
      "subject_title": "string or null",
      "course_code": "string",
      "history": [
        {
          "question": "string",
          "answer": "string"
        }
      ]
    }
    ```
  - **Error (404)**:
    ```json
    {"error": "Course not found."}
    ```
  - **Error (500)**:
    ```json
    {"error": "<error_message>"}
    ```
- **Logic**:
  1. Verify course exists in `CourseProxy`.
  2. Get `subject_title` from `CourseBasicInfoProxy`.
  3. Fetch `ChatHistory` for user and course, ordered by `timestamp`.
  4. Return subject title, course code, and history.

### 5.17 Get User Status
- **Endpoint**: `GET /api/app/user/status/`
- **Permission**: `IsAuthenticated`
- **Description**: Retrieves the user’s status and basic info.
- **Input**: None.
- **Output**:
  - **Success (200)**:
    ```json
    {
      "full_name": "string",
      "phone_number": "string",
      "status": "accepted|rejected"
    }
    ```
- **Logic**:
  1. Return user’s `full_name`, `phone_number`, and `status`.

### 5.18 KTU News
- **Endpoint**: `GET /api/app/ktu-news/`
- **Permission**: None (public)
- **Description**: Retrieves up to 10 latest KTU news items, with random updates during daytime IST.
- **Input**: None.
- **Output**:
  - **Success (200)**:
    ```json
    [
      {
        "id": integer,
        "title": "string",
        "date": "string",
        "content": "string"
      }
    ]
    ```
- **Logic**:
  1. Check cache (`ktu_news`, 5-minute timeout).
  2. If cache miss, check time (6 AM–10 PM IST) and randomly trigger `update_news` (0.01% chance).
  3. Fetch up to 10 news items from `News`, ordered by `date` (descending).
  4. Cache and return results.

### 5.19 Add KTU News
- **Endpoint**: `POST /api/app/add-ktu-news/`
- **Permission**: None (consider adding `IsAuthenticated` or admin check)
- **Description**: Manually adds a news item and invalidates cache.
- **Input**:
  ```json
  {
    "title": "string",
    "date": "string",
    "content": "string"
  }
  ```
- **Output**:
  - **Success (201)**:
    ```json
    {
      "id": integer,
      "title": "string",
      "date": "string",
      "content": "string",
      "last_updated": "datetime"
    }
    ```
  - **Error (400)**:
    ```json
    {"title": ["This field is required."]}
    ```
- **Logic**:
  1. Validate input with `NewsSerializer`.
  2. Set `last_updated` to current time.
  3. Save news item and invalidate `ktu_news` cache.

### 5.20 Blog List
- **Endpoint**: `GET /api/app/blogs/`
- **Permission**: `IsAuthenticated`
- **Description**: Retrieves all published blogs, ordered by creation date (descending).
- **Input**: None.
- **Output**:
  - **Success (200)**:
    ```json
    [
      {
        "id": integer,
        "title": "string",
        "author": "string",
        "category": "string",
        "status": "publish",
        "created_at": "datetime",
        "html_code": "string"
      }
    ]
    ```
- **Logic**:
  1. Fetch published blogs from `BlogProxy`, ordered by `created_at` (descending).
  2. Serialize with `BlogSerializer`.

### 5.21 Blog Detail
- **Endpoint**: `GET /api/app/blog/<id>/`
- **Permission**: `IsAuthenticated`
- **Description**: Retrieves details for a specific published blog by ID.
- **Input**: None (uses `id` from URL).
- **Output**:
  - **Success (200)**:
    ```json
    {
      "id": integer,
      "title": "string",
      "author": "string",
      "category": "string",
      "html_code": "string",
      "status": "publish",
      "created_at": "datetime"
    }
    ```
  - **Error (404)**:
    ```json
    {"error": "Blog not found or not published."}
    ```
- **Logic**:
  1. Fetch published blog by `id` from `BlogProxy`.
  2. Serialize with `BlogDetailSerializer`.

### 5.22 Notification History
- **Endpoint**: `GET /api/app/notifications/`
- **Permission**: `IsAuthenticated`
- **Description**: Retrieves notification history with read status for the user.
- **Input**: None.
- **Output**:
  - **Success (200)**:
    ```json
    [
      {
        "id": integer,
        "title": "string",
        "message": "string",
        "created_at": "datetime",
        "read": boolean
      }
    ]
    ```
  - **Error (500)**:
    ```json
    {"error": "<error_message>"}
    ```
- **Logic**:
  1. Fetch all notifications from `NotificationProxy`, ordered by `created_at` (descending).
  2. Serialize with `NotificationSerializer`, including `read` status from `NotificationReadStatus`.

### 5.23 Toggle Notification Read Status
- **Endpoint**: `POST /api/app/toggle-notification-read/`
- **Permission**: `IsAuthenticated`
- **Description**: Marks a notification as read for the user.
- **Input**:
  ```json
  {"notification_id": integer}
  ```
- **Output**:
  - **Success (201, new read status)**:
    ```json
    {"message": "Notification marked as read."}
    ```
  - **Success (200, already read)**:
    ```json
    {"message": "Notification is already marked as read."}
    ```
  - **Error (400)**:
    ```json
    {"error": "Notification ID is required."}
    ```
  - **Error (404)**:
    ```json
    {"error": "Notification not found."}
    ```
  - **Error (500)**:
    ```json
    {"error": "<error_message>"}
    ```
- **Logic**:
  1. Validate `notification_id`.
  2. Verify notification exists in `NotificationProxy`.
  3. Create or update `NotificationReadStatus` to `read=True`.

## 6. Security and Authentication
- **JWT Authentication**: Uses `rest_framework_simplejwt` with:
  - Access token lifetime: 365 days.
  - Refresh token lifetime: 730 days.
  - Tokens rotate with `ROTATE_REFRESH_TOKENS=True` and blacklist old tokens.
  - Tokens are generated via `/login-otp/` or `/login-password/`.
- **CORS**: `CORS_ALLOW_ALL_ORIGINS=True` for development. Specify allowed origins in production.
- **Permissions**:
  - Most endpoints require `IsAuthenticated`.
  - Authentication endpoints (`request-otp`, `verify-otp`, `resend-otp`, `signup/part1`, `signup/part2`, `login-otp`, `login-password`, `reset-password`) use `AllowAny`.
  - `ktu-news` and `add-ktu-news` lack explicit permissions (consider adding `IsAuthenticated` or admin checks).

## 7. File Storage
- **Media Files**: Profile pictures are stored in `media/profile_pics/`.
  - `MEDIA_URL = '/media/'`
  - `MEDIA_ROOT = BASE_DIR / 'media'`

## 8. Caching and Task Queue
- **Redis Caching**: Used for KTU news (`ktu_news` key, 5-minute timeout) and OTP storage (5-minute timeout).
- **Celery**: Configured with Redis broker (`redis://localhost:6379/0`) for asynchronous tasks (e.g., news updates).

## 9. External Dependencies
- **MSG91**: Used for OTP sending/verification (`MSG91_AUTH_KEY`, `MSG91_TEMPLATE_ID`).
- **AI API**: Chat queries are sent to `AI_API_URL` (default: `http://127.0.0.1:5000/api/user_request`).
- **KTU News API**: News is fetched from `KTU_NEWS_API_URL` (default: `https://ktu.api.lealabs.in/api/data`).

## 10. Logging
- Logging is implemented using `logging.getLogger(__name__)` to track:
  - API successes (e.g., OTP sent, user created).
  - Errors (e.g., course not found, AI API failures).
  - Debug info for course and notification processing.

## 11. Notes for Developers
- **MongoDB Integration**: Djongo maps Django models to MongoDB collections. Proxy models (`CourseProxy`, `BlogProxy`, `NotificationProxy`) access admin-side collections.
- **Daily Word Limit**: Chat queries are limited to 3000 words per day per user, tracked in `DailyQuery`.
- **News Updates**: KTU news updates randomly during 6 AM–10 PM IST (0.01% chance) or every 12 hours. Cache invalidates on manual updates.
- **Security Improvements**:
  - Set `CORS_ALLOW_ALL_ORIGINS=False` and specify origins in production.
  - Add permissions to `ktu-news` and `add-ktu-news`.
  - Set `DEBUG=False` in production and secure `SECRET_KEY`.
  - Consider shorter JWT access token lifetime (e.g., 60 minutes).
- **Testing**: Use Postman or curl with `Authorization: Bearer <access_token>` for authenticated endpoints.

## 12. Example API Usage
### Request OTP
```bash
curl -X POST http://localhost:8000/api/app/request-otp/ \
-H "Content-Type: application/json" \
-d '{"phone_number": "+919876543210"}'
```

### Login with OTP
```bash
curl -X POST http://localhost:8000/api/app/login-otp/ \
-H "Content-Type: application/json" \
-d '{"phone_number": "+919876543210", "otp": "123456"}'
```

### Add Preferred Subject
```bash
curl -X POST http://localhost:8000/api/app/add-preferred-subject/ \
-H "Authorization: Bearer <access_token>" \
-H "Content-Type: application/json" \
-d '{"course_code": "CS101", "preferred": true}'
```

### Chat Query
```bash
curl -X POST http://localhost:8000/api/app/chat/CS101/ \
-H "Authorization: Bearer <access_token>" \
-H "Content-Type: application/json" \
-d '{"query": "Explain Python functions", "previous_question_rating": "good"}'
```

### Get KTU News
```bash
curl -X GET http://localhost:8000/api/app/ktu-news/
```
# EzyDoo API

EzyDoo is a hyperlocal platform connecting people who need help with simple tasks to local helpers.

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository
```
git clone <repository-url>
cd ezydoo
```

2. Create and activate a virtual environment (optional but recommended)
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Run migrations
```
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser
```
python manage.py createsuperuser
```

6. Run the development server
```
python manage.py runserver
```

## API Documentation

The API documentation is available at:
- Swagger UI: `/swagger/`
- ReDoc: `/redoc/`

## API Endpoints

### Authentication
- `POST /api/auth/token/` - Obtain JWT token
- `POST /api/auth/token/refresh/` - Refresh JWT token

### Users
- `GET /api/users/` - List users (limited for non-admin users)
- `POST /api/users/` - Register a new user
- `GET /api/users/{id}/` - Get user details
- `PUT /api/users/{id}/` - Update user details
- `GET /api/users/{id}/ratings/` - Get user ratings
- `POST /api/users/request_otp/` - Request OTP verification
- `POST /api/users/verify_otp/` - Verify OTP

### Helper Documents
- `GET /api/documents/` - List helper documents (only own documents)
- `PUT /api/documents/{id}/` - Update helper documents
- `GET /api/documents/{id}/status/` - Check document verification status

### Jobs
- `GET /api/jobs/` - List jobs
- `POST /api/jobs/` - Create a new job
- `GET /api/jobs/{id}/` - Get job details
- `PUT /api/jobs/{id}/` - Update job details
- `POST /api/jobs/{id}/assign/` - Assign a helper to a job
- `POST /api/jobs/{id}/complete/` - Mark a job as complete

### Job Applications
- `GET /api/applications/` - List job applications
- `POST /api/applications/` - Apply for a job
- `GET /api/applications/{id}/` - Get application details

### Reviews
- `GET /api/reviews/` - List reviews
- `POST /api/reviews/` - Create a review
- `GET /api/reviews/{id}/` - Get review details

### Wallet
- `GET /api/wallets/` - View wallet details

### Transactions
- `GET /api/transactions/` - List transactions

### Notifications
- `GET /api/notifications/` - List notifications
- `PATCH /api/notifications/{id}/` - Mark notification as read
- `POST /api/notifications/mark_all_read/` - Mark all notifications as read

## Verification Process

### Job Posters
1. Register with a phone number
2. Request OTP verification using the `/api/users/request_otp/` endpoint
3. Verify OTP using the `/api/users/verify_otp/` endpoint
4. Job posters are verified immediately after OTP verification

### Helpers
1. Register with a phone number
2. Request OTP verification using the `/api/users/request_otp/` endpoint
3. Verify OTP using the `/api/users/verify_otp/` endpoint
4. Upload required documents (Aadhaar Card, Driving License, PAN Card, and Selfie) using the `/api/documents/` endpoint
5. Admin reviews and approves documents
6. Helper is marked as verified after document approval

Note: Helper must be verified to apply for jobs, and only verified helpers can be assigned to jobs. 
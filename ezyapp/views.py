from django.shortcuts import render
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from .models import Job, JobApplication, Review, Wallet, Transaction, Notification, HelperDocument
from .serializers import (
    UserSerializer, UserUpdateSerializer, UserProfileSerializer,
    JobSerializer, JobDetailSerializer,
    JobApplicationSerializer, JobApplicationDetailSerializer,
    ReviewSerializer, ReviewDetailSerializer,
    WalletSerializer, TransactionSerializer,
    NotificationSerializer, HelperDocumentSerializer
)

User = get_user_model()

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.user == request.user

@extend_schema(tags=['users'])
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users.
    
    Provides CRUD operations for user profiles and additional actions for OTP verification.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action in ['retrieve', 'list']:
            return UserProfileSerializer
        return UserSerializer
    
    def get_queryset(self):
        if self.action == 'list' and not self.request.user.is_staff:
            # Regular users can only see their own profile when listing
            return User.objects.filter(id=self.request.user.id)
        return super().get_queryset()
    
    @extend_schema(
        summary="Get user ratings",
        description="Retrieve the average rating and total number of reviews for a user",
        responses={200: {"type": "object", "properties": {
            "avg_rating": {"type": "number"},
            "review_count": {"type": "integer"}
        }}}
    )
    @action(detail=True, methods=['get'])
    def ratings(self, request, pk=None):
        """Get the average rating and review count for a user."""
        user = self.get_object()
        avg_rating = Review.objects.filter(reviewed=user).aggregate(Avg('rating'))
        review_count = Review.objects.filter(reviewed=user).count()
        
        return Response({
            'avg_rating': avg_rating['rating__avg'] or 0,
            'review_count': review_count
        })
    
    @extend_schema(
        summary="Request OTP",
        description="Request a new OTP for phone number verification",
        request={
            "application/json": {
                "type": "object",
                "required": ["phone_number"],
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "User's phone number",
                        "example": "+1234567890"
                    }
                }
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "otp": {"type": "string"}
                }
            },
            400: {
                "type": "object",
                "properties": {
                    "error": {"type": "string"}
                }
            },
            404: {
                "type": "object",
                "properties": {
                    "error": {"type": "string"}
                }
            }
        }
    )
    @action(detail=False, methods=['post'])
    def request_otp(self, request):
        """Request a new OTP for verification."""
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(phone_number=phone_number)
            otp = user.generate_otp()
            
            # In a real application, you would send the OTP via SMS
            # For this example, we'll just return it in the response (NOT SECURE for production)
            return Response({'message': f'OTP sent to {phone_number}', 'otp': otp})
            
        except User.DoesNotExist:
            return Response({'error': 'User with this phone number not found'}, 
                           status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        summary="Verify OTP",
        description="Verify OTP and mark user as verified if applicable",
        request={
            "application/json": {
                "type": "object",
                "required": ["phone_number", "otp"],
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "User's phone number",
                        "example": "+1234567890"
                    },
                    "otp": {
                        "type": "string",
                        "description": "One-time password received",
                        "example": "123456"
                    }
                }
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "string"}
                }
            },
            400: {
                "type": "object",
                "properties": {
                    "error": {"type": "string"}
                }
            }
        }
    )
    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        """Verify OTP and mark user as verified."""
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        
        if not phone_number or not otp:
            return Response({'error': 'Phone number and OTP are required'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(phone_number=phone_number, otp=otp)
            
            # Check if OTP is expired
            expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
            expiry_time = user.otp_created_at + timedelta(minutes=expiry_minutes)
            
            if timezone.now() > expiry_time:
                return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark user as verified if they're a job poster
            # Helpers need document verification
            if user.user_type == 'poster':
                user.is_verified = True
            
            # Clear OTP
            user.otp = None
            user.otp_created_at = None
            user.save()
            
            return Response({'success': 'OTP verified successfully'})
            
        except User.DoesNotExist:
            return Response({'error': 'Invalid phone number or OTP'}, 
                           status=status.HTTP_400_BAD_REQUEST)

@extend_schema(tags=['documents'])
class HelperDocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing helper documents.
    
    Allows helpers to upload and manage their verification documents.
    """
    serializer_class = HelperDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = HelperDocument.objects.none()  # Initialize with empty queryset

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return HelperDocument.objects.none()
        return HelperDocument.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        # Set document status to pending when documents are updated
        instance = serializer.instance
        
        # Only change status if it was already approved and user is updating documents
        if instance.status == 'approved' and any(
            field in self.request.data for field in 
            ['aadhaar_card', 'driving_license', 'pan_card', 'selfie']
        ):
            serializer.save(status='pending')
        else:
            serializer.save()
    
    @extend_schema(
        summary="Get document status",
        description="Retrieve the current status and details of verification documents",
        responses={200: {"type": "object", "properties": {
            "status": {"type": "string"},
            "has_aadhaar": {"type": "boolean"},
            "has_driving_license": {"type": "boolean"},
            "has_pan_card": {"type": "boolean"},
            "has_selfie": {"type": "boolean"},
            "rejection_reason": {"type": "string"},
            "verified_at": {"type": "string", "format": "date-time"}
        }}}
    )
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get the current status of verification documents."""
        document = self.get_object()
        return Response({
            'status': document.status,
            'has_aadhaar': bool(document.aadhaar_card),
            'has_driving_license': bool(document.driving_license),
            'has_pan_card': bool(document.pan_card),
            'has_selfie': bool(document.selfie),
            'rejection_reason': document.rejection_reason,
            'verified_at': document.verified_at,
        })

@extend_schema(tags=['jobs'])
class JobViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing jobs.
    
    Provides CRUD operations for job postings and additional actions for job management.
    """
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'job_type']
    search_fields = ['title', 'description', 'location_address']
    ordering_fields = ['created_at', 'start_time', 'price', 'hourly_rate']
    
    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return JobDetailSerializer
        return JobSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Job posters can only see their own jobs or jobs they're assigned to
        if user.user_type == 'poster':
            return Job.objects.filter(user=user)
        
        # Helpers can see all open jobs or jobs they're assigned to
        return Job.objects.filter(
            Q(status='open') | Q(assigned_to=user)
        )
    
    @extend_schema(
        summary="Assign job to helper",
        description="Assign a job to a helper based on their application",
        request={
            "application/json": {
                "type": "object",
                "required": ["application_id"],
                "properties": {
                    "application_id": {
                        "type": "integer",
                        "description": "ID of the job application to assign",
                        "example": 1
                    }
                }
            }
        },
        responses={
            200: JobDetailSerializer,
            400: {
                "type": "object",
                "properties": {
                    "error": {"type": "string"}
                }
            },
            403: {
                "type": "object",
                "properties": {
                    "error": {"type": "string"}
                }
            },
            404: {
                "type": "object",
                "properties": {
                    "error": {"type": "string"}
                }
            }
        }
    )
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign a job to a helper based on their application."""
        job = self.get_object()
        application_id = request.data.get('application_id')
        
        if not application_id:
            return Response({'error': 'Application ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            application = JobApplication.objects.get(id=application_id, job=job)
            
            # Only job owner can assign
            if job.user != request.user:
                return Response({'error': 'Only job owner can assign jobs'}, status=status.HTTP_403_FORBIDDEN)
            
            # Job must be open
            if job.status != 'open':
                return Response({'error': 'Only open jobs can be assigned'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Helper must be verified
            if not application.helper.is_verified:
                return Response({'error': 'Helper must be verified before being assigned'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            # Update job status and assigned_to
            job.status = 'assigned'
            job.assigned_to = application.helper
            job.save()
            
            # Update application status
            application.status = 'accepted'
            application.save()
            
            # Reject other applications
            JobApplication.objects.filter(job=job).exclude(id=application_id).update(status='rejected')
            
            # Create notification for helper
            Notification.objects.create(
                user=application.helper,
                message=f"You've been assigned to the job '{job.title}'!"
            )
            
            return Response({'success': 'Job assigned successfully'})
            
        except JobApplication.DoesNotExist:
            return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        job = self.get_object()
        
        # Only job owner or assigned helper can mark as complete
        if job.user != request.user and job.assigned_to != request.user:
            return Response({'error': 'Only job owner or assigned helper can mark job as complete'}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        # Job must be assigned
        if job.status != 'assigned':
            return Response({'error': 'Only assigned jobs can be marked as complete'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Update job status
        job.status = 'completed'
        job.save()
        
        # Create notification for the other party
        if request.user == job.user:
            recipient = job.assigned_to
            message = f"Job '{job.title}' has been marked as complete by the job poster"
        else:
            recipient = job.user
            message = f"Job '{job.title}' has been marked as complete by the helper"
        
        Notification.objects.create(
            user=recipient,
            message=message
        )
        
        return Response({'success': 'Job marked as complete'})

@extend_schema(tags=['applications'])
class JobApplicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing job applications.
    
    Allows helpers to apply for jobs and job posters to manage applications.
    """
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'job']
    ordering_fields = ['created_at']
    
    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return JobApplicationDetailSerializer
        return JobApplicationSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'poster':
            # Job posters can see applications for their jobs
            return JobApplication.objects.filter(job__user=user)
        # Helpers can see their own applications
        return JobApplication.objects.filter(applicant=user)
    
    @extend_schema(
        summary="Create job application",
        description="Create a new job application (helpers only)",
        responses={
            201: JobApplicationSerializer,
            400: {"type": "object", "properties": {
                "error": {"type": "string"}
            }}
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a new job application (helpers only)."""
        # Check if user is a helper
        if request.user.user_type != 'helper':
            return Response(
                {'error': 'Only helpers can apply for jobs'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

@extend_schema(tags=['reviews'])
class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing reviews.
    
    Allows users to create and manage reviews for completed jobs.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['reviewer', 'reviewed']
    ordering_fields = ['created_at', 'rating']
    
    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return ReviewDetailSerializer
        return ReviewSerializer
    
    def get_queryset(self):
        user = self.request.user
        # Users can see reviews they've given or received
        return Review.objects.filter(Q(reviewer=user) | Q(reviewed=user))

@extend_schema(tags=['wallets'])
class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing wallet information.
    
    Allows users to view their wallet balance and details.
    """
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Wallet.objects.none()  # Initialize with empty queryset
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Wallet.objects.none()
        return Wallet.objects.filter(user=self.request.user)

@extend_schema(tags=['transactions'])
class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing transaction history.
    
    Allows users to view their transaction history with filtering and ordering options.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['type', 'reason']
    ordering_fields = ['created_at', 'amount']
    queryset = Transaction.objects.none()  # Initialize with empty queryset
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()
        return Transaction.objects.filter(wallet__user=self.request.user)

@extend_schema(tags=['notifications'])
class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing notifications.
    
    Allows users to view and manage their notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_read']
    ordering_fields = ['created_at']
    queryset = Notification.objects.none()  # Initialize with empty queryset
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)
    
    @extend_schema(
        summary="Update notification",
        description="Update notification fields (only is_read is allowed)",
        responses={
            200: NotificationSerializer,
            400: {"type": "object", "properties": {
                "error": {"type": "string"}
            }}
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """Only allow updating is_read field."""
        if len(request.data) > 1 or 'is_read' not in request.data:
            return Response(
                {'error': 'Only is_read field can be updated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Mark all notifications as read",
        description="Mark all unread notifications as read",
        responses={200: {"type": "object", "properties": {
            "message": {"type": "string"},
            "count": {"type": "integer"}
        }}}
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        count = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({
            'message': f'Marked {count} notifications as read',
            'count': count
        })

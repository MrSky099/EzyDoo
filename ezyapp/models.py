from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import JSONField
from django.core.validators import MinValueValidator, MaxValueValidator
import random
import string

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('poster', 'Job Poster'),
        ('helper', 'Helper'),
    )
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    is_verified = models.BooleanField(default=False)
    kyc_details = JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # OTP verification fields
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user_type']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_verified']),
        ]

    def __str__(self):
        return self.username
    
    def generate_otp(self):
        self.otp = generate_otp()
        from django.utils import timezone
        self.otp_created_at = timezone.now()
        self.save(update_fields=['otp', 'otp_created_at'])
        return self.otp

class HelperDocument(models.Model):
    DOCUMENT_STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='documents')
    aadhaar_card = models.FileField(upload_to='documents/aadhaar/', blank=True, null=True)
    driving_license = models.FileField(upload_to='documents/driving_license/', blank=True, null=True)
    pan_card = models.FileField(upload_to='documents/pan/', blank=True, null=True)
    selfie = models.ImageField(upload_to='documents/selfie/', blank=True, null=True)
    
    status = models.CharField(max_length=10, choices=DOCUMENT_STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Admin verification fields
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                    related_name='verified_documents', 
                                    null=True, blank=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['verified_by']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Documents for {self.user.username}"

class Job(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    JOB_TYPE_CHOICES = (
        ('fixed', 'Fixed Price'),
        ('hourly', 'Hourly Rate'),
    )
    
    CATEGORY_CHOICES = (
        ('pet', 'Pet Care'),
        ('home', 'Home Services'),
        ('outdoor', 'Outdoor Tasks'),
        ('delivery', 'Delivery'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    location_lat = models.DecimalField(max_digits=10, decimal_places=7)
    location_long = models.DecimalField(max_digits=10, decimal_places=7)
    location_address = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    job_type = models.CharField(max_length=10, choices=JOB_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='assigned_jobs',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['created_at']),
            models.Index(fields=['start_time']),
            # Compound index for location-based queries
            models.Index(fields=['location_lat', 'location_long']),
        ]
    
    def __str__(self):
        return self.title

class JobApplication(models.Model):
    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    helper = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Ensure a helper can only apply once to a job
        unique_together = ('job', 'helper')
        indexes = [
            models.Index(fields=['job']),
            models.Index(fields=['helper']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Application for {self.job.title} by {self.helper.username}"

class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    reviewed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Ensure a user can only review another user once
        unique_together = ('reviewer', 'reviewed')
        indexes = [
            models.Index(fields=['reviewer']),
            models.Index(fields=['reviewed']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.reviewed.username}"

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['balance']),
        ]
    
    def __str__(self):
        return f"Wallet of {self.user.username}"

class Transaction(models.Model):
    TYPE_CHOICES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )
    
    REASON_CHOICES = (
        ('job_payment', 'Job Payment'),
        ('withdrawal', 'Withdrawal'),
        ('deposit', 'Deposit'),
        ('refund', 'Refund'),
        ('other', 'Other'),
    )
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['wallet']),
            models.Index(fields=['type']),
            models.Index(fields=['reason']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.type} transaction of {self.amount} for {self.wallet.user.username}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:30]}..."

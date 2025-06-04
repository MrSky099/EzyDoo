from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .models import User, Job, JobApplication, Review, Wallet, Transaction, Notification, HelperDocument

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_verified', 'created_at')
    list_filter = ('user_type', 'is_verified', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')}),
        ('EzyDoo info', {'fields': ('user_type', 'is_verified', 'kyc_details')}),
        ('OTP', {'fields': ('otp', 'otp_created_at')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at')}),
    )
    readonly_fields = ('created_at', 'otp', 'otp_created_at')
    actions = ['generate_otp', 'verify_users']
    
    def generate_otp(self, request, queryset):
        count = 0
        for user in queryset:
            user.generate_otp()
            count += 1
        self.message_user(request, f"Generated OTP for {count} users.")
    generate_otp.short_description = "Generate OTP for selected users"
    
    def verify_users(self, request, queryset):
        count = 0
        for user in queryset:
            if not user.is_verified:
                user.is_verified = True
                user.save()
                count += 1
        self.message_user(request, f"Verified {count} users.")
    verify_users.short_description = "Mark selected users as verified"

class HelperDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'has_all_documents', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_documents', 'reject_documents']
    
    def has_all_documents(self, obj):
        return bool(obj.aadhaar_card and obj.driving_license and obj.pan_card and obj.selfie)
    has_all_documents.boolean = True
    has_all_documents.short_description = "All documents uploaded"
    
    def approve_documents(self, request, queryset):
        count = 0
        for doc in queryset:
            if doc.status != 'approved':
                doc.status = 'approved'
                doc.verified_by = request.user
                doc.verified_at = timezone.now()
                doc.rejection_reason = None
                doc.save()
                
                # Also verify the user
                doc.user.is_verified = True
                doc.user.save()
                count += 1
        self.message_user(request, f"Approved documents for {count} helpers.")
    approve_documents.short_description = "Approve selected documents"
    
    def reject_documents(self, request, queryset):
        # This action would typically be followed by a form to enter rejection reason
        count = 0
        for doc in queryset:
            if doc.status != 'rejected':
                doc.status = 'rejected'
                doc.verified_by = request.user
                doc.verified_at = timezone.now()
                # The rejection_reason would be set via a form
                doc.save()
                count += 1
        self.message_user(request, f"Rejected documents for {count} helpers.")
    reject_documents.short_description = "Reject selected documents"

class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'job_type', 'status', 'start_time', 'created_at')
    list_filter = ('category', 'job_type', 'status')
    search_fields = ('title', 'description', 'location_address')
    readonly_fields = ('created_at',)

class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'helper', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('job__title', 'helper__username', 'message')
    readonly_fields = ('created_at',)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'reviewed', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('reviewer__username', 'reviewed__username', 'comment')
    readonly_fields = ('created_at',)

class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'type', 'amount', 'reason', 'created_at')
    list_filter = ('type', 'reason')
    search_fields = ('wallet__user__username',)
    readonly_fields = ('created_at',)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_short', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('user__username', 'message')
    readonly_fields = ('created_at',)
    
    def message_short(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = 'Message'

admin.site.register(User, CustomUserAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(JobApplication, JobApplicationAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(HelperDocument, HelperDocumentAdmin)

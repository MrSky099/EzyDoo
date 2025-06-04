from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Job, JobApplication, Review, Wallet, Transaction, Notification, HelperDocument
from drf_spectacular.utils import extend_schema_field

User = get_user_model()

class HelperDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelperDocument
        fields = ('id', 'aadhaar_card', 'driving_license', 'pan_card', 'selfie', 
                 'status', 'rejection_reason', 'created_at', 'updated_at')
        read_only_fields = ('status', 'rejection_reason', 'created_at', 'updated_at')

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    documents = HelperDocumentSerializer(required=False, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', 'email', 'first_name', 'last_name', 
                 'phone_number', 'user_type', 'is_verified', 'kyc_details', 'profile_picture',
                 'created_at', 'documents')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'user_type': {'required': True},
        }
        
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
        
    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data.get('phone_number', ''),
            user_type=validated_data['user_type'],
            kyc_details=validated_data.get('kyc_details', {}),
            profile_picture=validated_data.get('profile_picture', None)
        )
        
        user.set_password(validated_data['password'])
        user.save()
        
        # Create a wallet for the user
        Wallet.objects.create(user=user)
        
        # Create helper document entry if user is a helper
        if user.user_type == 'helper':
            HelperDocument.objects.create(user=user)
        
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'kyc_details', 'profile_picture')

class UserProfileSerializer(serializers.ModelSerializer):
    documents_status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'phone_number', 'user_type', 'is_verified', 'profile_picture',
                 'created_at', 'documents_status')
        read_only_fields = fields
    
    @extend_schema_field({
        'type': 'object',
        'nullable': True,
        'properties': {
            'status': {'type': 'string'},
            'has_aadhaar': {'type': 'boolean'},
            'has_driving_license': {'type': 'boolean'},
            'has_pan_card': {'type': 'boolean'},
            'has_selfie': {'type': 'boolean'},
            'rejection_reason': {'type': 'string', 'nullable': True},
        }
    })
    def get_documents_status(self, obj):
        if obj.user_type != 'helper':
            return None
        
        try:
            doc = obj.documents
            return {
                'status': doc.status,
                'has_aadhaar': bool(doc.aadhaar_card),
                'has_driving_license': bool(doc.driving_license),
                'has_pan_card': bool(doc.pan_card),
                'has_selfie': bool(doc.selfie),
                'rejection_reason': doc.rejection_reason,
            }
        except HelperDocument.DoesNotExist:
            return None

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ('id', 'user', 'title', 'description', 'location_lat', 'location_long', 
                 'location_address', 'category', 'job_type', 'price', 'hourly_rate', 
                 'start_time', 'end_time', 'status', 'assigned_to', 'created_at')
        read_only_fields = ('user', 'assigned_to', 'created_at')
        
    def validate(self, attrs):
        job_type = attrs.get('job_type')
        price = attrs.get('price')
        hourly_rate = attrs.get('hourly_rate')
        
        if job_type == 'fixed' and not price:
            raise serializers.ValidationError({"price": "Price is required for fixed price jobs."})
        elif job_type == 'hourly' and not hourly_rate:
            raise serializers.ValidationError({"hourly_rate": "Hourly rate is required for hourly jobs."})
            
        return attrs
        
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class JobDetailSerializer(JobSerializer):
    user = UserProfileSerializer(read_only=True)
    assigned_to = UserProfileSerializer(read_only=True)
    
    class Meta(JobSerializer.Meta):
        pass

class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ('id', 'job', 'helper', 'status', 'message', 'created_at')
        read_only_fields = ('helper', 'status', 'created_at')
        
    def create(self, validated_data):
        validated_data['helper'] = self.context['request'].user
        return super().create(validated_data)

class JobApplicationDetailSerializer(JobApplicationSerializer):
    job = JobSerializer(read_only=True)
    helper = UserProfileSerializer(read_only=True)
    
    class Meta(JobApplicationSerializer.Meta):
        pass

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ('id', 'reviewer', 'reviewed', 'rating', 'comment', 'created_at')
        read_only_fields = ('reviewer', 'created_at')
        
    def validate(self, attrs):
        if attrs['reviewed'] == self.context['request'].user:
            raise serializers.ValidationError({"reviewed": "You cannot review yourself."})
        return attrs
        
    def create(self, validated_data):
        validated_data['reviewer'] = self.context['request'].user
        return super().create(validated_data)

class ReviewDetailSerializer(ReviewSerializer):
    reviewer = UserProfileSerializer(read_only=True)
    reviewed = UserProfileSerializer(read_only=True)
    
    class Meta(ReviewSerializer.Meta):
        pass

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ('id', 'user', 'balance', 'created_at')
        read_only_fields = fields

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'wallet', 'type', 'amount', 'reason', 'created_at')
        read_only_fields = fields

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'user', 'message', 'is_read', 'created_at')
        read_only_fields = ('user', 'message', 'created_at')
        
    def update(self, instance, validated_data):
        # Only allow updating is_read field
        instance.is_read = validated_data.get('is_read', instance.is_read)
        instance.save()
        return instance 